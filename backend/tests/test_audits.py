"""Audit creation and retrieval tests.

Celery dispatch is mocked in conftest, so these tests verify the API contract
and the queue handoff but do not actually run the audit task end-to-end.
"""
from __future__ import annotations

import io
import uuid

import numpy as np
import pandas as pd
import pytest
from httpx import AsyncClient


def _audit_csv(n: int = 200) -> bytes:
    rng = np.random.default_rng(11)
    df = pd.DataFrame({
        "feature_a": rng.integers(0, 100, size=n),
        "feature_b": rng.normal(size=n),
        "gender": rng.choice(["M", "F"], size=n),
        "label": rng.integers(0, 2, size=n),
        "prediction": rng.integers(0, 2, size=n),
    })
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


async def _upload(client: AsyncClient, headers: dict) -> str:
    resp = await client.post(
        "/api/v1/datasets/upload",
        headers=headers,
        files={"file": ("a.csv", _audit_csv(), "text/csv")},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_create_audit_returns_pending_with_task_id(
    client: AsyncClient, auth_headers: dict, _patch_celery: list
):
    ds_id = await _upload(client, auth_headers)
    resp = await client.post(
        "/api/v1/audits",
        headers=auth_headers,
        json={
            "dataset_id": ds_id,
            "name": "first audit",
            "config": {
                "label_column": "label",
                "prediction_column": "prediction",
                "sensitive_attributes": ["gender"],
                "positive_label": "1",
                "favorable_prediction": "1",
            },
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["name"] == "first audit"
    assert body["status"] in {"pending", "running"}
    assert body["dataset_id"] == ds_id
    # Celery delay should have been called once
    assert any(c[0] == "run_audit" for c in _patch_celery)


@pytest.mark.asyncio
async def test_create_audit_validates_required_fields(client: AsyncClient, auth_headers: dict):
    ds_id = await _upload(client, auth_headers)
    resp = await client.post(
        "/api/v1/audits",
        headers=auth_headers,
        json={
            "dataset_id": ds_id,
            "name": "missing config",
            "config": {
                "label_column": "label",
                # prediction_column missing
                "sensitive_attributes": ["gender"],
                "positive_label": "1",
                "favorable_prediction": "1",
            },
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_audit_rejects_too_many_sensitive_attrs(
    client: AsyncClient, auth_headers: dict
):
    ds_id = await _upload(client, auth_headers)
    resp = await client.post(
        "/api/v1/audits",
        headers=auth_headers,
        json={
            "dataset_id": ds_id,
            "name": "bad",
            "config": {
                "label_column": "label",
                "prediction_column": "prediction",
                "sensitive_attributes": ["a", "b", "c", "d", "e", "f"],  # 6 > 5
                "positive_label": "1",
                "favorable_prediction": "1",
            },
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_audits_returns_my_audits(client: AsyncClient, auth_headers: dict):
    ds_id = await _upload(client, auth_headers)
    for i in range(3):
        await client.post(
            "/api/v1/audits",
            headers=auth_headers,
            json={
                "dataset_id": ds_id,
                "name": f"audit-{i}",
                "config": {
                    "label_column": "label",
                    "prediction_column": "prediction",
                    "sensitive_attributes": ["gender"],
                    "positive_label": "1",
                    "favorable_prediction": "1",
                },
            },
        )
    resp = await client.get("/api/v1/audits", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 3


@pytest.mark.asyncio
async def test_get_unknown_audit_returns_404(client: AsyncClient, auth_headers: dict):
    resp = await client.get(
        f"/api/v1/audits/{uuid.uuid4()}",
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_audit_status_endpoint_returns_progress(
    client: AsyncClient, auth_headers: dict
):
    ds_id = await _upload(client, auth_headers)
    create = await client.post(
        "/api/v1/audits",
        headers=auth_headers,
        json={
            "dataset_id": ds_id,
            "name": "status-check",
            "config": {
                "label_column": "label",
                "prediction_column": "prediction",
                "sensitive_attributes": ["gender"],
                "positive_label": "1",
                "favorable_prediction": "1",
            },
        },
    )
    audit_id = create.json()["id"]
    resp = await client.get(f"/api/v1/audits/{audit_id}/status", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "progress" in body
    assert body["status"] in {"pending", "running", "completed", "failed"}


@pytest.mark.asyncio
async def test_delete_audit(client: AsyncClient, auth_headers: dict):
    ds_id = await _upload(client, auth_headers)
    create = await client.post(
        "/api/v1/audits",
        headers=auth_headers,
        json={
            "dataset_id": ds_id,
            "name": "to-delete",
            "config": {
                "label_column": "label",
                "prediction_column": "prediction",
                "sensitive_attributes": ["gender"],
                "positive_label": "1",
                "favorable_prediction": "1",
            },
        },
    )
    audit_id = create.json()["id"]
    resp = await client.delete(f"/api/v1/audits/{audit_id}", headers=auth_headers)
    assert resp.status_code == 204
    follow = await client.get(f"/api/v1/audits/{audit_id}", headers=auth_headers)
    assert follow.status_code == 404
