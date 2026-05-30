# System Overview

Project: Event Booking System (Flask)

Summary:
- A small web application to create events, sign up/login users, book and cancel seats.
- Exposes HTML UI routes and a small JSON API under `/api/*`.

Key Features:
- User signup and login (session-based)
- Admin event creation
- Event listing and details
- Booking and cancellation flows with seat counters
- `/api/health`, `/api/login`, `/api/events` endpoints

Assumptions:
- Admin account exists with email `admin@eventflow.com` / `admin123`.
- App uses an SQLite file database (configurable via `DATABASE`).
- UI uses standard HTML forms suitable for Playwright tests.

Reference files:
- Application entry: [app.py](app.py)
- Utilities: [utils/app.py](utils/app.py)
- Tests: [tests/](tests/)
