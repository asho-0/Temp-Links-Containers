import pytest
import pytest_mock
import bcrypt

from app.services.auth.auth import AuthService
from app.services.auth.exceptions import (
    EmailAlreadyRegistered,
    UsernameTaken,
    InvalidCredentials,
    EmailNotVerified,
    InvalidVerificationToken,
)


@pytest.fixture
def repo(mocker: pytest_mock.MockerFixture) -> pytest_mock.MockType:
    r = mocker.AsyncMock()
    r.get_by_email.return_value = None
    r.get_by_username.return_value = None
    r.get_by_id.return_value = None
    return r


@pytest.fixture
def service(repo: pytest_mock.MockType) -> AuthService:
    return AuthService(repo=repo)


@pytest.fixture
def verified_user(mocker: pytest_mock.MockerFixture) -> pytest_mock.MockType:
    pw = "S3cure!"
    hashed = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
    u = mocker.MagicMock()
    u.id = 1
    u.email = "alice@example.com"
    u.username = "alice"
    u.hashed_password = hashed
    u.email_verified = True
    u.verification_token = None
    u._raw_password = pw
    return u


@pytest.fixture
def unverified_user(
    verified_user: pytest_mock.MockType,
) -> pytest_mock.MockType:
    verified_user.email_verified = False
    verified_user.verification_token = "tok"
    return verified_user


class TestRegister:
    @pytest.mark.asyncio
    async def test_new_user_calls_repo_add(
        self,
        service: AuthService,
        repo: pytest_mock.MockType,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        repo.add.return_value = mocker.MagicMock(id=1)
        mocker.patch("app.services.auth.auth.send_verification_email_task")
        await service.register(
            username="alice", email="alice@example.com", password="S3cure!"
        )
        repo.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_new_user_dispatches_email_task(
        self,
        service: AuthService,
        repo: pytest_mock.MockType,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        repo.add.return_value = mocker.MagicMock(id=1)
        mock_task = mocker.patch(
            "app.services.auth.auth.send_verification_email_task"
        )
        await service.register(
            username="alice", email="alice@example.com", password="S3cure!"
        )
        mock_task.delay.assert_called_once()

    @pytest.mark.asyncio
    async def test_password_is_not_stored_as_plaintext(
        self,
        service: AuthService,
        repo: pytest_mock.MockType,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        repo.add.return_value = mocker.MagicMock(id=1)
        mocker.patch("app.services.auth.auth.send_verification_email_task")
        await service.register(
            username="alice", email="alice@example.com", password="S3cure!"
        )
        stored_user = repo.add.call_args[0][0]
        assert stored_user.hashed_password != "S3cure!"

    @pytest.mark.asyncio
    async def test_duplicate_email_raises(
        self,
        service: AuthService,
        repo: pytest_mock.MockType,
        verified_user: pytest_mock.MockType,
    ) -> None:
        repo.get_by_email.return_value = verified_user
        with pytest.raises(EmailAlreadyRegistered):
            await service.register(
                username="other", email="alice@example.com", password="pw"
            )

    @pytest.mark.asyncio
    async def test_duplicate_username_raises(
        self,
        service: AuthService,
        repo: pytest_mock.MockType,
        verified_user: pytest_mock.MockType,
    ) -> None:
        repo.get_by_username.return_value = verified_user
        with pytest.raises(UsernameTaken):
            await service.register(
                username="alice", email="new@example.com", password="pw"
            )


class TestVerifyEmail:
    @pytest.mark.asyncio
    async def test_valid_token_marks_user_as_verified(
        self,
        service: AuthService,
        repo: pytest_mock.MockType,
        unverified_user: pytest_mock.MockType,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        repo.get_by_email.return_value = unverified_user
        mocker.patch(
            "app.services.auth.auth.decode_verification_token",
            return_value="alice@example.com",
        )
        await service.verify_email("tok")
        assert unverified_user.email_verified is True
        repo.update.assert_called_once_with(unverified_user)

    @pytest.mark.asyncio
    async def test_already_verified_skips_update(
        self,
        service: AuthService,
        repo: pytest_mock.MockType,
        verified_user: pytest_mock.MockType,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        repo.get_by_email.return_value = verified_user
        mocker.patch(
            "app.services.auth.auth.decode_verification_token",
            return_value="alice@example.com",
        )
        await service.verify_email("tok")
        repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_expired_token_raises(
        self,
        service: AuthService,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        import jwt

        mocker.patch(
            "app.services.auth.auth.decode_verification_token",
            side_effect=jwt.ExpiredSignatureError,
        )
        with pytest.raises(InvalidVerificationToken):
            await service.verify_email("expired")

    @pytest.mark.asyncio
    async def test_invalid_token_raises(
        self,
        service: AuthService,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        import jwt

        mocker.patch(
            "app.services.auth.auth.decode_verification_token",
            side_effect=jwt.InvalidTokenError,
        )
        with pytest.raises(InvalidVerificationToken):
            await service.verify_email("garbage")

    @pytest.mark.asyncio
    async def test_unknown_email_raises(
        self,
        service: AuthService,
        repo: pytest_mock.MockType,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        repo.get_by_email.return_value = None
        mocker.patch(
            "app.services.auth.auth.decode_verification_token",
            return_value="ghost@example.com",
        )
        with pytest.raises(InvalidVerificationToken):
            await service.verify_email("tok")


class TestLogin:
    @pytest.mark.asyncio
    async def test_correct_credentials_return_token_string(
        self,
        service: AuthService,
        repo: pytest_mock.MockType,
        verified_user: pytest_mock.MockType,
    ) -> None:
        repo.get_by_email.return_value = verified_user
        token: str = await service.login(
            email="alice@example.com", password=verified_user._raw_password
        )
        assert isinstance(token, str)
        assert len(token) > 0

    @pytest.mark.asyncio
    async def test_wrong_password_raises(
        self,
        service: AuthService,
        repo: pytest_mock.MockType,
        verified_user: pytest_mock.MockType,
    ) -> None:
        repo.get_by_email.return_value = verified_user
        with pytest.raises(InvalidCredentials):
            await service.login(email="alice@example.com", password="wrong")

    @pytest.mark.asyncio
    async def test_unknown_email_raises(
        self,
        service: AuthService,
        repo: pytest_mock.MockType,
    ) -> None:
        repo.get_by_email.return_value = None
        with pytest.raises(InvalidCredentials):
            await service.login(email="ghost@example.com", password="any")

    @pytest.mark.asyncio
    async def test_unverified_email_raises(
        self,
        service: AuthService,
        repo: pytest_mock.MockType,
        unverified_user: pytest_mock.MockType,
    ) -> None:
        repo.get_by_email.return_value = unverified_user
        with pytest.raises(EmailNotVerified):
            await service.login(
                email="alice@example.com",
                password=unverified_user._raw_password,
            )


class TestDeleteUser:
    @pytest.mark.asyncio
    async def test_existing_user_is_deleted(
        self,
        service: AuthService,
        repo: pytest_mock.MockType,
        verified_user: pytest_mock.MockType,
    ) -> None:
        repo.get_by_id.return_value = verified_user
        await service.delete_user(1)
        repo.delete.assert_called_once_with(verified_user)

    @pytest.mark.asyncio
    async def test_nonexistent_user_raises(
        self,
        service: AuthService,
        repo: pytest_mock.MockType,
    ) -> None:
        repo.get_by_id.return_value = None
        with pytest.raises(InvalidCredentials):
            await service.delete_user(99)
