import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.core.exceptions import BookingError, AuthError
from src.domain.api import AimHarderAPI
from src.domain.booking import BookingManager
from src.config.settings import AppConfig

@pytest.fixture
def mock_session():
    return MagicMock()

@pytest.fixture
def config():
    return AppConfig(
        email="test@example.com",
        password="password",
        box_name="testbox",
        class_name="WOD",
        class_time="0700",
        target_hours=72,
        retry_attempts=3,
        retry_delay=1.0,
        retry_backoff=2.0
    )

@pytest.fixture
def api(mock_session):
    return AimHarderAPI(mock_session, box_name="testbox")

@pytest.fixture
def manager(api, config):
    return BookingManager(api, config)

class TestBookingManager:
    
    def test_find_and_book_raises_when_no_class_found(self, manager, api):
        with patch.object(api, "get_schedule", return_value=[]):
            with pytest.raises(BookingError, match="No class matching"):
                manager.find_and_book(datetime.now())

    def test_find_and_book_raises_when_window_closed(self, manager, api):
        fake_class = {"id": "123", "className": "WOD CrossFit", "time": "07:00"}
        # Class is in 73 hours, window opens at class_dt - 72h
        target_dt = datetime.now() + timedelta(hours=73)
        
        with patch.object(api, "get_schedule", return_value=[fake_class]):
            with pytest.raises(BookingError, match="Booking window not open yet"):
                manager.find_and_book(target_dt)

    def test_find_and_book_success(self, manager, api):
        fake_class = {"id": "42", "className": "WOD CrossFit", "time": "07:00 - 08:00"}
        target_dt = datetime.now() + timedelta(hours=24)
        
        with (
            patch.object(api, "get_schedule", return_value=[fake_class]),
            patch.object(api, "book_class", return_value={"code": 200, "msg": "OK"}) as mock_book
        ):
            result = manager.find_and_book(target_dt)
            mock_book.assert_called_once()
            assert result["code"] == 200

    def test_book_with_retry_success_on_first_attempt(self, manager):
        target_dt = datetime.now() + timedelta(hours=24)
        with patch.object(manager, "find_and_book", return_value={"code": 200}) as mock_find:
            success = manager.book_with_retry(target_dt)
            assert success is True
            mock_find.assert_called_once()

    def test_book_with_retry_exhausts_attempts(self, manager):
        target_dt = datetime.now() + timedelta(hours=24)
        with (
            patch.object(manager, "find_and_book", side_effect=BookingError("Failed")),
            patch("time.sleep") # Don't actually sleep
        ):
            success = manager.book_with_retry(target_dt)
            assert success is False
