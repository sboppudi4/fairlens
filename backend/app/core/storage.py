"""S3 / MinIO object storage. Uses boto3 sync client wrapped via asyncio.to_thread."""
from __future__ import annotations

import asyncio
from io import BytesIO
from typing import BinaryIO

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import get_settings


def _build_client():
    s = get_settings()
    return boto3.client(
        "s3",
        aws_access_key_id=s.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=s.AWS_SECRET_ACCESS_KEY,
        endpoint_url=s.AWS_ENDPOINT_URL,
        region_name=s.AWS_REGION,
        config=Config(signature_version="s3v4", retries={"max_attempts": 3}),
    )


_client = None


def get_client():
    global _client
    if _client is None:
        _client = _build_client()
    return _client


def ensure_bucket() -> None:
    s = get_settings()
    client = get_client()
    try:
        client.head_bucket(Bucket=s.AWS_BUCKET_NAME)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code")
        if code in ("404", "NoSuchBucket", "NotFound"):
            client.create_bucket(Bucket=s.AWS_BUCKET_NAME)
        else:
            raise


async def upload_bytes(key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    s = get_settings()

    def _put():
        client = get_client()
        client.put_object(Bucket=s.AWS_BUCKET_NAME, Key=key, Body=data, ContentType=content_type)
        return key

    return await asyncio.to_thread(_put)


async def upload_fileobj(key: str, fileobj: BinaryIO, content_type: str = "application/octet-stream") -> str:
    s = get_settings()

    def _put():
        client = get_client()
        client.upload_fileobj(
            fileobj,
            s.AWS_BUCKET_NAME,
            key,
            ExtraArgs={"ContentType": content_type},
        )
        return key

    return await asyncio.to_thread(_put)


async def download_bytes(key: str) -> bytes:
    s = get_settings()

    def _get():
        client = get_client()
        buf = BytesIO()
        client.download_fileobj(s.AWS_BUCKET_NAME, key, buf)
        return buf.getvalue()

    return await asyncio.to_thread(_get)


def download_bytes_sync(key: str) -> bytes:
    """Sync version for Celery workers."""
    s = get_settings()
    client = get_client()
    buf = BytesIO()
    client.download_fileobj(s.AWS_BUCKET_NAME, key, buf)
    return buf.getvalue()


def upload_bytes_sync(key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    """Sync upload for Celery workers."""
    s = get_settings()
    client = get_client()
    client.put_object(Bucket=s.AWS_BUCKET_NAME, Key=key, Body=data, ContentType=content_type)
    return key


async def stream_object(key: str):
    """Async generator that yields chunks of an S3 object for FastAPI StreamingResponse."""
    data = await download_bytes(key)
    chunk = 64 * 1024
    for i in range(0, len(data), chunk):
        yield data[i : i + chunk]


async def delete_object(key: str) -> None:
    s = get_settings()

    def _del():
        client = get_client()
        client.delete_object(Bucket=s.AWS_BUCKET_NAME, Key=key)

    await asyncio.to_thread(_del)
