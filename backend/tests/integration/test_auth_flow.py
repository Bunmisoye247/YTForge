from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from testcontainers.postgres import PostgresContainer

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def postgres_dsn() -> AsyncIterator[str]:
    with PostgresContainer("postgres:16-alpine") as postgres:
        os.environ["YTFORGE__DATABASE__HOST"] = postgres.get_container_host_ip()
        os.environ["YTFORGE__DATABASE__PORT"] = str(postgres.get_exposed_port(5432))
        os.environ["YTFORGE__DATABASE__USER"] = postgres.username
        os.environ["YTFORGE__DATABASE__PASSWORD"] = postgres.password
        os.environ["YTFORGE__DATABASE__NAME"] = postgres.dbname

        from ytforge.infrastructure.config.settings import get_settings

        get_settings.cache_clear()

        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        alembic_cfg = Config(os.path.join(backend_dir, "alembic.ini"))
        command.upgrade(alembic_cfg, "head")

        yield postgres.get_connection_url()


@pytest.fixture
async def client(postgres_dsn: str) -> AsyncIterator[AsyncClient]:
    from ytforge.infrastructure.db.session import get_engine, get_session_factory
    from ytforge.interfaces.api.main import create_app

    # get_engine()/get_session_factory() are process-wide lru_caches, but each
    # test runs in its own pytest-asyncio event loop; a pool built on a prior
    # test's loop starts failing writes once that loop is closed. Rebuild and
    # dispose the engine per test so its connections stay bound to this loop.
    get_engine.cache_clear()
    get_session_factory.cache_clear()

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    await get_engine().dispose()
    get_engine.cache_clear()
    get_session_factory.cache_clear()


async def test_register_login_refresh_me(client: AsyncClient) -> None:
    register_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "founder@example.com", "password": "hunter22", "full_name": "Founder"},
    )
    assert register_response.status_code == 201

    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "founder@example.com", "password": "hunter22"},
    )
    assert login_response.status_code == 200
    body = login_response.json()
    assert "access_token" in body
    assert "refresh_token" in login_response.cookies

    me_response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "founder@example.com"

    refresh_response = await client.post("/api/v1/auth/refresh")
    assert refresh_response.status_code == 200


async def test_channel_rbac_blocks_viewer_from_creating_projects(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "owner@example.com", "password": "hunter22", "full_name": "Owner"},
    )
    owner_login = await client.post(
        "/api/v1/auth/login", data={"username": "owner@example.com", "password": "hunter22"}
    )
    owner_token = owner_login.json()["access_token"]
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    channel_response = await client.post(
        "/api/v1/channels", json={"name": "Test Channel"}, headers=owner_headers
    )
    channel_id = channel_response.json()["id"]

    await client.post(
        "/api/v1/auth/register",
        json={"email": "viewer@example.com", "password": "hunter22", "full_name": "Viewer"},
    )
    viewer_login = await client.post(
        "/api/v1/auth/login", data={"username": "viewer@example.com", "password": "hunter22"}
    )
    viewer_id = viewer_login.json()["user"]["id"]
    viewer_token = viewer_login.json()["access_token"]
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    await client.post(
        f"/api/v1/channels/{channel_id}/members",
        json={"user_id": viewer_id, "role": "viewer"},
        headers=owner_headers,
    )

    project_response = await client.post(
        f"/api/v1/channels/{channel_id}/projects", json={"title": "Idea"}, headers=viewer_headers
    )
    assert project_response.status_code == 403

    editor_project_response = await client.post(
        f"/api/v1/channels/{channel_id}/projects", json={"title": "Idea"}, headers=owner_headers
    )
    assert editor_project_response.status_code == 201
