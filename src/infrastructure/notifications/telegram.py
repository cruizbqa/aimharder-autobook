import logging
import requests
from .base import Notifier

logger = logging.getLogger(__name__)

class TelegramNotifier(Notifier):
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}/sendMessage"

    def send_message(self, message: str) -> None:
        """Send a simple message via Telegram bot."""
        if not self.token or not self.chat_id:
            logger.debug("Telegram credentials not fully set, skipping notification.")
            return

        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }

        try:
            resp = requests.post(self.base_url, data=payload, timeout=10)
            if resp.status_code != 200:
                logger.error(f"Telegram API returned error {resp.status_code}: {resp.text}")
            else:
                logger.info("Telegram notification sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
