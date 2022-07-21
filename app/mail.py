import smtplib
import ssl

from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid
from typing import Optional

from app.settings import Settings

context = ssl.create_default_context()


def send_mail(to_addr: str, subject: str, message: str, to_name: Optional[str] = None) -> None:
    with smtplib.SMTP_SSL(Settings.SMTP_SERVER, Settings.SMTP_PORT, context=context) as server:
        server.login(Settings.SMTP_USER, Settings.SMTP_PASS)

        msg = EmailMessage()

        # We have to add Date and Message-ID fields ourselves to pass DKIM verification
        msg['Date'] = formatdate()
        msg['Message-ID'] = make_msgid(domain=Settings.MAIN_DOMAIN)

        msg['Subject'] = subject
        msg['From'] = formataddr((Settings.MAIL_FROM_NAME, Settings.SMTP_USER))
        msg['To'] = formataddr((to_name, to_addr))

        msg.set_content(f"<html><pre>{message}</pre></html>", subtype='html')

        server.send_message(msg, Settings.SMTP_USER, to_addr)
