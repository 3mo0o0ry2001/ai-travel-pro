import json
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path


def send_email(message, settings):
    if not settings.smtp_host:
        if settings.production:
            raise RuntimeError("Production mail requires SMTP")
        outbox = Path(settings.database_path).parent / "dev-mail.jsonl"
        with outbox.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(message, ensure_ascii=False) + "\n")
        return
    email = EmailMessage()
    email["From"], email["To"] = settings.mail_from, message["email"]
    email["Subject"] = message["subject"]
    email["Message-ID"] = f"<waypoint-{message['dedupe']}@{settings.mail_from.split('@')[-1]}>"
    email.set_content(message["body"])
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as client:
        client.ehlo()
        client.starttls(context=ssl.create_default_context())
        client.ehlo()
        if settings.smtp_username:
            client.login(settings.smtp_username, settings.smtp_password)
        client.send_message(email)
