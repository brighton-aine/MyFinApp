import streamlit as st

from database.db import get_connection

# -------------------------
# SECURITY
# -------------------------
if "user" not in st.session_state:
    st.session_state["user"] = None

if st.session_state["user"] is None:
    st.warning(
        "Please login first."
    )
    st.switch_page("app.py")
    st.stop()

# -------------------------
# PAGE TITLE
# -------------------------
st.title("👤 My Profile")

# -------------------------
# DATABASE
# -------------------------
conn = get_connection()
cursor = conn.cursor()

user = cursor.execute(
    """
    SELECT username, email
    FROM users
    WHERE username = ?
    """,
    (
        st.session_state["user"],
    )
).fetchone()

# -------------------------
# USER NOT FOUND
# -------------------------
if user is None:

    st.error(
        "User profile not found."
    )

    conn.close()
    st.stop()

# -------------------------
# DISPLAY PROFILE
# -------------------------
st.write(
    f"**Username:** {user[0]}"
)

st.write(
    f"**Email:** {user[1]}"
)

# -------------------------
# UPDATE PROFILE
# -------------------------
new_email = st.text_input(
    "Update Email",
    value=user[1]
)

if st.button("Update Profile"):

    try:

        cursor.execute(
            """
            UPDATE users
            SET email = ?
            WHERE username = ?
            """,
            (
                new_email,
                st.session_state["user"]
            )
        )

        conn.commit()

        st.success(
            "Profile updated successfully."
        )

    except Exception as e:

        st.error(
            f"Error updating profile: {e}"
        )

# -------------------------
# CLOSE CONNECTION
# -------------------------
conn.close()