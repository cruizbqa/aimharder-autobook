import logging
import requests
from datetime import datetime
from typing import Optional
from src.core.exceptions import AimHarderError, BookingError

logger = logging.getLogger(__name__)

class AimHarderAPI:
    def __init__(self, session: requests.Session, box_name: str, box_id: Optional[int] = None):
        self.session = session
        self.box_name = box_name
        self.box_id = box_id
        self.box_url = f"https://{box_name}.aimharder.com"

    def get_schedule(self, target_date: datetime) -> list[dict]:
        """Fetch the class schedule for a given date."""
        date_str = target_date.strftime("%Y%m%d")
        logger.info(f"Fetching schedule for {date_str} on {self.box_name}...")

        params = {
            "day": date_str,
            "box": self.box_id or self.box_name,
        }

        resp = self.session.get(
            f"{self.box_url}/api/bookings",
            params=params,
            timeout=30,
        )

        if resp.status_code != 200:
            raise AimHarderError(f"Schedule fetch error {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        return data.get("bookings", [])

    def book_class(self, class_id: str, class_datetime: datetime, family_id: Optional[str] = None) -> dict:
        """Book a single class by its ID."""
        date_str = class_datetime.strftime("%Y%m%d")
        logger.info(f"Booking class {class_id} for {date_str}...")

        payload = {
            "id": class_id,
            "day": date_str,
            "insist": "0",
            "familyId": family_id or "",
        }

        resp = self.session.post(
            f"{self.box_url}/api/book",
            data=payload,
            timeout=30,
        )

        if resp.status_code != 200:
            raise BookingError(f"Booking HTTP error {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        code = data.get("code", -1)
        msg = data.get("msg", "")

        if code in (200, 201):
            logger.info(f"Class {class_id} booked successfully.")
            return data

        raise BookingError(f"Booking failed (code {code}): {msg}")

    def cancel_booking(self, class_id: str, class_datetime: datetime, family_id: Optional[str] = None) -> dict:
        """Cancel an existing booking."""
        date_str = class_datetime.strftime("%Y%m%d")
        logger.info(f"Cancelling booking for class {class_id} on {date_str}...")

        payload = {
            "id": class_id,
            "day": date_str,
            "familyId": family_id or "",
        }

        resp = self.session.post(
            f"{self.box_url}/api/removeBook",
            data=payload,
            timeout=30,
        )

        if resp.status_code != 200:
            raise AimHarderError(f"Cancel HTTP error {resp.status_code}: {resp.text[:200]}")

        data = resp.json()
        code = data.get("code", -1)
        if code == 200:
            logger.info("Booking cancelled successfully.")
            return data

        raise BookingError(f"Cancel failed (code {code}): {data.get('msg', '')}")
