import streamlit as st
import sqlite3
from datetime import date
import pandas as pd

import streamlit as st

if "user" not in st.session_state:
    st.warning(
        "Please login first."
    )
    st.stop()

st.title("💸 Expense Management")

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

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
        min_value=0.0
    )

    save = st.form_submit_button(
        "💾 Save Expense"
    )

if save:

    cursor.execute(
        """
        INSERT INTO expenses
        (date, category, description, amount)
        VALUES (?, ?, ?, ?)
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
        "Expense Added Successfully"
    )

expenses = pd.read_sql(
    "SELECT * FROM expenses ORDER BY id DESC",
    conn
)

st.dataframe(
    expenses,
    use_container_width=True
)

conn.close()