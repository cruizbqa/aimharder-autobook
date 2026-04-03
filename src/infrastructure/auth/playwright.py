import logging
import requests
from playwright.sync_api import sync_playwright
from .base import Authenticator
from src.core.exceptions import AuthError

logger = logging.getLogger(__name__)

class PlaywrightAuthenticator(Authenticator):
    def __init__(self, email: str, password: str, box_name: str, base_url: str):
        self.email = email
        self.password = password
        self.box_name = box_name
        self.base_url = base_url

    def login(self, session: requests.Session) -> bool:
        """Playwright-based login to bypass anti-bot mechanisms."""
        logger.info(f"Authenticating as {self.email} with Playwright...")

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1280, "height": 720}
                )
                page = context.new_page()

                # Navigate to login
                page.goto(f"{self.base_url}/login")

                # Fill form and submit
                page.fill("input[name='login'], input[type='email']", self.email)
                page.fill("input[name='psw'], input[type='password']", self.password)
                page.keyboard.press("Enter")

                # Wait for redirection (indicating login success)
                try:
                    page.wait_for_function("window.location.href.indexOf('login') === -1", timeout=15000)
                except Exception:
                    # Some navigations may not happen as expected but we should check cookies
                    pass

                # Get cookies
                cookies = context.cookies()
                auth_cookie = next((c["value"] for c in cookies if c["name"] == "amhrdrauth"), None)

                if not auth_cookie:
                    raise AuthError("Auth cookie not found after login. Check credentials.")

                # Populate session cookies
                # Setting for both .aimharder.com and [box].aimharder.com to be sure
                session.cookies.set("amhrdrauth", auth_cookie, domain=".aimharder.com")
                session.cookies.set("amhrdrauth", auth_cookie, domain=f"{self.box_name}.aimharder.com")

                browser.close()
                logger.info("Playwright login successful.")
                return True
        except Exception as e:
            if isinstance(e, AuthError):
                raise e
            raise AuthError(f"Login failed via Playwright: {str(e)}")

    def logout(self, session: requests.Session) -> None:
        """Simply clear cookies (and ideally call logout API)."""
        session.cookies.clear()
        try:
            session.get(f"{self.base_url}/Util/logout.php", timeout=10)
        except:
            pass
        logger.info("Logged out.")
