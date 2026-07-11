import re
import hmac
import hashlib

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
# PASSWORD HASHING HELPERS
#
# Matches your login page (app.py) exactly: hashlib.sha256(password)
# hexdigest, unsalted. Using a different scheme here (e.g. a salted
# hash) would make "Current Password" verification fail for every
# real account, since app.py is what actually wrote the stored value.
#
# Note: unsalted single-round SHA-256 is hashed (not plain text), but
# it's weaker than a proper password hash (no salt means identical
# passwords produce identical hashes, and it's fast to brute-force).
# If you want to upgrade to something like PBKDF2 or bcrypt later,
# both this page and app.py's login/register logic need to change
# together — happy to do that as a follow-up.
# =====================================================


def hash_password(password: str) -> str:

    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, stored: str) -> bool:

    if not stored:
        return False

    return hmac.compare_digest(
        hashlib.sha256(password.encode()).hexdigest(),
        stored
    )


def is_valid_email(value: str) -> bool:

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return re.match(pattern, value.strip()) is not None


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
# OPTIONAL: MEMBER SINCE
# =====================================================

member_since = None

try:

    joined_row = cursor.execute(
        "SELECT created_at FROM users WHERE username = ?",
        (username,)
    ).fetchone()

    if joined_row and joined_row[0]:
        member_since = joined_row[0]

except Exception:

    member_since = None

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
# ACCOUNT USAGE STATS
# =====================================================

try:
    income_count = cursor.execute(
        "SELECT COUNT(*) FROM income"
    ).fetchone()[0]
except Exception:
    income_count = 0

try:
    expense_count = cursor.execute(
        "SELECT COUNT(*) FROM expenses"
    ).fetchone()[0]
except Exception:
    expense_count = 0

try:
    goal_count = cursor.execute(
        "SELECT COUNT(*) FROM goals"
    ).fetchone()[0]
except Exception:
    goal_count = 0

total_transactions = income_count + expense_count

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.metric(
        "📊 Total Transactions",
        total_transactions
    )

with c2:

    st.metric(
        "🎯 Goals Created",
        goal_count
    )

with c3:

    st.metric(
        "📅 Member Since",
        member_since if member_since else "N/A"
    )

with c4:

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
            "💾 Update Profile",
            use_container_width=True
        )
    )

if update_profile:

    if not is_valid_email(new_email):

        st.error(
            "Please enter a valid email address."
        )

    else:

        try:

            cursor.execute(
                """
                UPDATE users
                SET email = ?
                WHERE username = ?
                """,
                (
                    new_email.strip(),
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
# CHANGE PASSWORD
# =====================================================

st.divider()

st.subheader(
    "🔑 Change Password"
)

st.caption(
    "Your new password is hashed the same way your account already is."
)

with st.form("change_password_form", clear_on_submit=True):

    current_password = st.text_input(
        "Current Password",
        type="password"
    )

    pw_col1, pw_col2 = st.columns(2)

    with pw_col1:

        new_password = st.text_input(
            "New Password",
            type="password"
        )

    with pw_col2:

        confirm_password = st.text_input(
            "Confirm New Password",
            type="password"
        )

    change_password_btn = st.form_submit_button(
        "🔒 Update Password",
        use_container_width=True
    )

if change_password_btn:

    try:

        stored_row = cursor.execute(
            "SELECT password FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        stored_password = stored_row[0] if stored_row else None

    except Exception as e:

        stored_password = None

        st.error(
            "Couldn't read the stored password — this page assumes a "
            f"`password` column on the `users` table. Details: {e}"
        )

    if stored_password is None:

        pass  # error already shown above, or user has no password set

    elif not verify_password(current_password, stored_password):

        st.error(
            "Current password is incorrect."
        )

    elif len(new_password) < 8:

        st.warning(
            "New password must be at least 8 characters long."
        )

    elif new_password != confirm_password:

        st.warning(
            "New password and confirmation do not match."
        )

    elif new_password == current_password:

        st.warning(
            "New password must be different from your current password."
        )

    else:

        try:

            cursor.execute(
                """
                UPDATE users
                SET password = ?
                WHERE username = ?
                """,
                (
                    hash_password(new_password),
                    username
                )
            )

            conn.commit()

            st.success(
                "Password updated and securely hashed."
            )

        except Exception as e:

            st.error(
                f"Error updating password: {e}"
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
• Use a strong, unique password (12+ characters, mixed case, numbers, symbols)

• Change your password regularly, and immediately if you suspect it's been exposed

• Never share your credentials, even with people you trust

• Logout on shared or public devices

• Review your account activity frequently
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