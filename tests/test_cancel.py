def signup(client, email="student@example.com"):
	return client.post(
		"/signup",
		data={"name": "Student", "email": email, "password": "test123"},
		follow_redirects=True,
	)


def login(client, email="student@example.com", password="test123"):
	return client.post(
		"/login",
		data={"email": email, "password": password},
		follow_redirects=True,
	)


def create_event(client):
	client.post(
		"/login",
		data={"email": "admin@university.edu", "password": "admin123"},
		follow_redirects=True,
	)
	client.post(
		"/create-event",
		data={
			"title": "Quality Engineering Meetup",
			"description": "Talks on quality engineering practices and tools in industry.",
			"date": "2026-07-05",
			"location": "Block B",
			"available_seats": "5",
		},
		follow_redirects=True,
	)
	client.get("/logout", follow_redirects=True)
	conn = client.application.get_db_connection()
	row = conn.execute("SELECT id FROM events ORDER BY id DESC LIMIT 1").fetchone()
	event_id = row["id"] if row is not None else None
	conn.close()
	return event_id


def book_event(client, email):
	signup(client, email=email)
	login(client, email=email)
	# find latest event id and book it
	conn = client.application.get_db_connection()
	row = conn.execute("SELECT id FROM events ORDER BY id DESC LIMIT 1").fetchone()
	event_id = row["id"]
	conn.close()
	client.post(f"/book-event/{event_id}", follow_redirects=True)
	return event_id
	client.get("/logout", follow_redirects=True)


def test_cancel_booking_success(client, app_instance):
	event_id = create_event(client)
	book_event(client, "cancelme@example.com")
	login(client, email="cancelme@example.com")

	# lookup the booking id for this user and event
	conn = app_instance.get_db_connection()
	user = conn.execute("SELECT id FROM users WHERE email = ?", ("cancelme@example.com",)).fetchone()
	booking = conn.execute(
		"SELECT id FROM bookings WHERE user_id = ? AND event_id = ?",
		(user["id"], event_id),
	).fetchone()
	booking_id = booking["id"]
	conn.close()

	response = client.post(f"/cancel-booking/{booking_id}", follow_redirects=True)
	assert response.status_code == 200
	assert b"cancelled successfully" in response.data

	conn = app_instance.get_db_connection()
	seats = conn.execute("SELECT available_seats FROM events WHERE id = 1").fetchone()["available_seats"]
	bookings_count = conn.execute("SELECT COUNT(*) AS count FROM bookings").fetchone()["count"]
	conn.close()

	assert seats == 5
	assert bookings_count == 0


def test_user_cannot_cancel_other_user_booking(client):
	event_id = create_event(client)
	book_event(client, "owner@example.com")
	signup(client, email="intruder@example.com")
	login(client, email="intruder@example.com")

	# find the booking id for the owner and the event
	conn = client.application.get_db_connection()
	owner = conn.execute("SELECT id FROM users WHERE email = ?", ("owner@example.com",)).fetchone()
	booking = conn.execute(
		"SELECT id FROM bookings WHERE user_id = ? AND event_id = ?",
		(owner["id"], event_id),
	).fetchone()
	booking_id = booking["id"]
	conn.close()

	response = client.post(f"/cancel-booking/{booking_id}", follow_redirects=True)
	assert b"not allowed" in response.data
