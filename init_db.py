import sqlite3
from werkzeug.security import generate_password_hash

# Connect to the database file (creates it if it doesn't exist)
conn = sqlite3.connect("marketplace.db")
cur = conn.cursor()

# Build the tables (wipes old ones first, so it can rerun safely)
cur.executescript("""
DROP TABLE IF EXISTS listings;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_verified INTEGER NOT NULL DEFAULT 0,
    verification_code TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    category TEXT NOT NULL,
    condition TEXT,
    photo TEXT,
    contact_info TEXT NOT NULL,
    is_available INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
""")

# Add one fake verified seller
cur.execute(
    "INSERT INTO users (email, password_hash, is_verified) VALUES (?, ?, ?)",
    ("test.seller@sjsu.edu", generate_password_hash("password123"), 1),
)
seller_id = cur.lastrowid

# Add a few fake listings
sample_listings = [
    ("Calculus Textbook", "Stewart 8th edition, some highlighting.", 40.00, "Textbooks", "Good", "test.seller@sjsu.edu"),
    ("Mini Fridge", "Works great, fits under a desk.", 60.00, "Furniture", "Like New", "test.seller@sjsu.edu"),
    ("TI-84 Calculator", "Comes with batteries.", 55.00, "Electronics", "Good", "test.seller@sjsu.edu"),
    ("Desk Lamp", "LED, adjustable brightness.", 15.00, "Furniture", "Fair", "test.seller@sjsu.edu"),
]

for title, desc, price, category, condition, contact in sample_listings:
    cur.execute(
        """INSERT INTO listings (user_id, title, description, price, category, condition, contact_info)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (seller_id, title, desc, price, category, condition, contact),
    )

conn.commit()
conn.close()
print("Database created with sample data!")
