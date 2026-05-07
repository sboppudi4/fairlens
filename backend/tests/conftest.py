"""Test fixtures.

Strategy
--------
* Use the same Postgres instance as the rest of the app — DATABASE_URL must be set.
  In CI the workflow provisions a postgres service and runs alembic. Locally, run
  ``docker compose up -d postgres redis`` first.
* Each test runs inside its own transaction that is rolled back at the end, so
  tests are fully isolated without TRUNCATE.
* Object storage and Celery dispatch are monkey-patched to in-memory shims, so
  tests never touch MinIO or a Celery broker.
* The FastAPI ``get_db`` dependency is overridden to return the same session that
  the test fixture uses, so any data created via the API is visible to the test
  and gets rolled back at the end.

Markers
-------
* ``pytest.mark.asyncio`` is the default — set in pyproject.toml.
"""
from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set test-friendly env BEFORE importing the app
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "test-only-secret-key-do-not-use-in-prod-12345678901234567890")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("AWS_BUCKET_NAME", "fairlens-test")
os.environ.setdefault("AWS_ENDPOINT_URL", "http://localhost:9000")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://fairlens:fairlens@localhost:5432/fairlens",
)

from app.core.database import Base  # noqa: E402
from app.dependencies import get_db  # noqa: E402
from app.main import create_app  # noqa: E402

# Import all models so create_all sees them
from app.models import Audit, Dataset, Report, User  # noqa: F401, E402


@pytest_asyncio.fixture(scope="session")
async def _engine():
    engine = create_async_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(_engine) -> AsyncIterator[AsyncSession]:
    """Per-test transaction, rolled back at teardown."""
    connection = await _engine.connect()
    transaction = await connection.begin()
    Session = async_sessionmaker(bind=connection, expire_on_commit=False, class_=AsyncSession)
    session = Session()

    # SAVEPOINT so service-level session.commit() doesn't end the outer txn.
    await connection.begin_nested()

    from sqlalchemy import event

    @event.listens_for(session.sync_session, "after_transaction_end")
    def _restart_savepoint(sess, trans):  # pragma: no cover - sqlalchemy internals
        if trans.nested and not trans._parent.nested and connection.in_transaction():
            sess.begin_nested()

    try:
        yield session
    finally:
        await session.close()
        if transaction.is_active:
            await transaction.rollback()
        await connection.close()


@pytest.fixture(autouse=True)
def _patch_storage(monkeypatch: pytest.MonkeyPatch) -> dict[str, bytes]:
    """In-memory replacement for app.core.storage."""
    store: dict[str, bytes] = {}

    async def _upload_bytes(key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        store[key] = data
        return key

    async def _upload_fileobj(key: str, fileobj: Any, content_type: str = "application/octet-stream") -> str:
        store[key] = fileobj.read()
        return key

    async def _download_bytes(key: str) -> bytes:
        if key not in store:
            raise FileNotFoundError(key)
        return store[key]

    def _download_bytes_sync(key: str) -> bytes:
        if key not in store:
            raise FileNotFoundError(key)
        return store[key]

    def _upload_bytes_sync(key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        store[key] = data
        return key

    async def _delete_object(key: str) -> None:
        store.pop(key, None)

    async def _stream_object(key: str):
        yield store.get(key, b"")

    def _ensure_bucket() -> None:
        return None

    monkeypatch.setattr("app.core.storage.upload_bytes", _upload_bytes)
    monkeypatch.setattr("app.core.storage.upload_fileobj", _upload_fileobj)
    monkeypatch.setattr("app.core.storage.download_bytes", _download_bytes)
    monkeypatch.setattr("app.core.storage.download_bytes_sync", _download_bytes_sync)
    monkeypatch.setattr("app.core.storage.upload_bytes_sync", _upload_bytes_sync)
    monkeypatch.setattr("app.core.storage.delete_object", _delete_object)
    monkeypatch.setattr("app.core.storage.stream_object", _stream_object)
    monkeypatch.setattr("app.core.storage.ensure_bucket", _ensure_bucket)
    return store


@pytest.fixture(autouse=True)
def _patch_celery(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, tuple, dict]]:
    """Capture Celery dispatches without running them."""
    calls: list[tuple[str, tuple, dict]] = []

    class _FakeTask:
        def __init__(self, name: str):
            self.name = name

        def delay(self, *args: Any, **kwargs: Any) -> Any:
            calls.append((self.name, args, kwargs))
            return type("R", (), {"id": str(uuid.uuid4())})()

    monkeypatch.setattr("app.tasks.audit_tasks.run_audit", _FakeTask("run_audit"))
    monkeypatch.setattr("app.tasks.audit_tasks.generate_report", _FakeTask("generate_report"))
    # Re-import sites:
    monkeypatch.setattr("app.api.v1.audits.run_audit", _FakeTask("run_audit"))
    monkeypatch.setattr("app.api.v1.reports.generate_report", _FakeTask("generate_report"))
    return calls


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """HTTPX AsyncClient bound to the FastAPI app, with get_db overridden."""
    app = create_app()

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Register a fresh user and return Authorization headers for them."""
    email = f"user-{uuid.uuid4().hex[:8]}@test.dev"
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password1234", "full_name": "Test User"},
    )
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
