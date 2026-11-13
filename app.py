import sqlite3
from flask import Flask, render_template, request

app = Flask(__name__)

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


if __name__ == "__main__":
    app.run(debug=True, port=5001)
