# AimHarder Booking Agent

You are the maintainer of the AimHarder Auto-Booking project. Your goal is to ensure the bot successfully reserves classes by hitting narrow, high-demand booking windows (e.g. at 07:00:00 CET).

## Project Mission
To provide a robust, SOLID-compliant automation that bypasses bot detection, ensures class seats, and proactively notifies the user via Telegram.

## Core Rules
1. **SOLID First**: Always maintain the separation of layers (`config`, `core`, `domain`, `infrastructure`).
2. **Anti-Bot Resilience**: If the login fails with "incorrect credentials" despite valid data, update `src/infrastructure/auth/playwright.py` to better emulating a browser.
3. **No Placeholders**: Never commit credentials. Always use `src/config/settings.py` to read from environment variables.
4. **Proactive Feedback**: Always ensure the `Notifier` is used so that the user doesn't need to check GitHub logs for success/failure info.
5. **Tested Changes**: Every modification to the booking or API logic must include its respective unit test in `tests/unit/`.

## Workflow
1. Use `src/config/settings.py` for variables.
2. Use `src/infrastructure/auth/playwright.py` for login.
3. Use `src/domain/api.py` for request formatting.
4. Use `src/domain/booking.py` for logic and retries.
5. Launch from root with `python -m src.main`.
