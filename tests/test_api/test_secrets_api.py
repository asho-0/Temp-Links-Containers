import pytest
import pytest_mock
import httpx
from types import SimpleNamespace
from datetime import datetime, UTC

from app.db.schemas.secret_schm import SecretReadScheme

CREATE = "app.services.bl.secret.SecretService.create"
LIST = "app.services.bl.secret.SecretService.list_for_user"
DECRYPT = "app.services.bl.secret.SecretService.get_and_decrypt"
DELETE = "app.services.bl.secret.SecretService.delete"
EXISTS = "app.services.bl.secret.SecretService.exists_for_owner"

CREATE_SHARE_TOKEN = "app.core.security.create_share_token"


def read_schema(**kwargs: object) -> SecretReadScheme:
    fields: dict[str, object] = dict(
        id=1, creator_id=1, title="t", is_read=False
    )
    fields.update(kwargs)
    return SecretReadScheme.model_construct(**fields)


def orm_secret(**kwargs: object) -> SimpleNamespace:
    fields: dict[str, object] = dict(
        id=1,
        creator_id=1,
        title="t",
        is_read=False,
        created_at=datetime.now(UTC),
    )
    fields.update(kwargs)
    return SimpleNamespace(**fields)


DECRYPT_PAYLOAD: dict[str, str] = {"encryption_password": "strongkey"}
SHARE_PAYLOAD: dict[str, str | int] = {
    "encryption_password": "strongkey",
    "expires_minutes": 60,
}
CREATE_PAYLOAD: dict[str, str] = {
    "title": "pw",
    "content": "hunter2",
    "encryption_password": "strongkey",
}


class TestCreateSecret:
    ENDPOINT = "/secrets/"

    @pytest.mark.asyncio
    async def test_returns_201_with_id_and_title(
        self,
        client: httpx.AsyncClient,
        valid_token_headers: dict[str, str],
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            CREATE, new=mocker.AsyncMock(return_value=read_schema(title="pw"))
        )
        resp = await client.post(
            self.ENDPOINT, json=CREATE_PAYLOAD, headers=valid_token_headers
        )
        assert resp.status_code == 201
        assert "id" in resp.json()
        assert "title" in resp.json()

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        resp = await client.post(self.ENDPOINT, json=CREATE_PAYLOAD)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_fields_returns_422(
        self,
        client: httpx.AsyncClient,
        valid_token_headers: dict[str, str],
    ) -> None:
        resp = await client.post(
            self.ENDPOINT, json={"title": "x"}, headers=valid_token_headers
        )
        assert resp.status_code == 422


class TestListSecrets:
    ENDPOINT = "/secrets/"

    @pytest.mark.asyncio
    async def test_returns_200_with_list(
        self,
        client: httpx.AsyncClient,
        valid_token_headers: dict[str, str],
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            LIST,
            new=mocker.AsyncMock(
                return_value=[read_schema(), read_schema(id=2)]
            ),
        )
        resp = await client.get(self.ENDPOINT, headers=valid_token_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_returns_empty_list(
        self,
        client: httpx.AsyncClient,
        valid_token_headers: dict[str, str],
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(LIST, new=mocker.AsyncMock(return_value=[]))
        resp = await client.get(self.ENDPOINT, headers=valid_token_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        resp = await client.get(self.ENDPOINT)
        assert resp.status_code == 401


class TestDecryptSecret:
    @pytest.mark.asyncio
    async def test_returns_200_with_content_field(
        self,
        client: httpx.AsyncClient,
        valid_token_headers: dict[str, str],
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            DECRYPT,
            new=mocker.AsyncMock(return_value=(orm_secret(), "plaintext")),
        )
        resp = await client.post(
            "/secrets/decrypt/1",
            json=DECRYPT_PAYLOAD,
            headers=valid_token_headers,
        )
        assert resp.status_code == 200
        assert "content" in resp.json()

    @pytest.mark.asyncio
    async def test_permission_denied_returns_404_with_detail(
        self,
        client: httpx.AsyncClient,
        valid_token_headers: dict[str, str],
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            DECRYPT, new=mocker.AsyncMock(side_effect=PermissionError("denied"))
        )
        resp = await client.post(
            "/secrets/decrypt/1",
            json=DECRYPT_PAYLOAD,
            headers=valid_token_headers,
        )
        assert resp.status_code == 404
        assert "detail" in resp.json()

    @pytest.mark.asyncio
    async def test_expired_returns_410_with_detail(
        self,
        client: httpx.AsyncClient,
        valid_token_headers: dict[str, str],
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            DECRYPT, new=mocker.AsyncMock(side_effect=ValueError("expired"))
        )
        resp = await client.post(
            "/secrets/decrypt/1",
            json=DECRYPT_PAYLOAD,
            headers=valid_token_headers,
        )
        assert resp.status_code == 410
        assert "detail" in resp.json()

    @pytest.mark.asyncio
    async def test_bad_password_returns_422_with_detail(
        self,
        client: httpx.AsyncClient,
        valid_token_headers: dict[str, str],
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            DECRYPT, new=mocker.AsyncMock(side_effect=Exception("bad decrypt"))
        )
        resp = await client.post(
            "/secrets/decrypt/1",
            json=DECRYPT_PAYLOAD,
            headers=valid_token_headers,
        )
        assert resp.status_code == 422
        assert "detail" in resp.json()


class TestDeleteSecret:
    @pytest.mark.asyncio
    async def test_returns_204(
        self,
        client: httpx.AsyncClient,
        valid_token_headers: dict[str, str],
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(DELETE, new=mocker.AsyncMock(return_value=None))
        resp = await client.delete("/secrets/1", headers=valid_token_headers)
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_not_owner_returns_404_with_detail(
        self,
        client: httpx.AsyncClient,
        valid_token_headers: dict[str, str],
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            DELETE, new=mocker.AsyncMock(side_effect=PermissionError("denied"))
        )
        resp = await client.delete("/secrets/1", headers=valid_token_headers)
        assert resp.status_code == 404
        assert "detail" in resp.json()


class TestCreateShareLink:
    @pytest.mark.asyncio
    async def test_returns_201_with_share_url_key(
        self,
        client: httpx.AsyncClient,
        valid_token_headers: dict[str, str],
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(EXISTS, new=mocker.AsyncMock(return_value=True))
        mocker.patch(CREATE_SHARE_TOKEN, return_value="tok")
        resp = await client.post(
            "/secrets/1/share_link",
            json=SHARE_PAYLOAD,
            headers=valid_token_headers,
        )
        assert resp.status_code == 201
        assert "share_url" in resp.json()

    @pytest.mark.asyncio
    async def test_unknown_secret_returns_404_with_detail(
        self,
        client: httpx.AsyncClient,
        valid_token_headers: dict[str, str],
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(EXISTS, new=mocker.AsyncMock(return_value=False))
        resp = await client.post(
            "/secrets/1/share_link",
            json=SHARE_PAYLOAD,
            headers=valid_token_headers,
        )
        assert resp.status_code == 404
        assert "detail" in resp.json()


class TestAccessSharedSecret:
    @pytest.fixture
    def token(self) -> str:
        from app.core.security import create_share_token

        return create_share_token(
            secret_id=1,
            owner_id=1,
            encryption_password="strongkey",
            expires_minutes=60,
        )

    @pytest.mark.asyncio
    async def test_valid_token_returns_200_with_content_field(
        self,
        client: httpx.AsyncClient,
        token: str,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            DECRYPT,
            new=mocker.AsyncMock(return_value=(orm_secret(), "plaintext")),
        )
        resp = await client.get(f"/secrets/shared/{token}")
        assert resp.status_code == 200
        assert "content" in resp.json()

    @pytest.mark.asyncio
    async def test_invalid_token_returns_404_with_detail(
        self,
        client: httpx.AsyncClient,
    ) -> None:
        resp = await client.get("/secrets/shared/garbage.invalid.token")
        assert resp.status_code == 404
        assert "detail" in resp.json()

    @pytest.mark.asyncio
    async def test_expired_secret_returns_410(
        self,
        client: httpx.AsyncClient,
        token: str,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        mocker.patch(
            DECRYPT, new=mocker.AsyncMock(side_effect=ValueError("expired"))
        )
        resp = await client.get(f"/secrets/shared/{token}")
        assert resp.status_code == 410
