import streamlit as st
import sqlite3
import pandas as pd

import streamlit as st

if "user" not in st.session_state:
    st.warning(
        "Please login first."
    )
    st.stop()
st.title("💰 Budget Management")

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

category = st.text_input("Category")

budget = st.number_input(
    "Monthly Budget",
    min_value=0.0
)

if st.button("💾 Save Budget"):

    cursor.execute(
        """
        INSERT INTO budgets
        (category,budget)
        VALUES (?,?)
        """,
        (category,budget)
    )

    conn.commit()

    st.success("Budget Saved")

budgets = pd.read_sql(
    "SELECT * FROM budgets",
    conn
)

st.dataframe(
    budgets,
    use_container_width=True
)

conn.close()