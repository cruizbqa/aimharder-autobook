"""
tests/test_booking_logic.py
Unit tests for booking window enforcement and schedule filtering.
"""

import sys
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from aimharder_client import AimHarderClient, BookingError


@pytest.fixture
def client():
    c = AimHarderClient(email="test@example.com", password="secret")
    c._authenticated = True
    return c


# ── Booking window ──────────────────────────────────────────────────

class TestBookingWindow:
    def test_window_closed_71h_before(self, client):
        class_dt = datetime.now() + timedelta(hours=71, minutes=59)
        assert not client.is_within_booking_window(class_dt)

    def test_window_open_exactly_72h_before(self, client):
        class_dt = datetime.now() + timedelta(hours=72)
        assert client.is_within_booking_window(class_dt)

    def test_window_open_less_than_72h(self, client):
        class_dt = datetime.now() + timedelta(hours=24)
        assert client.is_within_booking_window(class_dt)

    def test_window_open_past_class(self, client):
        class_dt = datetime.now() - timedelta(hours=1)
        assert client.is_within_booking_window(class_dt)


# ── book_class raises when window is closed ──────────────────────────

class TestBookClass:
    def test_raises_when_window_closed(self, client):
        future_dt = datetime.now() + timedelta(hours=73)
        with pytest.raises(BookingError, match="Booking window not open yet"):
            client.book_class("123", future_dt)

    def test_calls_api_when_window_open(self, client):
        now_plus_24h = datetime.now() + timedelta(hours=24)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"code": 200, "msg": "OK"}

        with patch.object(client.session, "post", return_value=mock_resp) as mock_post:
            result = client.book_class("abc", now_plus_24h)
            mock_post.assert_called_once()
            assert result["code"] == 200


# ── find_and_book name/time matching ────────────────────────────────

class TestFindAndBook:
    def test_raises_when_no_class_found(self, client):
        with patch.object(client, "get_schedule", return_value=[]):
            with pytest.raises(BookingError, match="No class matching"):
                client.find_and_book("WOD", "0700")

    def test_finds_and_books_matching_class(self, client):
        fake_class = {"id": "42", "name": "WOD CrossFit", "hour": "07:00"}
        target_dt = datetime.now() + timedelta(hours=24)

        with (
            patch.object(client, "get_schedule", return_value=[fake_class]),
            patch.object(
                client,
                "book_class",
                return_value={"code": 200, "msg": "OK"},
            ) as mock_book,
        ):
            result = client.find_and_book("WOD", "0700", target_date=target_dt)
            mock_book.assert_called_once()
            assert result["code"] == 200

    def test_case_insensitive_name_match(self, client):
        fake_class = {"id": "99", "name": "open box", "hour": "12:00"}
        target_dt = datetime.now() + timedelta(hours=24)

        with (
            patch.object(client, "get_schedule", return_value=[fake_class]),
            patch.object(
                client,
                "book_class",
                return_value={"code": 200, "msg": "OK"},
            ),
        ):
            result = client.find_and_book("OPEN", "1200", target_date=target_dt)
            assert result["code"] == 200


# ── Auth guard ───────────────────────────────────────────────────────

class TestAuthGuard:
    def test_get_schedule_requires_auth(self):
        c = AimHarderClient("e@mail.com", "pw")
        # _authenticated is False by default
        from aimharder_client import AuthError
        with pytest.raises(AuthError, match="Not authenticated"):
            c.get_schedule()
