#!/usr/bin/env python3
import logging
import os
import sys
from datetime import datetime, timedelta

# Project structure imports
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

from src.config.settings import AppConfig
from src.core.exceptions import AuthError, AimHarderError, BookingError
from src.infrastructure.http.session import create_session
from src.infrastructure.auth.playwright import PlaywrightAuthenticator
from src.infrastructure.notifications.telegram import TelegramNotifier
from src.domain.api import AimHarderAPI
from src.domain.booking import BookingManager

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("autobook")


def run(config: AppConfig) -> int:
    madrid_tz = ZoneInfo("Europe/Madrid")
    now = datetime.now(madrid_tz)
    
    # ── Lógica de Tiempo ─────────────────────────────────────────────
    # Si arrancamos poco antes de las 07:00, esperamos para el segundo exacto.
    # En cualquier otro horario, procedemos directamente (flexibilidad total).
    
    target_time = now.replace(hour=7, minute=0, second=1, microsecond=0)
    
    if now < target_time and now.hour == 6 and now.minute >= 40:
        wait_seconds = (target_time - now).total_seconds()
        logger.info(f"Arrancado temprano! [{now.strftime('%H:%M:%S')}] Esperando {wait_seconds:.1f}s hasta las 07:00:01")
        time.sleep(wait_seconds)
        now = datetime.now(madrid_tz)
    else:
        logger.info(f"Iniciando ejecución fuera de ventana crítica (Hora actual: {now.strftime('%H:%M:%S')})")

    target_date = now + timedelta(hours=config.target_hours)

    logger.info("═" * 55)
    logger.info(f"AimHarder Auto-Booking  —  {now.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("─" * 55)
    logger.info(f"Box          : {config.box_name}")
    logger.info(f"Clase        : {config.class_name}  a las  {config.class_time}")
    logger.info(f"Fecha clase  : {target_date.strftime('%Y-%m-%d %H:%M')}  ({target_date.strftime('%A')})")
    logger.info(f"Reintentos   : {config.retry_attempts} (backoff x{config.retry_backoff:.0f}, espera inicial {config.retry_delay:.0f}s)")
    logger.info("═" * 55)

    # Initialize Notification Service
    notifier = None
    if config.telegram_token and config.telegram_chat_id:
        notifier = TelegramNotifier(config.telegram_token, config.telegram_chat_id)

    # Dependency Injection
    session = create_session(proxy=config.proxy)
    auth = PlaywrightAuthenticator(
        email=config.email,
        password=config.password,
        box_name=config.box_name,
        base_url="https://login.aimharder.com"
    )

    try:
        # Authenticate
        auth.login(session)
        
        # Initialize API and Domain logic
        api = AimHarderAPI(session, box_name=config.box_name, box_id=config.box_id)
        manager = BookingManager(api, config)

        # Execute booking
        result = manager.book_with_retry(target_date)
        
        if result and notifier:
            # Formatear la hora de la clase (ej: "0800" -> "08:00")
            class_h = config.class_time[:2]
            class_m = config.class_time[2:]
            
            spot = result.get("spot")
            spot_msg = f"\n🔢 Plaza (Spot): {spot}" if spot else ""
            
            msg = (
                f"<b>✅ Reserva CONFIRMADA</b>\n"
                f"🏋️ Clase: {config.class_name}\n"
                f"📅 Fecha: {target_date.strftime('%d/%m/%Y')} a las {class_h}:{class_m}\n"
                f"📍 Centro: {config.box_name}{spot_msg}"
            )
            notifier.send_message(msg)
        elif not result and notifier:
            notifier.send_message(f"⚠️ El proceso terminó sin confirmar la reserva para {config.class_name}.")

        return 0 if result else 1

    except (AuthError, BookingError, AimHarderError) as exc:
        err_msg = f"❌ Error: {exc}"
        logger.error(err_msg)
        if notifier:
            notifier.send_message(err_msg)
        return 1
    except Exception as exc:
        err_msg = f"❌ Error inesperado: {exc}"
        logger.exception(err_msg)
        if notifier:
            notifier.send_message(err_msg)
        return 1
    finally:
        auth.logout(session)


if __name__ == "__main__":
    try:
        # Check if running from root or src
        if os.path.exists(".env"):
            from dotenv import load_dotenv
            load_dotenv()
        
        cfg = AppConfig.from_env()
        sys.exit(run(cfg))
    except Exception as e:
        logger.critical(f"Config load error: {e}")
        sys.exit(1)
