# EventFlow
EventFlow — Intelligent Event Booking &amp; Automation Platform

## Project Overview

EventFlow is a Flask-based event booking platform built for an Automated Software Testing university project. The codebase demonstrates session authentication, role-based access control, event booking workflows, API endpoints, browser automation, and repeatable database-backed testing.

## Testing Strategy

The project emphasizes correctness verification, repeatability, and business-rule enforcement. The suite is organized to cover functional testing, negative testing, boundary testing, property-based testing, API testing, UI testing, and end-to-end testing.

## Test Types Used

- Pytest for functional and regression testing
- Hypothesis for property-based testing
- Playwright for browser automation
- API checks for JSON and HTTP status validation

## Automation Tools

- Flask test client for request-level integration tests
- SQLite test databases for isolated state
- Hypothesis strategies for generated inputs
- Playwright for real-browser workflow coverage

## Oracle Design

The project documents expected-value oracles, state-validation oracles, invariant oracles, and API schema checks in [docs/oracle_design.md](docs/oracle_design.md).

## Property-Based Testing

Hypothesis-based tests cover invalid emails, seat boundaries, duplicate bookings, cancellation recovery, and random string inputs. See [tests/test_property_based.py](tests/test_property_based.py) for the implementation.

## End-to-End Testing

Browser automation is organized in [tests/test_playwright.py](tests/test_playwright.py) and uses stable selectors plus explicit waits to reduce flakiness.

## Running Tests

```bash
pytest -q
playwright install
python app.py
```

## Test Adequacy

The project includes a short adequacy analysis in [docs/test_adequacy.md](docs/test_adequacy.md), including what is covered and what is intentionally out of scope.

## Flaky Test Handling

The main reliability practices are documented in [docs/flaky_tests.md](docs/flaky_tests.md).

## Demo Credentials

The app seeds realistic demo content on first launch so the UI is immediately usable for presentations and testing.

Admin:

`admin@eventflow.com`

Password:

`admin123`

Student:

`student@eventflow.com`

Password:

`student123`

Legacy classroom login:

`admin@university.edu`

Password:

`admin123`

The legacy admin email remains enabled so the automated test suite and older demo workflows keep working.
