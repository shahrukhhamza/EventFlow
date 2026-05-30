from flask import session

from app import create_app
from utils.app import validate_email, validate_password, login_required, admin_required


def test_validate_email_good_and_bad():
    assert validate_email("user@example.com") is True
    assert validate_email("user.name+alias@sub.domain.co") is True
    assert validate_email("") is False
    assert validate_email("not-an-email") is False


def test_validate_password_length():
    assert validate_password("abcdef") is True
    assert validate_password("short") is False


def test_login_required_redirects_when_anonymous():
    app = create_app({"TESTING": True})

    @app.route("/protected")
    @login_required
    def protected():
        return "protected"

    client = app.test_client()
    resp = client.get("/protected", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Please login to continue" in resp.data


def test_admin_required_behaviour():
    app = create_app({"TESTING": True})

    @app.route("/admin-only")
    @admin_required
    def admin_only():
        return "admin"

    client = app.test_client()

    # Anonymous -> redirected to login
    resp = client.get("/admin-only", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Please login to continue" in resp.data

    # Logged in regular user -> redirected to dashboard with admin flash
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["role"] = "user"

    resp = client.get("/admin-only", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Admin access is required for this action" in resp.data

    # Logged in admin -> allowed
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["role"] = "admin"

    resp = client.get("/admin-only")
    assert resp.status_code == 200
    assert b"admin" in resp.data
