# Oracle Design for EventFlow

This project uses multiple oracle types so automated tests can explain not only what failed, but why the observed result is correct or incorrect.

| Test Case | Oracle Type | Expected Behavior | Why It Is Correct |
| --- | --- | --- | --- |
| Successful login | Value oracle + state oracle | Valid credentials redirect to the dashboard and display dashboard content | The session is created only after password verification, so a dashboard redirect indicates authenticated state |
| Invalid login | Negative value oracle | Invalid credentials keep the user on the login flow with an error message | Authentication should fail when the email/password pair does not match a stored account |
| Booking an event | State oracle | Available seats decrease by 1 and a booking row is inserted | The booking workflow should reserve one seat and persist one booking record |
| Duplicate booking | Invariant oracle | A second booking request for the same user/event does not increase booking count | The system enforces a unique user-event booking rule, preventing duplicate reservations |
| Cancel booking | State oracle | Booking row is removed and available seats increase by 1 | Cancelation should restore the reserved seat back to the event inventory |
| Seat exhaustion | Boundary oracle | When seats reach zero, further booking attempts are rejected | Seat availability must never become negative, so the system must stop accepting bookings at zero |
| API health check | Response oracle | `/api/health` returns HTTP 200 with `{ "status": "ok" }` | A health endpoint should provide a stable machine-readable success response |
| API event list | Schema oracle | `/api/events` returns a JSON array of event objects | Clients and tests depend on a predictable schema for automated validation |
| Playwright signup/login flow | UI state oracle | Signup leads to login, login leads to dashboard visibility | The browser-visible page is the correct oracle for an end-to-end user workflow |

## Oracle Notes

- Expected-value oracles compare returned text, JSON fields, or HTTP codes.
- State-validation oracles inspect the SQLite database after workflow completion.
- Invariant oracles check properties that should always remain true, such as non-negative seat counts and no duplicate bookings.
- API oracles validate both response status and JSON shape so browser tests are not the only source of truth.
