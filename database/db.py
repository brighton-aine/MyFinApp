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
    CREATE TABLE IF NOT EXISTS goals(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal_name TEXT,
        target REAL DEFAULT 0,
        current REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Fix old databases
    columns = [
        row[1]
        for row in cursor.execute(
            "PRAGMA table_info(goals)"
        ).fetchall()
    ]

    if "goal_name" not in columns:
        cursor.execute(
            "ALTER TABLE goals ADD COLUMN goal_name TEXT"
        )

    if "target" not in columns:
        cursor.execute(
            "ALTER TABLE goals ADD COLUMN target REAL DEFAULT 0"
        )

    if "current" not in columns:
        cursor.execute(
            "ALTER TABLE goals ADD COLUMN current REAL DEFAULT 0"
        )

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