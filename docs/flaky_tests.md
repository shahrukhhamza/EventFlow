# Flaky Tests in EventFlow

Flaky tests are automated tests that sometimes pass and sometimes fail without a real code change. They are a testing problem because they reduce trust in the suite and make debugging harder.

## Common Causes

- Timing issues in browser automation
- Asynchronous rendering or delayed page transitions
- Unstable selectors that change when the UI changes
- Random data or shared state between tests

## Reliability Practices Used Here

- Playwright waits for navigation before checking the dashboard
- Browser tests use stable label and role selectors instead of fragile CSS paths
- Test inputs are controlled and repeatable
- Each test runs against an isolated SQLite database file
- Property-based tests use bounded strategies and disabled deadlines so they stay predictable in CI-like environments

## Practical Fixes in This Project

- Use `wait_for_url` after signup and login submissions
- Use `get_by_label` and `get_by_role` for form interaction
- Keep browser assertions focused on visible page state
- Reset application state between tests with a fresh database

## What to Watch For

- If browser tests become slow, reduce the number of examples or move heavier checks to unit/property tests.
- If UI text changes, update the accessible label or role selectors rather than using brittle selectors.
- If new randomness is introduced, seed it or constrain it so failures remain reproducible.
