import re
from functools import wraps

from flask import flash, redirect, session, url_for


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(email: str) -> bool:
    """Return True for well-formed email addresses."""
    return bool(email and EMAIL_REGEX.match(email))


def validate_password(password: str) -> bool:
    """Keep password rules simple for beginner-friendly coursework."""
    return len(password) >= 6


def login_required(view_func):
    """Redirect anonymous users to the login page."""

    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to continue.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped_view


def admin_required(view_func):
    """Restrict access to admin-only pages."""

    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to continue.", "warning")
            return redirect(url_for("login"))

        if session.get("role") != "admin":
            flash("Admin access is required for this action.", "danger")
            return redirect(url_for("dashboard"))

        return view_func(*args, **kwargs)

    return wrapped_view
