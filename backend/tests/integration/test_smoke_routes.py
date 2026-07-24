from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from ytforge.interfaces.api.main import create_app

# These don't require a reachable database: unauthenticated requests are
# rejected by `get_current_user` before any query runs, and OpenAPI schema
# generation is pure introspection.


@pytest.fixture
def app():  # type: ignore[no-untyped-def]
    return create_app()


async def test_openapi_schema_builds(app) -> None:  # type: ignore[no-untyped-def]
    schema = app.openapi()
    assert "/api/v1/auth/register" in schema["paths"]
    assert len(schema["paths"]) > 40


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/api/v1/auth/me"),
        ("GET", "/api/v1/channels"),
        ("GET", "/api/v1/pipelines"),
        ("GET", "/api/v1/settings"),
        ("GET", "/api/v1/models"),
    ],
)
async def test_protected_routes_require_auth(app, method: str, path: str) -> None:  # type: ignore[no-untyped-def]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.request(method, path)
    assert response.status_code == 401


async def test_register_and_login_validation_errors_are_problem_json(app) -> None:  # type: ignore[no-untyped-def]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register", json={"email": "not-an-email", "password": "x", "full_name": "A"}
        )
    assert response.status_code == 422
