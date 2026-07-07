import streamlit as st
import hashlib

from database.db import (
    create_tables,
    get_connection
)

# Create tables
create_tables()

st.set_page_config(
    page_title="MyFinApp",
    page_icon="💰",
    layout="wide"
)

# Session
if "user" not in st.session_state:
    st.session_state["user"] = None

# If already logged in
if st.session_state["user"] is not None:
    st.switch_page("pages/01_Dashboard.py")

conn = get_connection()
cursor = conn.cursor()

st.title("💰 MyFinApp")

login_tab, register_tab = st.tabs(
    ["🔐 Login", "📝 Register"]
)

# ---------------- LOGIN ----------------

with login_tab:

    username = st.text_input(
        "Username",
        key="login_user"
    )

    password = st.text_input(
        "Password",
        type="password",
        key="login_pass"
    )

    if st.button("Login"):

        hashed_password = hashlib.sha256(
            password.encode()
        ).hexdigest()

        user = cursor.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            AND password = ?
            """,
            (
                username,
                hashed_password
            )
        ).fetchone()

        if user:

            st.session_state["user"] = username

            st.success(
                "Login successful!"
            )

            st.switch_page(
                "pages/01_Dashboard.py"
            )

        else:

            st.error(
                "Invalid username or password"
            )

# ---------------- REGISTER ----------------

with register_tab:

    new_user = st.text_input(
        "Username",
        key="reg_user"
    )

    email = st.text_input(
        "Email"
    )

    new_password = st.text_input(
        "Password",
        type="password",
        key="reg_pass"
    )

    if st.button("Register"):

        try:

            hashed_password = hashlib.sha256(
                new_password.encode()
            ).hexdigest()

            cursor.execute(
                """
                INSERT INTO users
                (
                    username,
                    email,
                    password
                )
                VALUES (?, ?, ?)
                """,
                (
                    new_user,
                    email,
                    hashed_password
                )
            )

            conn.commit()

            st.success(
                "Registration successful. Please login."
            )

        except Exception:

            st.error(
                "Username or email already exists."
            )

conn.close()