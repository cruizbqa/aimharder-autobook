import pytest
import os
from unittest.mock import patch
from src.config.settings import AppConfig

def test_config_from_env_success():
    env = {
        "EMAIL": "test@example.com",
        "PASSWORD": "password",
        "BOX_NAME": "test_crossfit",
        "BOX_ID": "123",
        "CLASS_TIME": "0800",
        "CLASS_NAME": "WOD",
        "TARGET_HOURS": "72",
        "RETRY_ATTEMPTS": "5",
        "RETRY_DELAY_SECONDS": "10.0",
        "RETRY_BACKOFF": "2.0"
    }
    with patch.dict(os.environ, env):
        cfg = AppConfig.from_env()
        assert cfg.email == "test@example.com"
        assert cfg.box_name == "test_crossfit"
        assert cfg.box_id == 123
        assert cfg.class_time == "0800"

def test_config_from_env_missing_required():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="is required"):
            AppConfig.from_env()
