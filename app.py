import os
import sqlite3
from datetime import datetime

from flask import Flask, flash, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from utils.app import admin_required, login_required, validate_email, validate_password


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY="event-booking-secret-key",
        DATABASE=os.path.join(app.root_path, "database.db"),
    )

    if test_config:
        app.config.update(test_config)

    def get_db_connection():
        conn = sqlite3.connect(app.config["DATABASE"])
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db():
        conn = get_db_connection()
        cursor = conn.cursor()

        # If an old schema exists from earlier project iterations, reset to current schema.
        users_table_exists = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        ).fetchone()
        if users_table_exists:
            user_columns = {
                row["name"] for row in cursor.execute("PRAGMA table_info(users)").fetchall()
            }
            if "password_hash" not in user_columns:
                cursor.execute("DROP TABLE IF EXISTS bookings")
                cursor.execute("DROP TABLE IF EXISTS events")
                cursor.execute("DROP TABLE IF EXISTS users")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                date TEXT NOT NULL,
                location TEXT NOT NULL,
                available_seats INTEGER NOT NULL CHECK (available_seats >= 0),
                created_by INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_id INTEGER NOT NULL,
                booking_status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
                UNIQUE(user_id, event_id)
            )
            """
        )

        # Default admin account for classroom demo usage.
        cursor.execute("SELECT id FROM users WHERE email = ?", ("admin@university.edu",))
        if cursor.fetchone() is None:
            cursor.execute(
                """
                INSERT INTO users (name, email, password_hash, role, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "System Admin",
                    "admin@university.edu",
                    generate_password_hash("admin123"),
                    "admin",
                    datetime.utcnow().isoformat(),
                ),
            )

        conn.commit()
        conn.close()

    @app.before_request
    def load_logged_in_user():
        user_id = session.get("user_id")
        g.user = None

        if user_id is not None:
            conn = get_db_connection()
            g.user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            conn.close()

    @app.context_processor
    def inject_session_context():
        return {
            "current_user": g.user,
            "is_logged_in": g.user is not None,
            "is_admin": g.user is not None and g.user["role"] == "admin",
        }

    @app.route("/")
    def index():
        conn = get_db_connection()
        featured_events = conn.execute(
            """
            SELECT id, title, description, date, location, available_seats
            FROM events
            ORDER BY date ASC
            LIMIT 3
            """
        ).fetchall()
        conn.close()
        return render_template("index.html", featured_events=featured_events)

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            if len(name) < 2:
                flash("Name must contain at least 2 characters.", "danger")
                return render_template("signup.html")

            if not validate_email(email):
                flash("Please enter a valid email address.", "danger")
                return render_template("signup.html")

            if not validate_password(password):
                flash("Password must be at least 6 characters long.", "danger")
                return render_template("signup.html")

            conn = get_db_connection()
            existing_user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if existing_user is not None:
                conn.close()
                flash("An account with this email already exists.", "warning")
                return render_template("signup.html")

            conn.execute(
                """
                INSERT INTO users (name, email, password_hash, role, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, email, generate_password_hash(password), "user", datetime.utcnow().isoformat()),
            )
            conn.commit()
            conn.close()

            flash("Signup successful. Please login.", "success")
            return redirect(url_for("login"))

        return render_template("signup.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            conn = get_db_connection()
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            conn.close()

            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session["user_id"] = user["id"]
                session["role"] = user["role"]
                session["name"] = user["name"]
                flash("Login successful.", "success")
                return redirect(url_for("dashboard"))

            flash("Invalid email or password.", "danger")

        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("index"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        conn = get_db_connection()

        total_events = conn.execute("SELECT COUNT(*) AS count FROM events").fetchone()["count"]
        my_bookings_count = conn.execute(
            "SELECT COUNT(*) AS count FROM bookings WHERE user_id = ?", (session["user_id"],)
        ).fetchone()["count"]
        available_events = conn.execute(
            "SELECT COUNT(*) AS count FROM events WHERE available_seats > 0"
        ).fetchone()["count"]

        conn.close()
        return render_template(
            "dashboard.html",
            total_events=total_events,
            my_bookings_count=my_bookings_count,
            available_events=available_events,
        )

    @app.route("/events")
    def events():
        conn = get_db_connection()
        events_data = conn.execute(
            """
            SELECT e.id, e.title, e.description, e.date, e.location, e.available_seats, u.name AS created_by_name
            FROM events e
            JOIN users u ON u.id = e.created_by
            ORDER BY e.date ASC
            """
        ).fetchall()
        conn.close()
        return render_template("events.html", events=events_data)

    @app.route("/events/create", methods=["GET", "POST"])
    @app.route("/create-event", methods=["GET", "POST"])
    @admin_required
    def create_event():
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            date = request.form.get("date", "").strip()
            location = request.form.get("location", "").strip()
            seats = request.form.get("available_seats", "").strip()

            if len(title) < 3 or len(description) < 10 or len(location) < 2:
                flash("Please provide valid title, description and location.", "danger")
                return render_template("create_event.html", event=None)

            if not seats.isdigit() or int(seats) <= 0:
                flash("Available seats must be a positive number.", "danger")
                return render_template("create_event.html", event=None)

            conn = get_db_connection()
            conn.execute(
                """
                INSERT INTO events (title, description, date, location, available_seats, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    title,
                    description,
                    date,
                    location,
                    int(seats),
                    session["user_id"],
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()
            conn.close()
            flash("Event created successfully.", "success")
            return redirect(url_for("events"))

        return render_template("create_event.html", event=None)

    @app.route("/events/edit/<int:event_id>", methods=["GET", "POST"])
    @admin_required
    def edit_event(event_id):
        conn = get_db_connection()
        event = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()

        if event is None:
            conn.close()
            flash("Event not found.", "warning")
            return redirect(url_for("events"))

        if request.method == "POST":
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            date = request.form.get("date", "").strip()
            location = request.form.get("location", "").strip()
            seats = request.form.get("available_seats", "").strip()

            if len(title) < 3 or len(description) < 10 or len(location) < 2:
                conn.close()
                flash("Please provide valid title, description and location.", "danger")
                return render_template("create_event.html", event=event)

            if not seats.isdigit() or int(seats) < 0:
                conn.close()
                flash("Available seats must be zero or greater.", "danger")
                return render_template("create_event.html", event=event)

            conn.execute(
                """
                UPDATE events
                SET title = ?, description = ?, date = ?, location = ?, available_seats = ?
                WHERE id = ?
                """,
                (title, description, date, location, int(seats), event_id),
            )
            conn.commit()
            conn.close()
            flash("Event updated successfully.", "success")
            return redirect(url_for("events"))

        conn.close()
        return render_template("create_event.html", event=event)

    @app.route("/events/delete/<int:event_id>", methods=["POST"])
    @admin_required
    def delete_event(event_id):
        conn = get_db_connection()
        event = conn.execute("SELECT id FROM events WHERE id = ?", (event_id,)).fetchone()
        if event is None:
            conn.close()
            flash("Event not found.", "warning")
            return redirect(url_for("events"))

        conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()
        conn.close()
        flash("Event deleted successfully.", "success")
        return redirect(url_for("events"))

    @app.route("/events/book/<int:event_id>", methods=["POST", "GET"])
    @app.route("/book-event/<int:event_id>", methods=["POST", "GET"])
    @login_required
    def book_event(event_id):
        if session.get("role") == "admin":
            flash("Admin accounts cannot book events.", "warning")
            return redirect(url_for("events"))

        conn = get_db_connection()
        event = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()

        if event is None:
            conn.close()
            flash("Event not found.", "warning")
            return redirect(url_for("events"))

        if event["available_seats"] <= 0:
            conn.close()
            flash("No seats available for this event.", "danger")
            return redirect(url_for("events"))

        existing_booking = conn.execute(
            "SELECT id FROM bookings WHERE user_id = ? AND event_id = ?",
            (session["user_id"], event_id),
        ).fetchone()

        if existing_booking is not None:
            conn.close()
            flash("You have already booked this event.", "warning")
            return redirect(url_for("my_bookings"))

        conn.execute(
            """
            INSERT INTO bookings (user_id, event_id, booking_status, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (session["user_id"], event_id, "booked", datetime.utcnow().isoformat()),
        )
        conn.execute(
            "UPDATE events SET available_seats = available_seats - 1 WHERE id = ?",
            (event_id,),
        )
        conn.commit()
        conn.close()

        flash("Event booked successfully.", "success")
        return redirect(url_for("my_bookings"))

    @app.route("/bookings")
    @app.route("/my-bookings")
    @login_required
    def my_bookings():
        conn = get_db_connection()
        bookings_data = conn.execute(
            """
            SELECT b.id AS booking_id, b.booking_status, b.created_at,
                   e.id AS event_id, e.title, e.date, e.location
            FROM bookings b
            JOIN events e ON e.id = b.event_id
            WHERE b.user_id = ?
            ORDER BY e.date ASC
            """,
            (session["user_id"],),
        ).fetchall()
        conn.close()
        return render_template("bookings.html", bookings=bookings_data, admin_view=False)

    @app.route("/bookings/cancel/<int:booking_id>", methods=["POST", "GET"])
    @app.route("/cancel-booking/<int:booking_id>", methods=["POST", "GET"])
    @login_required
    def cancel_booking(booking_id):
        conn = get_db_connection()
        booking = conn.execute(
            "SELECT * FROM bookings WHERE id = ?",
            (booking_id,),
        ).fetchone()

        if booking is None:
            conn.close()
            flash("Booking not found.", "warning")
            return redirect(url_for("my_bookings"))

        if session.get("role") != "admin" and booking["user_id"] != session["user_id"]:
            conn.close()
            flash("You are not allowed to cancel this booking.", "danger")
            return redirect(url_for("my_bookings"))

        conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        conn.execute(
            "UPDATE events SET available_seats = available_seats + 1 WHERE id = ?",
            (booking["event_id"],),
        )
        conn.commit()
        conn.close()

        flash("Booking cancelled successfully.", "success")
        if session.get("role") == "admin":
            return redirect(url_for("admin_bookings"))
        return redirect(url_for("my_bookings"))

    @app.route("/admin/bookings")
    @admin_required
    def admin_bookings():
        conn = get_db_connection()
        all_bookings = conn.execute(
            """
            SELECT b.id AS booking_id, b.booking_status, b.created_at,
                   u.name AS student_name, u.email,
                   e.title, e.date, e.location
            FROM bookings b
            JOIN users u ON u.id = b.user_id
            JOIN events e ON e.id = b.event_id
            ORDER BY b.created_at DESC
            """
        ).fetchall()
        conn.close()
        return render_template("bookings.html", bookings=all_bookings, admin_view=True)

    @app.route("/api/events")
    def api_events():
        conn = get_db_connection()
        events_data = conn.execute(
            "SELECT id, title, description, date, location, available_seats FROM events ORDER BY date ASC"
        ).fetchall()
        conn.close()
        return jsonify([dict(event) for event in events_data]), 200

    @app.route("/api/login", methods=["POST"])
    def api_login():
        data = request.get_json(silent=True) or {}
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))

        if not email or not password:
            return jsonify({"message": "Email and password are required."}), 400

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            return jsonify({"message": "Login successful", "role": user["role"]}), 200

        return jsonify({"message": "Invalid credentials"}), 401

    @app.route("/api/health")
    def api_health():
        return jsonify({"status": "ok"}), 200

    app.get_db_connection = get_db_connection
    app.init_db = init_db

    with app.app_context():
        init_db()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)