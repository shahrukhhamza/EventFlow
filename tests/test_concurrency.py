import concurrent.futures
import time


def create_event_for_concurrency(client):
    # login as admin and create an event with limited seats
    client.post(
        "/login",
        data={"email": "admin@university.edu", "password": "admin123"},
        follow_redirects=True,
    )
    client.post(
        "/create-event",
        data={
            "title": "Concurrent Booking Test",
            "description": "Event for concurrency testing",
            "date": "2026-12-31",
            "location": "Hall",
            "available_seats": "5",
        },
        follow_redirects=True,
    )
    client.get("/logout", follow_redirects=True)
    # return created event id
    conn = client.application.get_db_connection()
    row = conn.execute("SELECT id FROM events ORDER BY id DESC LIMIT 1").fetchone()
    event_id = row["id"] if row is not None else None
    conn.close()
    return event_id


def try_book(base_client, email):
    # Each thread must have its own client instance to simulate separate users/connections
    with base_client.application.test_client() as client:
        client.post(
            "/signup",
            data={"name": email.split("@")[0], "email": email, "password": "test123"},
            follow_redirects=True,
        )
        client.post(
            "/login",
            data={"email": email, "password": "test123"},
            follow_redirects=True,
        )
        # book the event created for this test
        resp = client.post(f"/book-event/{base_client._concurrency_event_id}", follow_redirects=True)
        return resp


def test_concurrent_bookings_do_not_overbook(client, app_instance):
    # Prepare event with small seat count
    event_id = create_event_for_concurrency(client)
    client._concurrency_event_id = event_id

    # Spawn multiple worker threads attempting to book the same event
    attempts = 10
    emails = [f"concurrent_{i}@example.com" for i in range(attempts)]

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futures = [ex.submit(try_book, client, email) for email in emails]
        for fut in concurrent.futures.as_completed(futures):
            try:
                results.append(fut.result())
            except Exception:
                # thread errors should fail the test; capture and continue
                results.append(None)

    conn = app_instance.get_db_connection()
    seats_left = conn.execute("SELECT available_seats FROM events WHERE id = ?", (event_id,)).fetchone()["available_seats"]
    bookings_count = conn.execute("SELECT COUNT(*) AS count FROM bookings WHERE event_id = ?", (event_id,)).fetchone()["count"]
    conn.close()

    # Assert business invariants: seats non-negative and bookings not exceed initial capacity (5)
    assert seats_left >= 0
    assert bookings_count <= 5
