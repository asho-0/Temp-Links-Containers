import pytest
import pytest_mock

from app.services.bl.secret import SecretService

GET_STRATEGY_PATH = "app.services.bl.secret.get_strategy"


@pytest.fixture
def repo(mocker: pytest_mock.MockerFixture) -> pytest_mock.MockType:
    r = mocker.AsyncMock()
    r.add.return_value = None
    r.delete.return_value = 1
    r.list_for_user.return_value = []
    r.get_by_id_and_owner.return_value = None
    r.mark_as_read = mocker.AsyncMock()
    r.exists_for_owner.return_value = True
    r.decode_payload.return_value = b"ciphertext"
    return r


@pytest.fixture
def service(repo: pytest_mock.MockType) -> SecretService:
    return SecretService(repo=repo)


@pytest.fixture
def secret(mocker: pytest_mock.MockerFixture) -> pytest_mock.MockType:
    s = mocker.MagicMock()
    s.id = 1
    s.is_read = False
    return s


@pytest.fixture
def read_secret(secret: pytest_mock.MockType) -> pytest_mock.MockType:
    secret.is_read = True
    return secret


@pytest.fixture
def mock_strategy(mocker: pytest_mock.MockerFixture) -> pytest_mock.MockType:
    strategy = mocker.MagicMock()
    strategy.encrypt.return_value = b"ENC"
    strategy.decrypt.return_value = "plaintext"
    mocker.patch(GET_STRATEGY_PATH, return_value=strategy)
    return strategy


class TestCreate:
    @pytest.mark.asyncio
    async def test_calls_encrypt_with_plaintext(
        self,
        service: SecretService,
        repo: pytest_mock.MockType,
        secret: pytest_mock.MockType,
        mock_strategy: pytest_mock.MockType,
    ) -> None:
        repo.add.return_value = secret
        await service.create(
            creator_id=1, title="pw", plaintext="hunter2", password="key"
        )
        mock_strategy.encrypt.assert_called_once_with("hunter2")

    @pytest.mark.asyncio
    async def test_passes_encrypted_payload_to_repo(
        self,
        service: SecretService,
        repo: pytest_mock.MockType,
        secret: pytest_mock.MockType,
        mock_strategy: pytest_mock.MockType,
    ) -> None:
        repo.add.return_value = secret
        await service.create(
            creator_id=1, title="pw", plaintext="hunter2", password="key"
        )
        assert "encrypted_payload" in repo.add.call_args.kwargs

    @pytest.mark.asyncio
    async def test_returns_secret_from_repo(
        self,
        service: SecretService,
        repo: pytest_mock.MockType,
        secret: pytest_mock.MockType,
        mock_strategy: pytest_mock.MockType,
    ) -> None:
        repo.add.return_value = secret
        result = await service.create(
            creator_id=1, title="pw", plaintext="hunter2", password="key"
        )
        assert result is secret


class TestDelete:
    @pytest.mark.asyncio
    async def test_delegates_to_repo(
        self,
        service: SecretService,
        repo: pytest_mock.MockType,
    ) -> None:
        repo.delete.return_value = 1
        await service.delete(secret_id=1, owner_id=1)
        repo.delete.assert_called_once_with(secret_id=1, owner_id=1)

    @pytest.mark.asyncio
    async def test_zero_rows_deleted_raises_permission_error(
        self,
        service: SecretService,
        repo: pytest_mock.MockType,
    ) -> None:
        repo.delete.return_value = 0
        with pytest.raises(PermissionError):
            await service.delete(secret_id=99, owner_id=1)


class TestListForUser:
    @pytest.mark.asyncio
    async def test_returns_repo_result(
        self,
        service: SecretService,
        repo: pytest_mock.MockType,
        secret: pytest_mock.MockType,
    ) -> None:
        repo.list_for_user.return_value = [secret, secret]
        result = await service.list_for_user(owner_id=1)
        assert result == [secret, secret]

    @pytest.mark.asyncio
    async def test_empty_list_passthrough(
        self,
        service: SecretService,
        repo: pytest_mock.MockType,
    ) -> None:
        repo.list_for_user.return_value = []
        result = await service.list_for_user(owner_id=1)
        assert result == []


class TestGetAndDecrypt:
    @pytest.mark.asyncio
    async def test_returns_secret_and_plaintext(
        self,
        service: SecretService,
        repo: pytest_mock.MockType,
        read_secret: pytest_mock.MockType,
        mock_strategy: pytest_mock.MockType,
    ) -> None:
        repo.get_by_id_and_owner.return_value = read_secret
        s, text = await service.get_and_decrypt(
            secret_id=1, owner_id=1, password="key"
        )
        assert s is read_secret
        assert text == "plaintext"

    @pytest.mark.asyncio
    async def test_marks_as_read_on_first_access(
        self,
        service: SecretService,
        repo: pytest_mock.MockType,
        secret: pytest_mock.MockType,
        mock_strategy: pytest_mock.MockType,
    ) -> None:
        repo.get_by_id_and_owner.return_value = secret
        await service.get_and_decrypt(secret_id=1, owner_id=1, password="key")
        repo.mark_as_read.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_does_not_mark_as_read_when_already_read(
        self,
        service: SecretService,
        repo: pytest_mock.MockType,
        read_secret: pytest_mock.MockType,
        mock_strategy: pytest_mock.MockType,
    ) -> None:
        repo.get_by_id_and_owner.return_value = read_secret
        await service.get_and_decrypt(secret_id=1, owner_id=1, password="key")
        repo.mark_as_read.assert_not_called()

    @pytest.mark.asyncio
    async def test_secret_not_found_raises_permission_error(
        self,
        service: SecretService,
        repo: pytest_mock.MockType,
        mock_strategy: pytest_mock.MockType,
    ) -> None:
        repo.get_by_id_and_owner.return_value = None
        with pytest.raises(PermissionError):
            await service.get_and_decrypt(
                secret_id=99, owner_id=1, password="key"
            )

    @pytest.mark.asyncio
    async def test_none_password_coerced_to_empty_string(
        self,
        service: SecretService,
        repo: pytest_mock.MockType,
        read_secret: pytest_mock.MockType,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        repo.get_by_id_and_owner.return_value = read_secret
        mock_get = mocker.patch(
            GET_STRATEGY_PATH,
            return_value=mocker.MagicMock(
                decrypt=mocker.MagicMock(return_value="x")
            ),
        )
        await service.get_and_decrypt(secret_id=1, owner_id=1, password=None)
        called_password: str = mock_get.call_args[0][0]
        assert called_password == ""


class TestExistsForOwner:
    @pytest.mark.asyncio
    async def test_returns_true_when_owned(
        self,
        service: SecretService,
        repo: pytest_mock.MockType,
    ) -> None:
        repo.exists_for_owner.return_value = True
        assert await service.exists_for_owner(secret_id=1, owner_id=1) is True

    @pytest.mark.asyncio
    async def test_returns_false_when_not_owned(
        self,
        service: SecretService,
        repo: pytest_mock.MockType,
    ) -> None:
        repo.exists_for_owner.return_value = False
        assert await service.exists_for_owner(secret_id=99, owner_id=1) is False
