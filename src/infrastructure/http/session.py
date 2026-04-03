import requests
import logging

logger = logging.getLogger(__name__)

def create_session(proxy: str = None) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "X-Requested-With": "XMLHttpRequest",
        }
    )

    if proxy:
        session.proxies = {"http": proxy, "https": proxy}
        logger.info(f"Using proxy: {proxy}")

    return session
