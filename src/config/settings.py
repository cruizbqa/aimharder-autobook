import os
from dataclasses import dataclass
from typing import Optional


def _require_env(key: str) -> str:
    value = os.environ.get(key, "").strip()
    if not value:
        raise ValueError(f"Environment variable '{key}' is required but not set.")
    return value


@dataclass(frozen=True)
class AppConfig:
    email: str
    password: str
    box_name: str
    box_id: Optional[int] = None
    family_id: Optional[str] = None
    proxy: Optional[str] = None
    class_time: str = "0700"
    class_name: str = "CrossFit"
    target_hours: int = 72
    retry_attempts: int = 5
    retry_delay: float = 10.0
    retry_backoff: float = 2.0
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            email=_require_env("EMAIL"),
            password=_require_env("PASSWORD"),
            box_name=_require_env("BOX_NAME"),
            box_id=int(os.environ["BOX_ID"]) if os.environ.get("BOX_ID", "").strip() else None,
            family_id=os.environ.get("FAMILY_ID", "").strip() or None,
            proxy=os.environ.get("PROXY", "").strip() or None,
            class_time=os.environ.get("CLASS_TIME", "0700"),
            class_name=os.environ.get("CLASS_NAME", "CrossFit"),
            target_hours=int(os.environ.get("TARGET_HOURS", "72")),
            retry_attempts=int(os.environ.get("RETRY_ATTEMPTS", "5")),
            retry_delay=float(os.environ.get("RETRY_DELAY_SECONDS", "10.0")),
            retry_backoff=float(os.environ.get("RETRY_BACKOFF", "2.0")),
            telegram_token=os.environ.get("TELEGRAM_TOKEN", "").strip() or None,
            telegram_chat_id=os.environ.get("TELEGRAM_CHAT_ID", "").strip() or None,
        )
