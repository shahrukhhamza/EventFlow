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


def create_demo_event(client, title="Testing Bootcamp", seats="2"):
	client.post(
		"/login",
		data={"email": "admin@university.edu", "password": "admin123"},
		follow_redirects=True,
	)
	client.post(
		"/create-event",
		data={
			"title": title,
			"description": "Practical session on automated testing with Flask and Playwright.",
			"date": "2026-06-10",
			"location": "Seminar Hall",
			"available_seats": seats,
		},
		follow_redirects=True,
	)
	client.get("/logout", follow_redirects=True)


def test_book_event_success(client, app_instance):
	create_demo_event(client)
	signup(client)
	login(client)

	response = client.post("/book-event/1", follow_redirects=True)
	assert response.status_code == 200
	assert b"booked successfully" in response.data

	conn = app_instance.get_db_connection()
	seats = conn.execute("SELECT available_seats FROM events WHERE id = 1").fetchone()["available_seats"]
	conn.close()
	assert seats == 1


def test_cannot_book_same_event_twice(client):
	create_demo_event(client)
	signup(client)
	login(client)

	client.post("/book-event/1", follow_redirects=True)
	response = client.post("/book-event/1", follow_redirects=True)
	assert b"already booked" in response.data


def test_cannot_book_when_no_seats(client):
	create_demo_event(client, seats="1")

	signup(client, email="first@example.com")
	login(client, email="first@example.com")
	client.post("/book-event/1", follow_redirects=True)
	client.get("/logout", follow_redirects=True)

	signup(client, email="second@example.com")
	login(client, email="second@example.com")
	response = client.post("/book-event/1", follow_redirects=True)

	assert b"No seats available" in response.data
