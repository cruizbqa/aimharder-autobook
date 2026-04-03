---
name: autobook
description: Automated class booking logic for AimHarder.
---

# AimHarder Booking Skill

This skill provides functionality to synchronize with the AimHarder platform, fetch classes, and automate the booking process using SOLID principles and a headless browser for authentication.

## Core Capabilities
- **Automated Login**: Uses Playwright to bypass anti-bot mechanisms and obtain the `amhrdrauth` cookie.
- **Schedule Management**: Fetches class agendas for specific boxes and dates.
- **Booking Orchestration**: Handles exponential backoff retries to hit narrow booking windows (e.g., 72h precisely).

## Repository Structure
- **config**: Settings and env validation.
- **core**: Custom exceptions (`AimHarderError`, `AuthError`, `BookingError`).
- **domain**: Business logic (`AimHarderAPI` and `BookingManager`).
- **infrastructure**: External integrations (`PlaywrightAuthenticator`, `session`).

## Usage Patterns
When making changes:
1. **Adding new endpoints**: Add methods to `src/domain/api.py`.
2. **Changing Auth logic**: Update `src/infrastructure/auth/playwright.py`.
3. **Updating Booking heuristics**: Modify `src/domain/booking.py`.

## Testing
Always run unit tests before committing changes to these layers:
```bash
python -m pytest tests/unit/
```
