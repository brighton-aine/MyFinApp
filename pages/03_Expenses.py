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
st.title("💸 Expense Management")

# -------------------------
# DATABASE
# -------------------------
conn = get_connection()
cursor = conn.cursor()

# -------------------------
# CATEGORIES
# -------------------------
categories = [
    "Housing",
    "Food",
    "Transport",
    "Healthcare",
    "Education",
    "Entertainment",
    "Insurance",
    "Savings",
    "Travel",
    "Utilities",
    "Other"
]

# -------------------------
# EXPENSE FORM
# -------------------------
with st.form("expense_form"):

    expense_date = st.date_input(
        "Date",
        value=date.today()
    )

    category = st.selectbox(
        "Category",
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

    save = st.form_submit_button(
        "💾 Save Expense"
    )

# -------------------------
# SAVE EXPENSE
# -------------------------
if save:

    try:

        cursor.execute(
            """
            INSERT INTO expenses
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
                str(expense_date),
                category,
                description,
                amount
            )
        )

        conn.commit()

        st.success(
            "Expense added successfully."
        )

    except Exception as e:

        st.error(
            f"Error saving expense: {e}"
        )

# -------------------------
# DISPLAY EXPENSES
# -------------------------
try:

    expenses = pd.read_sql(
        """
        SELECT *
        FROM expenses
        ORDER BY id DESC
        """,
        conn
    )

    st.subheader(
        "Expense Records"
    )

    st.dataframe(
        expenses,
        use_container_width=True
    )

except Exception as e:

    st.error(
        f"Error loading expenses: {e}"
    )

# -------------------------
# SUMMARY
# -------------------------
if not expenses.empty:

    total_expenses = expenses[
        "amount"
    ].sum()

    st.metric(
        "Total Expenses",
        f"UGX {total_expenses:,.0f}"
    )

# -------------------------
# CLOSE CONNECTION
# -------------------------
conn.close()