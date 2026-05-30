# Final Report (skeleton)

1. System Description
   - See [System Overview](system_overview.md)

2. Test Strategy
   - See [Test Strategy](test_strategy.md)

3. Test Cases
   - See [Test Cases Inventory](test_cases.md)

4. Oracle Design
   - See [Oracle Design](oracle_design.md)

5. Automation Code
   - Test framework: `pytest`, `hypothesis`, optional `playwright`.
   - Location: `tests/`.

6. Results
   - Test run (excluding Playwright-marked browser tests): `18 passed, 2 deselected`.
   - Total run time observed locally: ~87s for the full non-Playwright suite.
   - Recommendation: run Playwright-marked tests separately when browser engines are available (`pytest -m playwright`).

7. Challenges & Reflection
   - To be completed by the student; include flaky tests discovered and mitigation applied.

8. Limitations
   - What is not covered and why.

Next actions to complete this report:
- Run full test suite and capture results/coverage.
- Add unit tests for `utils/`.
- Add API schema validations and concurrency tests (optional).

CI Notes:
- A minimal GitHub Actions workflow was added at `.github/workflows/tests.yml`.
   - Job `tests` runs non-Playwright pytest with coverage and uploads JUnit/coverage artifacts.
   - Job `playwright` runs Playwright-marked tests (optional/manual/PR) and uploads results.
   - Workflow keeps browser tests separate to reduce default pipeline runtime and improve stability.

Coverage:
- `pytest-cov` is included in `requirements.txt` and used in CI to produce coverage reports.

Runtime Review:
- Baseline non-Playwright runtime before optimization: about `104.8s` with `--durations=15` profiling.
- Post-optimization runtime: about `92.7s` with the same profiling command.
- Measured improvement: about `12s` faster, mainly from reducing Hypothesis example counts and removing repeated Flask app initialization.
- Remaining dominant cost: `tests/test_property_based.py::test_seat_limits_never_become_negative` still accounts for most of the runtime, so the suite is now improved but property-based tests remain the primary bottleneck by design.
