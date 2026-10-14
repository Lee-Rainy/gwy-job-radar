import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import get_settings

logger = logging.getLogger(__name__)


def send_html_email(
    *,
    subject: str,
    html_body: str,
    recipients: list[str] | None = None,
) -> None:
    settings = get_settings()
    to_addrs = recipients or settings.mail_recipients
    if not to_addrs:
        raise ValueError("未配置 MAIL_RECIPIENTS")
    if not settings.smtp_user or not settings.smtp_password:
        raise ValueError("未配置 SMTP_USER / SMTP_PASSWORD")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.mail_from or settings.smtp_user
    msg["To"] = ", ".join(to_addrs)
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    payload = msg.as_string()

    try:
        _deliver(
            host=settings.smtp_host,
            port=settings.smtp_port,
            use_ssl=settings.smtp_use_ssl,
            user=settings.smtp_user,
            password=settings.smtp_password,
            mail_from=msg["From"],
            to_addrs=to_addrs,
            payload=payload,
        )
    except ssl.SSLError as exc:
        if not _is_ssl_version_mismatch(exc):
            raise
        fallback_port = 587 if settings.smtp_port == 465 else settings.smtp_port
        logger.warning(
            "SMTP SSL 连接失败 (%s)，尝试 %s:%s STARTTLS",
            exc,
            settings.smtp_host,
            fallback_port,
        )
        _deliver(
            host=settings.smtp_host,
            port=fallback_port,
            use_ssl=False,
            user=settings.smtp_user,
            password=settings.smtp_password,
            mail_from=msg["From"],
            to_addrs=to_addrs,
            payload=payload,
        )


def _is_ssl_version_mismatch(exc: BaseException) -> bool:
    text = str(exc).lower()
    return "wrong version number" in text or "wrong_version_number" in text


def _deliver(
    *,
    host: str,
    port: int,
    use_ssl: bool,
    user: str,
    password: str,
    mail_from: str,
    to_addrs: list[str],
    payload: str,
) -> None:
    if use_ssl:
        with smtplib.SMTP_SSL(host, port, timeout=30) as server:
            server.login(user, password)
            server.sendmail(mail_from, to_addrs, payload)
        return

    with smtplib.SMTP(host, port, timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(user, password)
        server.sendmail(mail_from, to_addrs, payload)
