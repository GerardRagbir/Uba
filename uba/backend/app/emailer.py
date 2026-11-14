"""Sending email. In the demo stack the SMTP server is Mailpit, which catches
every message and shows it in a web page instead of delivering it."""

import smtplib
from email.message import EmailMessage

from app.config import get_settings
from app.observability import log

settings = get_settings()


def send_email(to: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=5) as smtp:
            smtp.send_message(message)
        log.info("email sent", extra={"fields": {"subject": subject}})
    except OSError:
        # Never let a mail problem crash a request. Log it and move on.
        log.exception("email failed", extra={"fields": {"subject": subject}})


def send_password_reset(to: str, name: str, token: str) -> None:
    link = f"{settings.public_url}/reset-password?token={token}"
    send_email(
        to,
        "Reset your UBA password",
        f"Hi {name},\n\n"
        f"Use this link to choose a new password. It works once and expires in "
        f"{settings.reset_token_minutes} minutes.\n\n{link}\n\n"
        f"If you did not ask for this, you can ignore this email.\n",
    )
