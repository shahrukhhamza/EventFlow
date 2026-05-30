# Test Cases Inventory

This file lists automated test cases present in the repository and notes gaps to fill for the assignment.

Existing tests (representative):
- `tests/test_login.py`
  - `test_signup_success` — normal signup
  - `test_signup_duplicate_email` — duplicate signup
  - `test_login_success` — normal login + dashboard
  - `test_login_invalid_credentials` — negative login
  - `test_signup_invalid_email_and_short_password` — input validation

- `tests/test_booking.py`
  - `test_book_event_success` — normal booking reduces seats
  - `test_cannot_book_same_event_twice` — duplicate booking
  - `test_cannot_book_when_no_seats` — boundary when full

- `tests/test_cancel.py`
  - `test_cancel_booking_success` — cancellation restores seats
  - `test_user_cannot_cancel_other_user_booking` — permission negative case

- `tests/test_api.py`
  - `test_api_health` — API health endpoint
  - `test_api_login_invalid_payload` — invalid API payload
  - `test_api_login_and_events` — API login + events listing

- `tests/test_playwright.py` and playwright-marked tests
  - UI signup/login end-to-end via Playwright (browser automation)

- `tests/test_property_based.py`
  - Property tests for invalid emails, booking duplicates, seat limits, cancellation recovery, random inputs not crashing

Gaps / Recommended additional cases:
- Unit tests for helper functions in `utils/` (pure logic) — increase unit-test coverage.
- API schema validation tests (JSON schema or strict field checks).
- More negative tests for event creation (invalid dates, missing fields).
- Tests simulating concurrent bookings (to expose race conditions) — can be added as integration tests or with threaded clients.
