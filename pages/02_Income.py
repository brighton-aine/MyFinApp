import streamlit as st
import pandas as pd
from datetime import date

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
st.title("💵 Income Management")

# -------------------------
# DATABASE
# -------------------------
conn = get_connection()
cursor = conn.cursor()

# -------------------------
# CATEGORIES
# -------------------------
categories = [
    "Salary",
    "Bonus",
    "Business",
    "Freelance",
    "Rental Income",
    "Interest",
    "Other"
]

# -------------------------
# FORM
# -------------------------
with st.form("income_form"):

    income_date = st.date_input(
        "Date",
        value=date.today()
    )

    category = st.selectbox(
        "Income Category",
        categories
    )

    description = st.text_input(
        "Description"
    )

    amount = st.number_input(
        "Amount",
        min_value=0.0,
        format="%.2f"
    )

    submit = st.form_submit_button(
        "💾 Save Income"
    )

# -------------------------
# SAVE INCOME
# -------------------------
if submit:

    try:

        cursor.execute(
            """
            INSERT INTO income
            (
                date,
                category,
                description,
                amount
            )
            VALUES
            (
                ?, ?, ?, ?
            )
            """,
            (
                str(income_date),
                category,
                description,
                amount
            )
        )

        conn.commit()

        st.success(
            "Income added successfully."
        )

    except Exception as e:

        st.error(
            f"Error saving income: {e}"
        )

# -------------------------
# DISPLAY INCOME
# -------------------------
try:

    df = pd.read_sql(
        """
        SELECT *
        FROM income
        ORDER BY id DESC
        """,
        conn
    )

    st.subheader(
        "Income Records"
    )

    st.dataframe(
        df,
        use_container_width=True
    )

except Exception as e:

    st.error(
        f"Error loading income records: {e}"
    )

# -------------------------
# CLOSE CONNECTION
# -------------------------
conn.close()