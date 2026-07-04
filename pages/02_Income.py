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
st.title("💵 Income Management")

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

categories = [
    "Salary",
    "Bonus",
    "Business",
    "Freelance",
    "Rental Income",
    "Interest",
    "Other"
]

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
        min_value=0.0
    )

    submit = st.form_submit_button(
        "💾 Save Income"
    )

if submit:

    cursor.execute(
        """
        INSERT INTO income
        (date, category, description, amount)
        VALUES (?, ?, ?, ?)
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
        "Income Added Successfully"
    )

df = pd.read_sql(
    "SELECT * FROM income ORDER BY id DESC",
    conn
)

st.dataframe(
    df,
    use_container_width=True
)

conn.close()