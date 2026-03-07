import pytest
import pytest_asyncio

from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport


@pytest.fixture(scope="session")
def app():
    from app.run import app as _app

    return _app


@pytest_asyncio.fixture
async def client(app: FastAPI):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def valid_token_headers():
    from app.core.security import create_access_token

    token = create_access_token(subject=1)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_id():
    return 1
