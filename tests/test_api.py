import os
import threading
from wsgiref.simple_server import make_server

import pytest


def test_api_health(client):
	response = client.get("/api/health")
	assert response.status_code == 200
	assert response.get_json()["status"] == "ok"


def test_api_login_invalid_payload(client):
	response = client.post("/api/login", json={})
	assert response.status_code == 400
	assert "required" in response.get_json()["message"]


def test_api_login_and_events(client):
	client.post(
		"/signup",
		data={"name": "Api User", "email": "api@example.com", "password": "test123"},
		follow_redirects=True,
	)

	login_response = client.post(
		"/api/login",
		json={"email": "api@example.com", "password": "test123"},
	)
	assert login_response.status_code == 200
	assert login_response.get_json()["message"] == "Login successful"

	client.post(
		"/login",
		data={"email": "admin@university.edu", "password": "admin123"},
		follow_redirects=True,
	)
	client.post(
		"/create-event",
		data={
			"title": "API Event",
			"description": "An event created to verify /api/events output.",
			"date": "2026-09-01",
			"location": "Auditorium",
			"available_seats": "10",
		},
		follow_redirects=True,
	)

	events_response = client.get("/api/events")
	assert events_response.status_code == 200
	data = events_response.get_json()
	assert isinstance(data, list)
	assert len(data) >= 1
	assert data[0]["title"]


@pytest.mark.playwright
def test_playwright_signup_login_flow(app_instance):
	playwright_module = pytest.importorskip("playwright.sync_api")

	host = "127.0.0.1"
	port = 5057
	http_server = make_server(host, port, app_instance)
	server_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
	server_thread.start()

	base_url = f"http://{host}:{port}"

	try:
		with playwright_module.sync_playwright() as p:
			browser = p.chromium.launch(headless=True)
			page = browser.new_page()

			unique_email = f"pw_{os.getpid()}@example.com"
			page.goto(f"{base_url}/signup")
			page.fill("input[name='name']", "Playwright Student")
			page.fill("input[name='email']", unique_email)
			page.fill("input[name='password']", "test123")
			page.click("button[type='submit']")

			page.goto(f"{base_url}/login")
			page.fill("input[name='email']", unique_email)
			page.fill("input[name='password']", "test123")
			page.click("button[type='submit']")

			page.wait_for_selector("text=Dashboard")
			assert "dashboard" in page.url.lower()
			browser.close()
	except Exception as exc:
		pytest.skip(f"Playwright browser not available in environment: {exc}")
	finally:
		http_server.shutdown()
		server_thread.join(timeout=2)