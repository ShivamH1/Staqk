
import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_health() -> None:
    import os
    os.environ.setdefault("CLERK_SECRET_KEY", "sk_test_dummy")
    os.environ.setdefault("CLERK_WEBHOOK_SECRET", "whsec_dummy")
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/staqk")
    os.environ.setdefault("DATABASE_URL_DIRECT", "postgresql://u:p@localhost/staqk")
    os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")
    os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_dummy")
    os.environ.setdefault("OPENROUTER_API_KEY", "sk-or-dummy")
    os.environ.setdefault("E2B_API_KEY", "e2b_dummy")

    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_me_requires_auth() -> None:
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/auth/me")
    assert response.status_code == 401  # no bearer token → 401
