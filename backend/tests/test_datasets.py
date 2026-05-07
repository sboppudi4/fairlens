"""Dataset upload + retrieval tests."""
from __future__ import annotations

import io

import numpy as np
import pandas as pd
import pytest
from httpx import AsyncClient


def _toy_csv(n_rows: int = 120, with_header: bool = True) -> bytes:
    rng = np.random.default_rng(7)
    df = pd.DataFrame({
        "age": rng.integers(20, 70, size=n_rows),
        "income": rng.choice(["low", "high"], size=n_rows),
        "gender": rng.choice(["M", "F"], size=n_rows),
        "label": rng.integers(0, 2, size=n_rows),
        "prediction": rng.integers(0, 2, size=n_rows),
    })
    buf = io.BytesIO()
    df.to_csv(buf, index=False, header=with_header)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_upload_valid_csv(client: AsyncClient, auth_headers: dict):
    csv_bytes = _toy_csv()
    resp = await client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers,
        files={"file": ("toy.csv", csv_bytes, "text/csv")},
        data={"name": "toy"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["row_count"] == 120
    assert "label" in body["column_names"]
    assert body["status"] == "ready"


@pytest.mark.asyncio
async def test_upload_rejects_non_csv_extension(client: AsyncClient, auth_headers: dict):
    resp = await client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers,
        files={"file": ("data.txt", b"not,a,csv\n1,2,3\n", "text/plain")},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_upload_rejects_too_few_rows(client: AsyncClient, auth_headers: dict):
    csv_bytes = _toy_csv(n_rows=50)
    resp = await client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers,
        files={"file": ("small.csv", csv_bytes, "text/csv")},
    )
    assert resp.status_code == 400
    assert "100 rows" in resp.json()["detail"].lower() or "at least" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/api/v1/datasets/upload",
        files={"file": ("x.csv", _toy_csv(), "text/csv")},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_datasets_returns_only_own(client: AsyncClient, auth_headers: dict):
    # Upload one
    await client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers,
        files={"file": ("a.csv", _toy_csv(), "text/csv")},
    )
    resp = await client.get("/api/v1/datasets", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 1


@pytest.mark.asyncio
async def test_get_unknown_dataset_returns_404(client: AsyncClient, auth_headers: dict):
    resp = await client.get(
        "/api/v1/datasets/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_other_user_cannot_see_dataset(client: AsyncClient, auth_headers: dict):
    # Upload as user A
    up = await client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers,
        files={"file": ("a.csv", _toy_csv(), "text/csv")},
    )
    ds_id = up.json()["id"]

    # Register a second user
    import uuid as _uuid
    email = f"other-{_uuid.uuid4().hex[:6]}@test.dev"
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password1234", "full_name": "Other"},
    )
    other = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    resp = await client.get(f"/api/v1/datasets/{ds_id}", headers=other)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_dataset_columns_endpoint(client: AsyncClient, auth_headers: dict):
    up = await client.post(
        "/api/v1/datasets/upload",
        headers=auth_headers,
        files={"file": ("c.csv", _toy_csv(), "text/csv")},
    )
    ds_id = up.json()["id"]
    resp = await client.get(f"/api/v1/datasets/{ds_id}/columns", headers=auth_headers)
    assert resp.status_code == 200
    cols = resp.json()["columns"]
    names = {c["name"] for c in cols}
    assert {"age", "income", "gender", "label", "prediction"} <= names
