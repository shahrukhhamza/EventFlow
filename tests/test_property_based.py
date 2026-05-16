import os
import string
import tempfile
from datetime import date, timedelta

from hypothesis import HealthCheck, given, settings, strategies as st

from app import create_app


EMAIL_ALPHABET = string.ascii_lowercase + string.digits + "._-"
TEXT_ALPHABET = string.ascii_letters + string.digits + " -_/."


def build_isolated_client():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE": db_path,
            "AUTO_SEED_DEMO": False,
        }
    )

    return app, app.test_client(), db_path


def cleanup_database(db_path):
    if os.path.exists(db_path):
        os.unlink(db_path)


def future_date(days_ahead):
    return (date.today() + timedelta(days=days_ahead)).isoformat()


def create_admin_event(client, title, seats, description="Hands-on automation workshop for QA students."):
    client.post(
        "/login",
        data={"email": "admin@eventflow.com", "password": "admin123"},
        follow_redirects=True,
    )
    client.post(
        "/create-event",
        data={
            "title": title,
            "description": description,
            "date": future_date(30),
            "location": "Innovation Hall",
            "available_seats": str(seats),
            "category": "Testing",
            "image_url": "",
        },
        follow_redirects=True,
    )
    client.get("/logout", follow_redirects=True)


def signup_user(client, email):
    client.post(
        "/signup",
        data={"name": "Property Student", "email": email, "password": "test123"},
        follow_redirects=True,
    )


def login_user(client, email):
    client.post(
        "/login",
        data={"email": email, "password": "test123"},
        follow_redirects=True,
    )


@given(
    email=st.text(alphabet=EMAIL_ALPHABET, min_size=1, max_size=20).filter(lambda value: "@" not in value),
    password=st.text(alphabet=TEXT_ALPHABET, min_size=1, max_size=20),
)
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_invalid_emails_never_authenticate(email, password):
    app, client, db_path = build_isolated_client()
    try:
        response = client.post(
            "/login",
            data={"email": email, "password": password},
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Invalid email or password" in response.data
    finally:
        cleanup_database(db_path)


@given(seat_count=st.integers(min_value=2, max_value=5))
@settings(max_examples=10, deadline=None)
def test_duplicate_booking_keeps_booking_count_stable(seat_count):
    app, client, db_path = build_isolated_client()
    try:
        create_admin_event(client, title="Booking Stability Workshop", seats=seat_count)

        unique_email = f"duplicate_{seat_count}@example.com"
        signup_user(client, unique_email)
        login_user(client, unique_email)

        first_response = client.post("/book-event/1", follow_redirects=True)
        second_response = client.post("/book-event/1", follow_redirects=True)

        conn = app.get_db_connection()
        bookings_count = conn.execute("SELECT COUNT(*) AS count FROM bookings").fetchone()["count"]
        seats_left = conn.execute("SELECT available_seats FROM events WHERE id = 1").fetchone()["available_seats"]
        conn.close()

        assert first_response.status_code == 200
        assert second_response.status_code == 200
        assert b"already booked" in second_response.data
        assert bookings_count == 1
        assert seats_left == seat_count - 1
    finally:
        cleanup_database(db_path)


@given(seat_count=st.integers(min_value=1, max_value=4))
@settings(max_examples=10, deadline=None)
def test_seat_limits_never_become_negative(seat_count):
    app, client, db_path = build_isolated_client()
    try:
        create_admin_event(client, title="Seat Limit Scenario", seats=seat_count)

        for index in range(seat_count + 2):
            unique_email = f"seatlimit_{seat_count}_{index}@example.com"
            signup_user(client, unique_email)
            login_user(client, unique_email)
            client.post("/book-event/1", follow_redirects=True)
            client.get("/logout", follow_redirects=True)

        conn = app.get_db_connection()
        seats_left = conn.execute("SELECT available_seats FROM events WHERE id = 1").fetchone()["available_seats"]
        bookings_count = conn.execute("SELECT COUNT(*) AS count FROM bookings").fetchone()["count"]
        conn.close()

        assert seats_left == 0
        assert bookings_count == seat_count
    finally:
        cleanup_database(db_path)


@given(seat_count=st.integers(min_value=1, max_value=5))
@settings(max_examples=10, deadline=None)
def test_cancellation_restores_seat_count(seat_count):
    app, client, db_path = build_isolated_client()
    try:
        create_admin_event(client, title="Cancellation Recovery Lab", seats=seat_count)

        unique_email = f"cancel_{seat_count}@example.com"
        signup_user(client, unique_email)
        login_user(client, unique_email)
        client.post("/book-event/1", follow_redirects=True)

        cancel_response = client.post("/cancel-booking/1", follow_redirects=True)

        conn = app.get_db_connection()
        seats_left = conn.execute("SELECT available_seats FROM events WHERE id = 1").fetchone()["available_seats"]
        bookings_count = conn.execute("SELECT COUNT(*) AS count FROM bookings").fetchone()["count"]
        conn.close()

        assert cancel_response.status_code == 200
        assert b"cancelled successfully" in cancel_response.data
        assert seats_left == seat_count
        assert bookings_count == 0
    finally:
        cleanup_database(db_path)


@given(
    title=st.text(alphabet=TEXT_ALPHABET, min_size=0, max_size=30),
    description=st.text(alphabet=TEXT_ALPHABET, min_size=0, max_size=80),
    location=st.text(alphabet=TEXT_ALPHABET, min_size=0, max_size=24),
)
@settings(max_examples=15, deadline=None)
def test_random_string_inputs_do_not_crash_system(title, description, location):
    app, client, db_path = build_isolated_client()
    try:
        client.post(
            "/login",
            data={"email": "admin@eventflow.com", "password": "admin123"},
            follow_redirects=True,
        )

        response = client.post(
            "/create-event",
            data={
                "title": title,
                "description": description,
                "date": future_date(40),
                "location": location,
                "available_seats": "10",
                "category": "Testing",
                "image_url": "",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert response.status_code != 500
    finally:
        cleanup_database(db_path)