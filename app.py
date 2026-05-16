import os
import sqlite3
from datetime import datetime, timezone

from flask import Flask, flash, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from utils.app import admin_required, login_required, validate_email, validate_password


DEMO_ADMIN_EMAIL = "admin@eventflow.com"
LEGACY_ADMIN_EMAIL = "admin@university.edu"
ADMIN_LOGIN_ALIASES = {
    LEGACY_ADMIN_EMAIL: DEMO_ADMIN_EMAIL,
}

DEMO_STUDENTS = [
    {
        "name": "Maya Patel",
        "email": "student@eventflow.com",
        "password": "student123",
    },
    {
        "name": "Jordan Lee",
        "email": "jordan.lee@eventflow.com",
        "password": "student123",
    },
    {
        "name": "Aisha Khan",
        "email": "aisha.khan@eventflow.com",
        "password": "student123",
    },
]

DEMO_EVENTS = [
    {
        "title": "AI & Machine Learning Summit 2026",
        "description": "A student-friendly summit covering responsible AI, model deployment, and practical machine learning workflows.",
        "date": "2026-08-14",
        "location": "Innovation Hall, Campus Center",
        "available_seats": 120,
        "category": "AI & Data Science",
        "image_url": "https://images.unsplash.com/photo-1553877522-43269d4ea984?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "title": "Startup Networking Expo",
        "description": "Connect with founders, recruiters, and incubators in a fast-paced networking showcase for ambitious students.",
        "date": "2026-08-29",
        "location": "Business School Atrium",
        "available_seats": 90,
        "category": "Entrepreneurship",
        "image_url": "https://images.unsplash.com/photo-1515169067868-5387ec356754?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "title": "Cybersecurity Workshop",
        "description": "Hands-on security lab focused on threat detection, secure coding, and incident response basics.",
        "date": "2026-09-06",
        "location": "Computer Lab 2",
        "available_seats": 40,
        "category": "Cybersecurity",
        "image_url": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "title": "Python Automation Bootcamp",
        "description": "Build reliable automation scripts for testing, reporting, file handling, and routine academic workflows.",
        "date": "2026-09-18",
        "location": "Software Lab 4",
        "available_seats": 60,
        "category": "Programming",
        "image_url": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "title": "Cloud Computing Seminar",
        "description": "Explore cloud-native architecture, deployment pipelines, and scalable infrastructure for modern applications.",
        "date": "2026-10-02",
        "location": "Lecture Theatre A",
        "available_seats": 150,
        "category": "Cloud & DevOps",
        "image_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "title": "Music & Cultural Festival",
        "description": "An evening of performances, food stalls, and student-led cultural exhibits celebrating campus diversity.",
        "date": "2026-10-16",
        "location": "Open Air Grounds",
        "available_seats": 300,
        "category": "Campus Life",
        "image_url": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "title": "Career Fair 2026",
        "description": "Meet hiring teams, explore internships, and practice interview conversations with industry professionals.",
        "date": "2026-10-24",
        "location": "Student Union Hall",
        "available_seats": 220,
        "category": "Career Development",
        "image_url": "https://images.unsplash.com/photo-1521737604893-d14cc237f11d?auto=format&fit=crop&w=1200&q=80",
    },
    {
        "title": "Web Engineering Conference",
        "description": "A technical conference focused on modern front-end systems, accessibility, APIs, and scalable delivery workflows.",
        "date": "2026-11-08",
        "location": "Digital Innovation Center",
        "available_seats": 110,
        "category": "Web Development",
        "image_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=80",
    },
]


def utc_now():
    return datetime.now(timezone.utc)


def utc_now_iso():
    return utc_now().isoformat()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY="event-booking-secret-key",
        DATABASE=os.path.join(app.root_path, "database.db"),
    )

    if test_config:
        app.config.update(test_config)

    if "AUTO_SEED_DEMO" not in app.config:
        app.config["AUTO_SEED_DEMO"] = not app.config.get("TESTING", False)

    def get_db_connection():
        conn = sqlite3.connect(app.config["DATABASE"])
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def normalize_login_email(email):
        return ADMIN_LOGIN_ALIASES.get(email, email)

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

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS app_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

        def add_column_if_missing(table_name, column_name, column_definition):
            existing_columns = {
                row["name"] for row in cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
            }
            if column_name not in existing_columns:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_definition}")

        add_column_if_missing("events", "category", "category TEXT NOT NULL DEFAULT 'General'")
        add_column_if_missing("events", "image_url", "image_url TEXT")
        add_column_if_missing("events", "seat_capacity", "seat_capacity INTEGER NOT NULL DEFAULT 0")
        cursor.execute(
            """
            UPDATE events
            SET seat_capacity = CASE
                WHEN seat_capacity IS NULL OR seat_capacity = 0 THEN available_seats
                ELSE seat_capacity
            END
            """
        )

        def ensure_user(name, email, password, role):
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone() is None:
                cursor.execute(
                    """
                    INSERT INTO users (name, email, password_hash, role, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (name, email, generate_password_hash(password), role, utc_now_iso()),
                )

        ensure_user("EventFlow Admin", DEMO_ADMIN_EMAIL, "admin123", "admin")

        if app.config.get("AUTO_SEED_DEMO", True):
            seeded = cursor.execute(
                "SELECT value FROM app_meta WHERE key = ?",
                ("demo_seeded",),
            ).fetchone()

            if seeded is None:
                for student in DEMO_STUDENTS:
                    ensure_user(student["name"], student["email"], student["password"], "user")

                admin_user = cursor.execute(
                    "SELECT id FROM users WHERE email = ?",
                    (DEMO_ADMIN_EMAIL,),
                ).fetchone()

                if admin_user is not None:
                    for event in DEMO_EVENTS:
                        cursor.execute(
                            """
                            INSERT INTO events (
                                title, description, date, location, available_seats, created_by, created_at,
                                category, image_url, seat_capacity
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                event["title"],
                                event["description"],
                                event["date"],
                                event["location"],
                                event["available_seats"],
                                admin_user["id"],
                                utc_now_iso(),
                                event["category"],
                                event["image_url"],
                                event["available_seats"],
                            ),
                        )

                cursor.execute(
                    "INSERT OR REPLACE INTO app_meta (key, value) VALUES (?, ?)",
                    ("demo_seeded", "1"),
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
            SELECT id, title, description, date, location, available_seats, category, image_url, seat_capacity
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
                (name, email, generate_password_hash(password), "user", utc_now_iso()),
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
            lookup_email = normalize_login_email(email)

            conn = get_db_connection()
            user = conn.execute("SELECT * FROM users WHERE email = ?", (lookup_email,)).fetchone()
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
        total_bookings = conn.execute("SELECT COUNT(*) AS count FROM bookings").fetchone()["count"]
        available_seats = conn.execute(
            "SELECT COALESCE(SUM(available_seats), 0) AS total FROM events"
        ).fetchone()["total"]
        active_users = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
        my_bookings_count = conn.execute(
            "SELECT COUNT(*) AS count FROM bookings WHERE user_id = ?", (session["user_id"],)
        ).fetchone()["count"]

        conn.close()
        return render_template(
            "dashboard.html",
            total_events=total_events,
            total_bookings=total_bookings,
            available_seats=available_seats,
            active_users=active_users,
            my_bookings_count=my_bookings_count,
        )

    @app.route("/events")
    def events():
        search_query = request.args.get("q", "").strip()
        category_filter = request.args.get("category", "").strip()
        conn = get_db_connection()
        query = [
            """
            SELECT e.id, e.title, e.description, e.date, e.location, e.available_seats,
                   COALESCE(e.category, 'General') AS category,
                   COALESCE(e.image_url, '') AS image_url,
                   COALESCE(e.seat_capacity, e.available_seats) AS seat_capacity,
                   u.name AS created_by_name
            FROM events e
            JOIN users u ON u.id = e.created_by
            WHERE 1 = 1
            """
        ]
        params = []

        if search_query:
            query.append(" AND (LOWER(e.title) LIKE ? OR LOWER(e.description) LIKE ? OR LOWER(e.location) LIKE ?)")
            like_term = f"%{search_query.lower()}%"
            params.extend([like_term, like_term, like_term])

        if category_filter:
            query.append(" AND COALESCE(e.category, 'General') = ?")
            params.append(category_filter)

        query.append(" ORDER BY e.date ASC")
        events_data = conn.execute("".join(query), params).fetchall()
        categories = conn.execute(
            """
            SELECT DISTINCT COALESCE(category, 'General') AS category
            FROM events
            ORDER BY category ASC
            """
        ).fetchall()
        conn.close()
        return render_template(
            "events.html",
            events=events_data,
            categories=categories,
            search_query=search_query,
            category_filter=category_filter,
        )

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
            category = request.form.get("category", "General").strip() or "General"
            image_url = request.form.get("image_url", "").strip()

            try:
                event_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                event_date = None

            if len(title) < 3 or len(description) < 10 or len(location) < 2:
                flash("Please provide valid title, description and location.", "danger")
                return render_template("create_event.html", event=None)

            if not seats.isdigit() or int(seats) <= 0:
                flash("Available seats must be a positive number.", "danger")
                return render_template("create_event.html", event=None)

            if event_date is None:
                flash("Please choose a valid event date.", "danger")
                return render_template("create_event.html", event=None)

            if event_date < utc_now().date():
                flash("Event date must be in the future.", "danger")
                return render_template("create_event.html", event=None)

            conn = get_db_connection()
            conn.execute(
                """
                INSERT INTO events (
                    title, description, date, location, available_seats, created_by, created_at,
                    category, image_url, seat_capacity
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    title,
                    description,
                    event_date.isoformat(),
                    location,
                    int(seats),
                    session["user_id"],
                    utc_now_iso(),
                    category,
                    image_url,
                    int(seats),
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
            category = request.form.get("category", "General").strip() or "General"
            image_url = request.form.get("image_url", "").strip()

            try:
                event_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                event_date = None

            if len(title) < 3 or len(description) < 10 or len(location) < 2:
                conn.close()
                flash("Please provide valid title, description and location.", "danger")
                return render_template("create_event.html", event=event)

            if not seats.isdigit() or int(seats) < 0:
                conn.close()
                flash("Available seats must be zero or greater.", "danger")
                return render_template("create_event.html", event=event)

            if event_date is None:
                conn.close()
                flash("Please choose a valid event date.", "danger")
                return render_template("create_event.html", event=event)

            conn.execute(
                """
                UPDATE events
                SET title = ?, description = ?, date = ?, location = ?, available_seats = ?, category = ?, image_url = ?, seat_capacity = ?
                WHERE id = ?
                """,
                (
                    title,
                    description,
                    event_date.isoformat(),
                    location,
                    int(seats),
                    category,
                    image_url,
                    int(seats),
                    event_id,
                ),
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
            (session["user_id"], event_id, "booked", utc_now_iso()),
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
            "SELECT id, title, description, date, location, available_seats, category, image_url FROM events ORDER BY date ASC"
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