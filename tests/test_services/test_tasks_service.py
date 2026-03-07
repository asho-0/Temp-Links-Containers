import pytest
import pytest_mock


class TestSyncSecretService:
    @pytest.fixture
    def repo(self, mocker: pytest_mock.MockerFixture) -> pytest_mock.MockType:
        r = mocker.MagicMock()
        r.delete_expired_secrets.return_value = 0
        return r

    @pytest.fixture
    def service(
        self,
        mocker: pytest_mock.MockerFixture,
        repo: pytest_mock.MockType,
    ) -> object:
        mocker.patch(
            "app.services.cleaner.worker.SyncSecretRepository",
            return_value=repo,
        )
        from app.services.cleaner.worker import SyncSecretService

        svc = SyncSecretService(mocker.MagicMock())
        svc._repo = repo
        return svc

    def test_delegates_to_repo_with_given_days(
        self,
        service: object,
        repo: pytest_mock.MockType,
    ) -> None:
        service.cleanup_expired_secrets(days=14)
        repo.delete_expired_secrets.assert_called_once_with(14)

    def test_default_days_is_30(
        self,
        service: object,
        repo: pytest_mock.MockType,
    ) -> None:
        service.cleanup_expired_secrets()
        repo.delete_expired_secrets.assert_called_once_with(30)

    def test_returns_deleted_count(
        self,
        service: object,
        repo: pytest_mock.MockType,
    ) -> None:
        repo.delete_expired_secrets.return_value = 5
        assert service.cleanup_expired_secrets() == 5

    def test_returns_zero_when_none_deleted(
        self,
        service: object,
        repo: pytest_mock.MockType,
    ) -> None:
        repo.delete_expired_secrets.return_value = 0
        assert service.cleanup_expired_secrets() == 0
