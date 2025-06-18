import asyncio
import os
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Debugging
from .logger import setup_logger

logger = setup_logger(__name__)


# Start the debug SMTP server
class SMTPConsoleServer:
    def __init__(self):
        self.controller = Controller(Debugging(), hostname=os.environ.get("EMAIL_HOST", "localhost"), port=int(os.environ.get("EMAIL_PORT", 10251)))

    def start(self):
        logger.info(f"Starting SMTP server on {self.controller.hostname}:{self.controller.port}")
        self.controller.start()

    def stop(self):
        self.controller.stop()
