import streamlit as st
import sqlite3

st.title("👤 My Profile")

if "user" not in st.session_state:

    st.stop()

conn = sqlite3.connect(
    "database.db"
)

cursor = conn.cursor()

user = cursor.execute(
    """
    SELECT username,email
    FROM users
    WHERE username=?
    """,
    (
        st.session_state.user,
    )
).fetchone()

st.write(
    f"Username: {user[0]}"
)

st.write(
    f"Email: {user[1]}"
)

new_email = st.text_input(
    "Update Email",
    value=user[1]
)

if st.button("Update Profile"):

    cursor.execute(
        """
        UPDATE users
        SET email=?
        WHERE username=?
        """,
        (
            new_email,
            st.session_state.user
        )
    )

    conn.commit()

    st.success(
        "Profile updated."
    )

conn.close()