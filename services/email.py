import os
from email.message import EmailMessage
import smtplib
from tenacity import retry, wait_fixed, stop_after_attempt, retry_if_exception_type

# Retry if SMTP errors occur — try 3 times, wait 2 seconds between
@retry(
    retry=retry_if_exception_type(smtplib.SMTPException),
    wait=wait_fixed(2),
    stop=stop_after_attempt(3)
)
def send_email(subject: str, body: str, to: str):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.environ.get("EMAIL_FROM", "admin@libtrary.com")
    msg["To"] = to
    msg.set_content(body)

    with smtplib.SMTP(
        host=os.environ.get("EMAIL_HOST", "localhost"),
        port=int(os.environ.get("EMAIL_PORT", 10251))
    ) as server:
        server.send_message(msg)


