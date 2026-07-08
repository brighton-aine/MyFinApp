import streamlit as st
import pandas as pd

from utils import (
    require_login,
    load_css,
    render_sidebar,
    page_header
)

from database.db import get_connection

# =====================================================
# APP SETUP
# =====================================================

load_css()
require_login()
render_sidebar()

page_header(
    "👤 My Profile",
    "Manage your account information and settings."
)

# =====================================================
# DATABASE
# =====================================================

conn = get_connection()
cursor = conn.cursor()

# =====================================================
# USER DETAILS
# =====================================================

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

# =====================================================
# USER NOT FOUND
# =====================================================

if user is None:

    st.error(
        "User profile not found."
    )

    conn.close()
    st.stop()

username = user[0]
email = user[1]

# =====================================================
# PROFILE CARD
# =====================================================

st.markdown(
    f"""
    <div style="
    background:linear-gradient(
        135deg,
        #2563EB,
        #7C3AED
    );
    padding:25px;
    border-radius:20px;
    color:white;
    margin-bottom:20px;
    ">

        <h2 style="color:white;">
        Welcome, {username}
        </h2>

        <p>
        📧 {email}
        </p>

        <p>
        ✅ Account Status: Active
        </p>

    </div>
    """,
    unsafe_allow_html=True
)

# =====================================================
# ACCOUNT KPIs
# =====================================================

c1, c2, c3 = st.columns(3)

with c1:

    st.metric(
        "👤 Username",
        username
    )

with c2:

    st.metric(
        "📧 Email",
        email
    )

with c3:

    st.metric(
        "✅ Status",
        "Active"
    )

# =====================================================
# ACCOUNT INFORMATION
# =====================================================

st.divider()

st.subheader(
    "📋 Account Information"
)

profile_df = pd.DataFrame(
    {
        "Field": [
            "Username",
            "Email",
            "Account Status"
        ],
        "Value": [
            username,
            email,
            "Active"
        ]
    }
)

st.dataframe(
    profile_df,
    use_container_width=True,
    hide_index=True
)

# =====================================================
# UPDATE PROFILE
# =====================================================

st.divider()

st.subheader(
    "✏️ Update Profile"
)

with st.form("update_profile_form"):

    new_email = st.text_input(
        "Email Address",
        value=email
    )

    update_profile = (
        st.form_submit_button(
            "💾 Update Profile"
        )
    )

if update_profile:

    try:

        cursor.execute(
            """
            UPDATE users
            SET email = ?
            WHERE username = ?
            """,
            (
                new_email,
                username
            )
        )

        conn.commit()

        st.success(
            "Profile updated successfully."
        )

        st.rerun()

    except Exception as e:

        st.error(
            f"Error updating profile: {e}"
        )

# =====================================================
# SECURITY TIPS
# =====================================================

st.divider()

st.subheader(
    "🔒 Security Center"
)

st.info(
    """
• Use a strong password

• Change your password regularly

• Keep credentials private

• Logout on shared devices

• Review account activity frequently
"""
)

# =====================================================
# ACCOUNT SUMMARY
# =====================================================

st.divider()

st.markdown(
    """
    <div style="
    background:linear-gradient(
        135deg,
        #10B981,
        #059669
    );
    padding:25px;
    border-radius:20px;
    color:white;
    ">

        <h3 style="color:white;">
        📈 Account Summary
        </h3>

        <p>
        Your MyFinApp account is active and ready
        to help you manage income, expenses, budgets,
        savings goals, reports, forecasts and overall
        financial health.
        </p>

    </div>
    """,
    unsafe_allow_html=True
)

# =====================================================
# APP INFORMATION
# =====================================================

st.divider()

st.subheader(
    "ℹ️ Application Information"
)

app_info = pd.DataFrame(
    {
        "Setting": [
            "Application",
            "Version",
            "Status"
        ],
        "Value": [
            "MyFinApp",
            "1.0",
            "Operational"
        ]
    }
)

st.dataframe(
    app_info,
    use_container_width=True,
    hide_index=True
)

# =====================================================
# FOOTER
# =====================================================

st.divider()

st.caption(
    "MyFinApp • Personal Finance Management System"
)

# =====================================================
# CLOSE DATABASE
# =====================================================

conn.close()