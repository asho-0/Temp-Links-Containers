import pytest
import pytest_mock
import httpx

from app.services.auth.exceptions import (
    EmailAlreadyRegistered,
    UsernameTaken,
    InvalidCredentials,
    EmailNotVerified,
    InvalidVerificationToken,
)

REGISTER = "app.services.auth.AuthService.register"
VERIFY = "app.services.auth.AuthService.verify_email"
LOGIN = "app.services.auth.AuthService.login"
DELETE = "app.services.auth.AuthService.delete_user"


class TestRegister:
    ENDPOINT = "/auth/register"
    PAYLOAD = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "S3cure!1",
    }

    @pytest.mark.asyncio
    async def test_success_returns_201_with_message_key(
        self,
        client: httpx.AsyncClient,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            REGISTER, new=mocker.AsyncMock(return_value=mocker.MagicMock(id=1))
        )
        resp = await client.post(self.ENDPOINT, json=self.PAYLOAD)
        assert resp.status_code == 201
        assert "message" in resp.json()

    @pytest.mark.asyncio
    async def test_duplicate_email_returns_400_with_detail(
        self,
        client: httpx.AsyncClient,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            REGISTER,
            new=mocker.AsyncMock(side_effect=EmailAlreadyRegistered("taken")),
        )
        resp = await client.post(self.ENDPOINT, json=self.PAYLOAD)
        assert resp.status_code == 400
        assert "detail" in resp.json()

    @pytest.mark.asyncio
    async def test_duplicate_username_returns_400_with_detail(
        self,
        client: httpx.AsyncClient,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            REGISTER, new=mocker.AsyncMock(side_effect=UsernameTaken("taken"))
        )
        resp = await client.post(self.ENDPOINT, json=self.PAYLOAD)
        assert resp.status_code == 400
        assert "detail" in resp.json()

    @pytest.mark.asyncio
    async def test_missing_fields_returns_422(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        resp = await client.post(self.ENDPOINT, json={"username": "alice"})
        assert resp.status_code == 422


class TestVerifyEmail:
    ENDPOINT = "/auth/verify"

    @pytest.mark.asyncio
    async def test_valid_token_returns_200_with_message_key(
        self,
        client: httpx.AsyncClient,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(VERIFY, new=mocker.AsyncMock(return_value=None))
        resp = await client.get(self.ENDPOINT, params={"token": "valid-token"})
        assert resp.status_code == 200
        assert "message" in resp.json()

    @pytest.mark.asyncio
    async def test_invalid_token_returns_400_with_detail(
        self,
        client: httpx.AsyncClient,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            VERIFY,
            new=mocker.AsyncMock(
                side_effect=InvalidVerificationToken("invalid")
            ),
        )
        resp = await client.get(self.ENDPOINT, params={"token": "bad"})
        assert resp.status_code == 400
        assert "detail" in resp.json()


class TestLogin:
    ENDPOINT = "/auth/login"
    PAYLOAD = {"email": "alice@example.com", "password": "S3cure!1"}

    @pytest.mark.asyncio
    async def test_success_returns_200_with_token_fields(
        self,
        client: httpx.AsyncClient,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(LOGIN, new=mocker.AsyncMock(return_value="jwt.token.here"))
        resp = await client.post(self.ENDPOINT, json=self.PAYLOAD)
        assert resp.status_code == 200
        assert "access_token" in resp.json()
        assert "token_type" in resp.json()

    @pytest.mark.asyncio
    async def test_unverified_email_returns_403_with_detail(
        self,
        client: httpx.AsyncClient,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            LOGIN,
            new=mocker.AsyncMock(side_effect=EmailNotVerified("verify first")),
        )
        resp = await client.post(self.ENDPOINT, json=self.PAYLOAD)
        assert resp.status_code == 403
        assert "detail" in resp.json()

    @pytest.mark.asyncio
    async def test_wrong_credentials_returns_401_with_detail(
        self,
        client: httpx.AsyncClient,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            LOGIN, new=mocker.AsyncMock(side_effect=InvalidCredentials("wrong"))
        )
        resp = await client.post(self.ENDPOINT, json=self.PAYLOAD)
        assert resp.status_code == 401
        assert "detail" in resp.json()


class TestDeleteAccount:
    ENDPOINT = "/auth/delete"

    @pytest.mark.asyncio
    async def test_authenticated_returns_204(
        self,
        client: httpx.AsyncClient,
        valid_token_headers: dict[str, str],
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(DELETE, new=mocker.AsyncMock(return_value=None))
        resp = await client.delete(self.ENDPOINT, headers=valid_token_headers)
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        resp = await client.delete(self.ENDPOINT)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_nonexistent_user_returns_404_with_detail(
        self,
        client: httpx.AsyncClient,
        valid_token_headers: dict[str, str],
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            DELETE,
            new=mocker.AsyncMock(side_effect=InvalidCredentials("not found")),
        )
        resp = await client.delete(self.ENDPOINT, headers=valid_token_headers)
        assert resp.status_code == 404
        assert "detail" in resp.json()
