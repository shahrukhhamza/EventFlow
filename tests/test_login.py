def signup(client, name="Test User", email="test@example.com", password="test123"):
	return client.post(
		"/signup",
		data={"name": name, "email": email, "password": password},
		follow_redirects=True,
	)


def login(client, email="test@example.com", password="test123"):
	return client.post(
		"/login",
		data={"email": email, "password": password},
		follow_redirects=True,
	)


def test_signup_success(client):
	response = signup(client)
	assert response.status_code == 200
	assert b"Signup successful" in response.data


def test_signup_duplicate_email(client):
	signup(client)
	response = signup(client)
	assert response.status_code == 200
	assert b"already exists" in response.data


def test_login_success(client):
	signup(client)
	response = login(client)
	assert response.status_code == 200
	assert b"Login successful" in response.data
	assert b"Dashboard" in response.data


def test_login_invalid_credentials(client):
	signup(client)
	response = client.post(
		"/login",
		data={"email": "test@example.com", "password": "wrongpass"},
		follow_redirects=True,
	)
	assert response.status_code == 200
	assert b"Invalid email or password" in response.data


def test_signup_invalid_email_and_short_password(client):
	response = client.post(
		"/signup",
		data={"name": "A", "email": "invalid", "password": "123"},
		follow_redirects=True,
	)
	assert response.status_code == 200
	assert b"at least 2 characters" in response.data
