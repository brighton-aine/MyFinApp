import streamlit as st
import hashlib

from database.db import (
    create_tables,
    get_connection
)

# Create tables at startup
create_tables()

st.set_page_config(
    page_title="MyFinApp",
    page_icon="💰",
    layout="wide"
)

if "user" not in st.session_state:
    st.session_state["user"] = None

conn = get_connection()
cursor = conn.cursor()

# USER LOGGED IN
if st.session_state["user"]:

    st.title("💰 MyFinApp")

    st.success(
        f"Welcome {st.session_state['user']}"
    )

    st.info(
        "Select a menu item from the sidebar."
    )

# LOGIN / REGISTER
else:

    st.title("💰 MyFinApp")

    login_tab, register_tab = st.tabs(
        ["🔐 Login", "📝 Register"]
    )

    # LOGIN
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
                WHERE username=?
                AND password=?
                """,
                (
                    username,
                    hashed_password
                )
            ).fetchone()

            if user:

                st.session_state["user"] = username

                st.success(
                    "Login successful"
                )

                st.rerun()

            else:

                st.error(
                    "Invalid username or password"
                )

    # REGISTER
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
                    VALUES
                    (
                        ?, ?, ?
                    )
                    """,
                    (
                        new_user,
                        email,
                        hashed_password
                    )
                )

                conn.commit()

                st.success(
                    "Registration successful. You can now login."
                )

            except Exception:

                st.error(
                    "Username or email already exists."
                )

conn.close()