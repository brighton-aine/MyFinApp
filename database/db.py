import sqlite3
import os

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DB_NAME = os.path.join(
    BASE_DIR,
    "database.db"
)


def get_connection():
    return sqlite3.connect(DB_NAME)


def create_tables():

    conn = get_connection()
    cursor = conn.cursor()

    # Income
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS income(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        category TEXT,
        description TEXT,
        amount REAL
    )
    """)

    # Expenses
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        category TEXT,
        description TEXT,
        amount REAL
    )
    """)

    # Budgets
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS budgets(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        budget REAL
    )
    """)

  # Goals
cursor.execute("""
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_name TEXT NOT NULL,
    target REAL NOT NULL DEFAULT 0,
    current REAL NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Upgrade existing databases
try:
    cursor.execute(
        "ALTER TABLE goals ADD COLUMN target REAL DEFAULT 0"
    )
except Exception:
    pass

try:
    cursor.execute(
        "ALTER TABLE goals ADD COLUMN current REAL DEFAULT 0"
    )
except Exception:
    pass

# Users
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    email TEXT UNIQUE,
    password TEXT
)
""")

conn.commit()
conn.close()