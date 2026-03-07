import pytest
import pytest_mock
from typing import Any


def apply_task(task: Any, *args: Any, **kwargs: Any) -> Any:
    """Run a Celery task synchronously in-process, no broker needed."""
    result = task.apply(args=args, kwargs=kwargs)
    return result.get(propagate=True)


class TestSendVerificationEmailTask:
    def test_runs_asyncio_run(self, mocker: pytest_mock.MockerFixture) -> None:
        mock_run = mocker.patch("asyncio.run")
        mocker.patch(
            "app.services.auth.email.EmailService.send_verification_email"
        )

        from app.tasks.worker import send_verification_email_task

        apply_task(send_verification_email_task, "user@example.com", "tok")

        mock_run.assert_called_once()

    def test_retries_on_smtp_failure(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        mocker.patch("asyncio.run", side_effect=OSError("smtp down"))

        from app.tasks.worker import send_verification_email_task

        send_verification_email_task.max_retries = 0
        with pytest.raises(Exception):
            apply_task(send_verification_email_task, "user@example.com", "tok")

    def test_no_exception_on_success(
        self, mocker: pytest_mock.MockerFixture
    ) -> None:
        mocker.patch("asyncio.run", return_value=None)

        from app.tasks.worker import send_verification_email_task

        apply_task(send_verification_email_task, "user@example.com", "tok")


class TestCleanupOldSecrets:
    @pytest.fixture(autouse=True)
    def _patch_db_and_service(self, mocker: pytest_mock.MockerFixture) -> None:
        mock_session = mocker.MagicMock()
        mock_ctx = mocker.MagicMock()
        mock_ctx.__enter__ = mocker.MagicMock(return_value=mock_session)
        mock_ctx.__exit__ = mocker.MagicMock(return_value=False)
        mocker.patch("app.db.session.SyncSessionLocal", return_value=mock_ctx)

        self.mock_service: pytest_mock.MockType = mocker.MagicMock()
        self.mock_service.cleanup_expired_secrets.return_value = 0
        mocker.patch(
            "app.services.cleaner.worker.SyncSecretService",
            return_value=self.mock_service,
        )

    def test_returns_count_from_service(self) -> None:
        self.mock_service.cleanup_expired_secrets.return_value = 7
        from app.tasks.worker import cleanup_old_secrets

        assert apply_task(cleanup_old_secrets) == 7

    def test_calls_cleanup_with_30_days(self) -> None:
        from app.tasks.worker import cleanup_old_secrets

        apply_task(cleanup_old_secrets)
        self.mock_service.cleanup_expired_secrets.assert_called_once_with(
            days=30
        )

    def test_returns_zero_when_nothing_deleted(self) -> None:
        self.mock_service.cleanup_expired_secrets.return_value = 0
        from app.tasks.worker import cleanup_old_secrets

        assert apply_task(cleanup_old_secrets) == 0
