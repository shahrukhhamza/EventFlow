# Test Adequacy Analysis

EventFlow is designed as a university software testing project, so adequacy is judged by workflow coverage, boundary checks, and test repeatability rather than by claiming exhaustive correctness.

## Functional Coverage

- Login and logout flows
- Role-based access control for admin and student behavior
- Event creation, editing, listing, booking, and cancellation
- API access for health and event listing
- Browser-based signup/login workflow with Playwright

## Logical Coverage

- Positive paths: valid login, successful booking, successful cancellation
- Negative paths: invalid credentials, duplicate booking, insufficient seats, unauthorized access
- Boundary paths: zero-seat handling, small seat counts, invalid form inputs
- Property-based paths: generated strings, random seat counts, repeated booking and cancelation rules

## Features Covered

- Flask routing and session management
- SQLite persistence and foreign-key relationships
- Validation logic for form input and booking constraints
- API response structure and status validation
- UI smoke testing via a real browser

## Edge Cases Covered

- Invalid email formats
- Duplicate event booking attempts
- Seat counts near zero
- Random string input to event creation
- Cancelation restoring state exactly once

## What Is Not Tested

- Load and stress testing
- Distributed deployment or multi-node behavior
- Cross-browser compatibility beyond the browser used in Playwright
- External payment, email, or notification integrations
- Accessibility auditing beyond the visible UI flow

## Limitations

- The suite does not prove the system is free of defects.
- Property-based tests sample representative inputs, but they do not exhaust every possible value.
- Browser automation depends on the local environment and installed browser binaries.

## Why the Suite Is Reasonably Sufficient

The test suite is adequate for a coursework project because it checks the core business rules from several angles: functionally, negatively, at boundaries, through generated inputs, at the API layer, and in the browser. It also uses isolated test databases and repeatable inputs, which makes the results stable enough for automated marking and demonstration.
