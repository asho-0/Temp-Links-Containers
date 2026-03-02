import logging
import ssl
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings, templates

logger = logging.getLogger(__name__)


class EmailService:
    async def _send(self, to: str, subject: str, html: str) -> None:
        tls_context = ssl.create_default_context()
        if settings.SSL_CERT_PATH:
            tls_context.load_verify_locations(cafile=settings.SSL_CERT_PATH)

        message = MIMEMultipart("alternative")
        message["From"] = settings.SMTP_FROM
        message["To"] = to
        message["Subject"] = subject
        message.attach(MIMEText(html, "html"))

        tls_context = ssl.create_default_context()
        tls_context.check_hostname = False
        tls_context.verify_mode = ssl.CERT_NONE

        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        logger.info("Email '%s' sent to %s", subject, to)

    async def send_verification_email(self, email: str, token: str) -> None:
        verify_url = f"{settings.APP_BASE_URL}/auth/verify?token={token}"
        html = templates.get_template("email/verify_email.html").render(
            verify_url=verify_url,
            expire_hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS,
        )
        await self._send(
            to=email, subject="Confirm your registration", html=html
        )
