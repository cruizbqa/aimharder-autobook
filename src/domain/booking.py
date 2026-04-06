import time
import logging
from datetime import datetime, timedelta
from typing import Optional
from src.core.exceptions import BookingError, AimHarderError, AlreadyBookedError
from src.domain.api import AimHarderAPI

logger = logging.getLogger(__name__)

class BookingManager:
    def __init__(self, api: AimHarderAPI, config: "AppConfig"):
        self.api = api
        self.config = config

    def find_and_book(self, target_date: datetime) -> dict:
        """Helper to find and book a class based on name and time."""
        schedule = self.api.get_schedule(target_date)
        
        target_name_clean = self.config.class_name.strip().upper()
        target_hour_clean = self.config.class_time.strip().replace(":", "").zfill(4)

        logger.info(f"Busca: '{target_name_clean}' a las '{target_hour_clean}'")
        
        matched_classes = []
        for c in schedule:
            # Soporte para campos de API: 'className' o 'name'
            raw_name = c.get("className") or c.get("name", "")
            c_name = raw_name.strip().upper()
            
            # Soporte para campos de tiempo: 'time' (ej: "08:00 - 09:00") o 'hour' (ej: "08:00")
            raw_time_str = c.get("time") or c.get("hour", "")
            # Extraer solo el HH:MM de inicio
            start_time_str = raw_time_str.split("-")[0].strip()
            c_hour = start_time_str.replace(":", "").zfill(4)
            
            if target_name_clean in c_name and c_hour == target_hour_clean:
                matched_classes.append(c)

        if not matched_classes:
            # Debug: show what we found instead (usando los nuevos campos)
            available = [f"{c.get('className') or c.get('name')} ({c.get('time') or c.get('hour')})" for c in schedule[:10]]
            logger.error(f"No match. Muestra del horario: {available}")
            raise BookingError(
                f"No class matching name='{self.config.class_name}' "
                f"time='{self.config.class_time}' on {target_date.date()}."
            )

        target_class = matched_classes[0]
        class_id = str(target_class["id"])

        # Construct full class datetime
        # Unify field access same as matching logic
        raw_time_str = target_class.get("time") or target_class.get("hour", "00:00")
        hour_str = raw_time_str.split("-")[0].strip().replace(":", "").zfill(4)
        
        hour = int(hour_str[:2])
        minute = int(hour_str[2:]) if len(hour_str) >= 4 else 0
        class_dt = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Basic 72h window check
        opens_at = class_dt - timedelta(hours=72)
        # Fix: compare aware with aware
        if datetime.now(target_date.tzinfo) < opens_at:
            raise BookingError(f"Booking window not open yet. It opens at {opens_at}.")

        return self.api.book_class(class_id, class_dt, family_id=self.config.family_id)

    def book_with_retry(self, target_date: datetime) -> bool:
        """Main booking orchestration with exponential backoff retry."""
        attempts = self.config.retry_attempts
        delay = self.config.retry_delay
        backoff = self.config.retry_backoff

        for attempt in range(1, attempts + 1):
            logger.info(f"━━━━━━━━ Intento {attempt}/{attempts} [{datetime.now().strftime('%H:%M:%S')}]")
            last_exc = None
            try:
                result = self.find_and_book(target_date)
                logger.info(f"✅ Reserva completada! Respuesta: {result}")
                return result
            except AlreadyBookedError as exc:
                # Abortamos reintentos inmediatamente si ya hay algo reservado
                logger.error(f"⚠️  Abortando reintentos: {exc}")
                raise exc
            except (BookingError, AimHarderError) as exc:
                last_exc = exc
                logger.warning(f"⚠️  Intento {attempt} fallido: {exc}")

            if attempt < attempts:
                wait = delay * (backoff ** (attempt - 1))
                logger.info(f"   Esperando {wait:.0f}s antes de reintentar...")
                time.sleep(wait)

        logger.error(f"❌ Todos los intentos ({attempts}) agotados.")
        raise last_exc
