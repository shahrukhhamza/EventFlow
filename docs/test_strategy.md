# Test Strategy

Scope:
- Unit tests: core business logic where practical (database-backed flows exercised through Flask test client).
- API tests: `tests/test_api.py` covers `/api/health`, `/api/login`, `/api/events`.
- UI tests: Playwright-based functional flows in `tests/test_playwright.py` and inlined playwright tests in `tests/test_api.py`.
- End-to-end: Combined flows exercised via the Flask test client and Playwright where available.
- Property-based: Hypothesis tests in `tests/test_property_based.py`.

Test Types Included:
- Functional tests: signup/login, event creation, booking, cancellation.
- Boundary tests: seat limits, duplicate booking, negative seats (Hypothesis asserts non-negative invariants).
- Negative tests: invalid login, invalid signup inputs.
- Property-based tests: randomized inputs to ensure robustness.

Tools:
- pytest + pytest fixtures
- Playwright for UI flows (optional, marked with `@pytest.mark.playwright`)
- Hypothesis for property-based testing

Execution:
- Run unit/api/property tests with `pytest -q`.
- Run playwright-marked tests when Playwright is installed and browser runners available: `pytest -q -m playwright`.
