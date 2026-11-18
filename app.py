import sqlite3
import os

from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from flask import (
    Flask,
    render_template,
    request,
    abort,
    redirect,
    url_for,
    session,
    g,
)

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

csrf = CSRFProtect(app)

DATABASE = "marketplace.db"
CATEGORIES = ["Textbooks", "Electronics", "Furniture", "Clothing", "Other"]
CONDITIONS = ["New", "Like New", "Good", "Fair"]
SORT_OPTIONS = {
    "newest": "created_at DESC, id DESC",
    "price_low": "price ASC",
    "price_high": "price DESC",
}


def get_db():
    """Open a connection to the database. Rows act like dictionaries (row["title"])."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.before_request
def load_logged_in_user():
    g.user = None
    user_id = session.get("user_id")

    if user_id is None:
        return

    conn = get_db()

    try:
        g.user = conn.execute(
            "SELECT id, email, is_verified FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()

    if g.user is None:
        session.clear()

def to_number(text):
    """Turn "25" into 25.0. Return None if it's blank or not a number."""
    try:
        return float(text)
    except ValueError:
        return None


@app.route("/")
def browse():
    # Read the search/filter choices from the URL, e.g. /?q=lamp&category=Furniture
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "")
    condition = request.args.get("condition", "")
    min_price = request.args.get("min_price", "")
    max_price = request.args.get("max_price", "")
    sort = request.args.get("sort", "newest")

    # Start with every available (not sold) listing, then narrow it down
    query = "SELECT * FROM listings WHERE is_available = 1"
    params = []

    if search:
        query += " AND (title LIKE ? OR description LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]

    if category in CATEGORIES:
        query += " AND category = ?"
        params.append(category)

    if condition in CONDITIONS:
        query += " AND condition = ?"
        params.append(condition)

    min_value = to_number(min_price)
    if min_value is not None:
        query += " AND price >= ?"
        params.append(min_value)

    max_value = to_number(max_price)
    if max_value is not None:
        query += " AND price <= ?"
        params.append(max_value)

    query += " ORDER BY " + SORT_OPTIONS.get(sort, SORT_OPTIONS["newest"])

    conn = get_db()
    listings = conn.execute(query, params).fetchall()
    conn.close()

    return render_template(
        "browse.html",
        listings=listings,
        categories=CATEGORIES,
        conditions=CONDITIONS,
        filters=request.args,
    )

@app.route("/listing/<int:listing_id>")
def listing_detail(listing_id):
    conn = get_db()

    try:
        listing = conn.execute(
            "SELECT * FROM listings WHERE id = ?",
            (listing_id,),
        ).fetchone()
    finally:
        conn.close()

    if listing is None:
        abort(404)

    return render_template("listing_detail.html", listing=listing)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if g.user is not None:
        return redirect(url_for("browse"))

    error = None
    email = ""

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        local_part, separator, domain = email.partition("@")

        if (
            not separator
            or not local_part
            or domain != "sjsu.edu"
            or any(character.isspace() for character in email)
        ):
            error = "Please use your @sjsu.edu email address."
        elif len(password) < 8:
            error = "Use a password with at least 8 characters."
        elif password != confirm_password:
            error = "Your passwords do not match."
        else:
            password_hash = generate_password_hash(password)
            conn = get_db()

            try:
                conn.execute(
                    """
                    INSERT INTO users (email, password_hash, is_verified)
                    VALUES (?, ?, 0)
                    """,
                    (email, password_hash),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                conn.rollback()
                error = "An account with that email already exists."
            finally:
                conn.close()

            if error is None:
                return redirect(url_for("login"))

    return render_template("signup.html", error=error, email=email)

@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user is not None:
        return redirect(url_for("browse"))

    error = None
    email = ""

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db()

        try:
            user = conn.execute(
                "SELECT * FROM users WHERE email = ? COLLATE NOCASE",
                (email,),
            ).fetchone()
        finally:
            conn.close()

        if user is None or not check_password_hash(
            user["password_hash"], password
        ):
            error = "Incorrect email or password."
        else:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("browse"))

    return render_template("login.html", error=error, email=email)

@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("browse"))

if __name__ == "__main__":
    app.run(debug=True, port=5001)
