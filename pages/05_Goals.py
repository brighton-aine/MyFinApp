import streamlit as st
import sqlite3
import pandas as pd

import streamlit as st

if "user" not in st.session_state:
    st.warning(
        "Please login first."
    )
    st.stop()

st.title("Savings Goals")

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

with st.form("goal_form"):

    goal_name = st.text_input(
        "Goal Name"
    )

    target = st.number_input(
        "Target Amount",
        min_value=0.0
    )

    current = st.number_input(
        "Current Amount",
        min_value=0.0
    )

    submit = st.form_submit_button(
        "Save Goal"
    )

if submit:

    cursor.execute(
        """
        INSERT INTO goals
        (goal_name,target,current)
        VALUES (?,?,?)
        """,
        (
            goal_name,
            target,
            current
        )
    )

    conn.commit()

goals = pd.read_sql(
    "SELECT * FROM goals",
    conn
)

for _, row in goals.iterrows():

    progress = (
        row["current"] /
        row["target"]
        if row["target"] > 0
        else 0
    )

    st.markdown(
        f"""
        ### {row['goal_name']}

        UGX {row['current']:,.0f}
        of
        UGX {row['target']:,.0f}
        """
    )

    st.progress(
        min(progress,1.0)
    )

conn.close()