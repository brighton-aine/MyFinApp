import streamlit as st
import hashlib

from database.db import (
    create_tables,
    get_connection
)

# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="MyFinApp",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# LOAD GLOBAL CSS
# =====================================================

def load_css():
    try:
        with open("assets/styles.css") as f:
            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True
            )
    except:
        pass

load_css()

# =====================================================
# CREATE DATABASE TABLES
# =====================================================

create_tables()

# =====================================================
# SESSION MANAGEMENT
# =====================================================

if "user" not in st.session_state:
    st.session_state["user"] = None

# Redirect logged-in users

if st.session_state["user"] is not None:
    st.switch_page("pages/01_Dashboard.py")

# =====================================================
# DATABASE CONNECTION
# =====================================================

conn = get_connection()
cursor = conn.cursor()

# =====================================================
# APP HEADER
# =====================================================

st.markdown("""
<div style="
text-align:center;
padding:20px;
">

<h1 style="
font-size:50px;
font-weight:800;
color:#2563EB;
margin-bottom:0px;
">
💰 MyFinApp
</h1>

<p style="
font-size:18px;
color:#64748B;
">
Smart Personal Finance Management Platform
</p>

</div>
""", unsafe_allow_html=True)

# =====================================================
# TWO COLUMN LAYOUT
# =====================================================

left_col, right_col = st.columns([1, 1])

# =====================================================
# LOGIN TAB
# =====================================================

with left_col:

    st.markdown("## 🔐 Account Access")

    login_tab, register_tab = st.tabs(
        ["Login", "Register"]
    )

    # =================================================
    # LOGIN
    # =================================================

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

        if st.button(
            "🚀 Login",
            use_container_width=True
        ):

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
                    f"Welcome {username}"
                )

                st.switch_page(
                    "pages/01_Dashboard.py"
                )

            else:

                st.error(
                    "Invalid username or password"
                )

    # =================================================
    # REGISTER
    # =================================================

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

        if st.button(
            "✅ Create Account",
            use_container_width=True
        ):

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

# =====================================================
# RIGHT SIDE INFORMATION PANEL
# =====================================================

with right_col:

    st.markdown("""
    <div style="
    background:linear-gradient(
        135deg,
        #2563EB,
        #7C3AED
    );
    padding:40px;
    border-radius:20px;
    color:white;
    min-height:450px;
    ">

    <h2 style="color:white;">
    📊 Financial Health Dashboard
    </h2>

    <br>

    <h4 style="color:white;">
    Features
    </h4>

    ✅ Income Tracking

    <br><br>

    ✅ Expense Management

    <br><br>

    ✅ Budget Planning

    <br><br>

    ✅ Financial Goals

    <br><br>

    ✅ Net Worth Tracking

    <br><br>

    ✅ Forecasting

    <br><br>

    ✅ Financial Reports

    <br><br>

    ✅ AI Financial Insights

    </div>
    """, unsafe_allow_html=True)

# =====================================================
# FOOTER
# =====================================================

st.markdown("---")

st.caption(
    "© 2026 MyFinApp | Personal Finance Management Platform"
)

# =====================================================
# CLOSE CONNECTION
# =====================================================

conn.close()