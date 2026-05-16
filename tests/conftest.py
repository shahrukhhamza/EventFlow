import os
import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app


@pytest.fixture()
def app_instance():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE": db_path,
        }
    )

    yield app

    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture()
def client(app_instance):
    return app_instance.test_client()


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


def login_admin(client):
    return client.post(
        "/login",
        data={"email": "admin@eventflow.com", "password": "admin123"},
        follow_redirects=True,
    )


def create_event(
    client,
    title="Automation Workshop",
    description="Hands-on pytest and Playwright session for QA students.",
    date="2026-06-20",
    location="Lab A",
    seats="5",
):
    return client.post(
        "/create-event",
        data={
            "title": title,
            "description": description,
            "date": date,
            "location": location,
            "available_seats": seats,
        },
        follow_redirects=True,
    )
