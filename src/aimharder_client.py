"""
AimHarder API Client
Connects to [BOX_NAME].aimharder.com and automates class booking.
The booking window opens 72h before the class.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Optional

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://aimharder.com"
BOX_SUBDOMAIN = "[BOX_NAME]"
BOX_URL = f"https://{BOX_SUBDOMAIN}.aimharder.com"


class AimHarderError(Exception):
    pass


class AuthError(AimHarderError):
    pass


class BookingError(AimHarderError):
    pass


class AimHarderClient:
    """
    Client for interacting with the AimHarder platform.

    Handles session authentication, class listing, and booking logic
    enforcing the 72-hour advance booking window constraint.
    """

    BOOKING_WINDOW_HOURS = 72

    def __init__(
        self,
        email: str,
        password: str,
        box_name: str = BOX_SUBDOMAIN,
        box_id: Optional[int] = None,
        family_id: Optional[str] = None,
        proxy: Optional[str] = None,
    ):
        self.email = email
        self.password = password
        self.box_name = box_name
        self.box_id = box_id
        self.family_id = family_id

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": BOX_URL,
                "Referer": f"{BOX_URL}/",
            }
        )

        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}
            logger.info("Using proxy: %s", proxy)

        self._authenticated = False

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def login(self) -> bool:
        """
        Authenticate against AimHarder.
        Returns True on success, raises AuthError on failure.
        """
        logger.info("Logging in as %s …", self.email)

        payload = {
            "login": self.email,
            "psw": self.password,
            "box": self.box_name,
            "remember": "false",
        }

        resp = self.session.post(
            f"{BASE_URL}/api/login",
            data=payload,
            timeout=30,
        )

        if resp.status_code != 200:
            raise AuthError(
                f"Login HTTP error {resp.status_code}: {resp.text[:200]}"
            )

        data = resp.json()
        code = data.get("code", -1)

        if code == 200:
            self._authenticated = True
            logger.info("Login successful.")
            return True

        error_msg = data.get("msg", "Unknown error")
        raise AuthError(f"Login failed (code {code}): {error_msg}")

    def logout(self) -> None:
        """Invalidate the current session."""
        try:
            self.session.get(f"{BASE_URL}/Util/logout.php", timeout=10)
        except requests.RequestException:
            pass
        self._authenticated = False
        logger.info("Logged out.")

    def _require_auth(self) -> None:
        if not self._authenticated:
            raise AuthError("Not authenticated. Call login() first.")

    # ------------------------------------------------------------------
    # Schedule / class listing
    # ------------------------------------------------------------------

    def get_schedule(self, target_date: Optional[datetime] = None) -> list[dict]:
        """
        Fetch the class schedule for a given date (defaults to today).
        Returns a list of class dicts with keys:
            id, name, hour, bookState, aforo, apuntados, date, ...
        """
        self._require_auth()

        if target_date is None:
            target_date = datetime.now()

        date_str = target_date.strftime("%Y-%m-%d")
        logger.info("Fetching schedule for %s …", date_str)

        params = {
            "day": target_date.strftime("%Y%m%d"),
            "box": self.box_id or self.box_name,
        }

        resp = self.session.get(
            f"{BOX_URL}/api/bookings",
            params=params,
            timeout=30,
        )

        if resp.status_code != 200:
            raise AimHarderError(
                f"Schedule fetch error {resp.status_code}: {resp.text[:200]}"
            )

        data = resp.json()
        classes = data.get("bookings", [])
        logger.info("Found %d classes on %s.", len(classes), date_str)
        return classes

    # ------------------------------------------------------------------
    # Booking logic
    # ------------------------------------------------------------------

    def is_within_booking_window(self, class_datetime: datetime) -> bool:
        """
        Returns True if now ≥ class_datetime - 72h
        (i.e., the booking window is already open).
        """
        window_opens = class_datetime - timedelta(hours=self.BOOKING_WINDOW_HOURS)
        return datetime.now() >= window_opens

    def book_class(self, class_id: str, class_datetime: datetime) -> dict:
        """
        Book a single class by its ID.

        Raises BookingError if the booking window is not open yet,
        or if the platform returns a non-success response.
        """
        self._require_auth()

        if not self.is_within_booking_window(class_datetime):
            opens_at = class_datetime - timedelta(hours=self.BOOKING_WINDOW_HOURS)
            raise BookingError(
                f"Booking window not open yet. "
                f"Opens at {opens_at.strftime('%Y-%m-%d %H:%M')} "
                f"(72 h before class at {class_datetime.strftime('%Y-%m-%d %H:%M')})."
            )

        logger.info("Booking class %s at %s …", class_id, class_datetime)

        payload: dict = {
            "id": class_id,
            "box": self.box_id or self.box_name,
            "day": class_datetime.strftime("%Y%m%d"),
        }

        if self.family_id:
            payload["familyId"] = self.family_id

        resp = self.session.post(
            f"{BOX_URL}/api/book",
            data=payload,
            timeout=30,
        )

        if resp.status_code != 200:
            raise BookingError(
                f"Booking HTTP error {resp.status_code}: {resp.text[:200]}"
            )

        data = resp.json()
        code = data.get("code", -1)
        msg = data.get("msg", "")

        if code in (200, 201):
            logger.info("Class %s booked successfully.", class_id)
            return data

        raise BookingError(f"Booking failed (code {code}): {msg}")

    def cancel_booking(self, class_id: str, class_datetime: datetime) -> dict:
        """Cancel an existing booking."""
        self._require_auth()

        logger.info("Cancelling booking for class %s …", class_id)

        payload: dict = {
            "id": class_id,
            "box": self.box_id or self.box_name,
            "day": class_datetime.strftime("%Y%m%d"),
        }

        if self.family_id:
            payload["familyId"] = self.family_id

        resp = self.session.post(
            f"{BOX_URL}/api/removeBook",
            data=payload,
            timeout=30,
        )

        if resp.status_code != 200:
            raise BookingError(
                f"Cancel HTTP error {resp.status_code}: {resp.text[:200]}"
            )

        data = resp.json()
        code = data.get("code", -1)
        msg = data.get("msg", "")

        if code == 200:
            logger.info("Booking cancelled successfully.")
            return data

        raise BookingError(f"Cancel failed (code {code}): {msg}")

    # ------------------------------------------------------------------
    # Convenience: find & book by name/time
    # ------------------------------------------------------------------

    def find_and_book(
        self,
        class_name_fragment: str,
        class_time: str,   # "HHMM"
        target_date: Optional[datetime] = None,
        retry_attempts: int = 3,
        retry_delay: float = 5.0,
    ) -> dict:
        """
        High-level helper:
        1. Fetch schedule for target_date.
        2. Find a class whose name contains class_name_fragment and
           whose time matches class_time (format "HHMM").
        3. Attempt to book it, retrying on transient errors.
        """
        if target_date is None:
            target_date = datetime.now()

        classes = self.get_schedule(target_date)

        matched = [
            c for c in classes
            if class_name_fragment.upper() in c.get("name", "").upper()
            and c.get("hour", "").replace(":", "") == class_time
        ]

        if not matched:
            raise BookingError(
                f"No class matching name='{class_name_fragment}' "
                f"time='{class_time}' on {target_date.date()}."
            )

        target_class = matched[0]
        class_id = str(target_class["id"])

        hour_str = target_class.get("hour", "0000").replace(":", "")
        hour = int(hour_str[:2])
        minute = int(hour_str[2:]) if len(hour_str) >= 4 else 0
        class_dt = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

        last_exc: Exception = BookingError("Unknown error")
        for attempt in range(1, retry_attempts + 1):
            try:
                return self.book_class(class_id, class_dt)
            except BookingError as exc:
                last_exc = exc
                logger.warning(
                    "Attempt %d/%d failed: %s", attempt, retry_attempts, exc
                )
                if attempt < retry_attempts:
                    time.sleep(retry_delay)

        raise last_exc

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "AimHarderClient":
        self.login()
        return self

    def __exit__(self, *_) -> None:
        self.logout()
