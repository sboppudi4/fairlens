"""End-to-end auth tests against the FastAPI app via httpx."""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_returns_token_and_user(client: AsyncClient):
    email = f"alice-{uuid.uuid4().hex[:6]}@test.dev"
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password1234", "full_name": "Alice"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == email
    assert body["user"]["full_name"] == "Alice"
    assert body["user"]["is_active"] is True


@pytest.mark.asyncio
async def test_register_duplicate_email_rejected(client: AsyncClient):
    email = f"dup-{uuid.uuid4().hex[:6]}@test.dev"
    payload = {"email": email, "password": "password1234", "full_name": "Dup"}
    r1 = await client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201
    r2 = await client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 400
    assert "already registered" in r2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_short_password_rejected(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "short@test.dev", "password": "short", "full_name": "Short"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_succeeds_with_correct_credentials(client: AsyncClient):
    email = f"login-{uuid.uuid4().hex[:6]}@test.dev"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password1234", "full_name": "Login"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password1234"},
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client: AsyncClient):
    email = f"wrong-{uuid.uuid4().hex[:6]}@test.dev"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password1234", "full_name": "Wrong"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "incorrect-pass"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_authentication(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_current_user(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"].endswith("@test.dev")


@pytest.mark.asyncio
async def test_me_with_invalid_token_returns_401(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_update_me_changes_full_name(client: AsyncClient, auth_headers: dict):
    resp = await client.put(
        "/api/v1/auth/me",
        headers=auth_headers,
        json={"full_name": "Renamed User"},
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Renamed User"
