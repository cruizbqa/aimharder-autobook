#!/usr/bin/env python3
"""
src/main.py  —  AimHarder auto-booking entry-point
───────────────────────────────────────────────────
Variables de entorno (inyectadas desde GitHub Secrets/vars):

  EMAIL                  Cuenta AimHarder
  PASSWORD               Contraseña
  BOX_NAME               Subdominio del box  (ej: "[BOX_NAME]")
  BOX_ID                 ID numérico del box
  CLASS_TIME             Hora clase en HHMM  (ej: "0700")
  CLASS_NAME             Fragmento del nombre (ej: "WOD")
  TARGET_HOURS           Horas hacia adelante para la fecha objetivo (default 72)
  RETRY_ATTEMPTS         Nº máximo de intentos  (default 5)
  RETRY_DELAY_SECONDS    Espera inicial entre intentos en segundos (default 10)
  RETRY_BACKOFF          Multiplicador exponencial (default 2)
                         intento 1→10s, 2→20s, 3→40s, 4→80s …
  FAMILY_ID              (Opcional) ID familiar
  PROXY                  (Opcional) socks5://[IP_ADDRESS]
"""

import logging
import os
import sys
import time
from datetime import datetime, timedelta

from aimharder_client import AimHarderClient, AimHarderError, BookingError

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("autobook")


# ── Helpers ──────────────────────────────────────────────────────────

def _require_env(key: str) -> str:
    value = os.environ.get(key, "").strip()
    if not value:
        logger.critical("Variable de entorno requerida '%s' no configurada.", key)
        sys.exit(1)
    return value


def load_config() -> dict:
    return {
        "email":         _require_env("EMAIL"),
        "password":      _require_env("PASSWORD"),
        "box_name":      os.environ.get("BOX_NAME").strip(),
        "box_id":        int(os.environ["BOX_ID"]) if os.environ.get("BOX_ID", "").strip() else None,
        "family_id":     os.environ.get("FAMILY_ID", "").strip() or None,
        "proxy":         os.environ.get("PROXY", "").strip() or None,
        "class_time":    _require_env("CLASS_TIME"),
        "class_name":    _require_env("CLASS_NAME"),
        "target_hours":  int(os.environ.get("TARGET_HOURS", "72")),
        "retry_attempts":      int(os.environ.get("RETRY_ATTEMPTS", "5")),
        "retry_delay":         float(os.environ.get("RETRY_DELAY_SECONDS", "10")),
        "retry_backoff":       float(os.environ.get("RETRY_BACKOFF", "2")),
    }


# ── Booking con retry + backoff exponencial ───────────────────────────

def book_with_retry(client: AimHarderClient, config: dict, target_date: datetime) -> bool:
    """
    Intenta reservar la clase hasta RETRY_ATTEMPTS veces.
    Entre cada intento fallido espera delay * backoff^intento segundos.
    Retorna True si la reserva se completó, False si agotó los intentos.
    """
    attempts      = config["retry_attempts"]
    delay         = config["retry_delay"]
    backoff       = config["retry_backoff"]
    class_name    = config["class_name"]
    class_time    = config["class_time"]

    for attempt in range(1, attempts + 1):
        logger.info(
            "━━ Intento %d/%d  [%s]",
            attempt, attempts, datetime.now().strftime("%H:%M:%S"),
        )
        try:
            result = client.find_and_book(
                class_name_fragment=class_name,
                class_time=class_time,
                target_date=target_date,
                # Desactivamos el retry interno del cliente;
                # el backoff exponencial lo gestiona este bucle.
                retry_attempts=1,
            )
            logger.info("✅ Reserva completada en el intento %d. Respuesta: %s", attempt, result)
            return True

        except BookingError as exc:
            logger.warning("⚠️  Intento %d fallido: %s", attempt, exc)

        except AimHarderError as exc:
            logger.warning("⚠️  Error de API en intento %d: %s", attempt, exc)

        if attempt < attempts:
            wait = delay * (backoff ** (attempt - 1))
            logger.info("   Esperando %.0f s antes del siguiente intento…", wait)
            time.sleep(wait)

    logger.error(
        "❌ Todos los intentos (%d) agotados. Clase '%s' a las %s no reservada.",
        attempts, class_name, class_time,
    )
    return False


# ── Entry point ───────────────────────────────────────────────────────

def run(config: dict) -> int:
    now = datetime.now()
    target_date = now + timedelta(hours=config["target_hours"])

    logger.info("═" * 55)
    logger.info("AimHarder Auto-Booking  —  %s", now.strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("─" * 55)
    logger.info("Box          : %s", config["box_name"])
    logger.info("Clase        : %s  a las  %s", config["class_name"], config["class_time"])
    logger.info("Fecha clase  : %s  (%s)",
                target_date.strftime("%Y-%m-%d %H:%M"),
                target_date.strftime("%A"))
    logger.info("Reintentos   : %d  (backoff x%.0f, espera inicial %.0fs)",
                config["retry_attempts"], config["retry_backoff"], config["retry_delay"])
    logger.info("═" * 55)

    client = AimHarderClient(
        email=config["email"],
        password=config["password"],
        box_name=config["box_name"],
        box_id=config["box_id"],
        family_id=config["family_id"],
        proxy=config["proxy"],
    )

    try:
        client.login()
    except AimHarderError as exc:
        logger.error("❌ Autenticación fallida: %s", exc)
        return 1

    try:
        success = book_with_retry(client, config, target_date)
        return 0 if success else 1
    finally:
        client.logout()


if __name__ == "__main__":
    cfg = load_config()
    sys.exit(run(cfg))
