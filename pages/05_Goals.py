import streamlit as st

# Security check
if "user" not in st.session_state:
    st.session_state["user"] = None

if st.session_state["user"] is None:
    st.warning(
        "Please login first."
    )
    st.switch_page("app.py")
    st.stop()
from database.db import (
    get_connection,
    create_tables
)

# Ensure tables exist
create_tables()

if "user" not in st.session_state:
    st.warning(
        "Please login first."
    )
    st.stop()

st.title("🎯 Savings Goals")

conn = get_connection()
cursor = conn.cursor()

with st.form("goal_form"):

    goal_name = st.text_input(
        "Goal Name"
    )

    target = st.number_input(
        "Target Amount",
        min_value=0.0,
        format="%.2f"
    )

    current = st.number_input(
        "Current Amount",
        min_value=0.0,
        format="%.2f"
    )

    submit = st.form_submit_button(
        "Save Goal"
    )

if submit:

    try:

        cursor.execute(
            """
            INSERT INTO goals
            (
                goal_name,
                target,
                current
            )
            VALUES
            (
                ?, ?, ?
            )
            """,
            (
                goal_name,
                target,
                current
            )
        )

        conn.commit()

        st.success(
            "Goal saved successfully."
        )

    except Exception as e:

        st.error(
            f"Error saving goal: {e}"
        )

try:

    goals = pd.read_sql(
        """
        SELECT *
        FROM goals
        ORDER BY id DESC
        """,
        conn
    )

    if len(goals) > 0:

        st.subheader(
            "Your Goals"
        )

        for _, row in goals.iterrows():

            if row["target"] > 0:

                progress = (
                    row["current"]
                    / row["target"]
                )

            else:

                progress = 0

            st.markdown(
                f"""
                ### {row['goal_name']}

                **Current Amount:** UGX {row['current']:,.0f}

                **Target Amount:** UGX {row['target']:,.0f}
                """
            )

            st.progress(
                min(progress, 1.0)
            )

    else:

        st.info(
            "No goals added yet."
        )

except Exception as e:

    st.error(
        f"Error loading goals: {e}"
    )

conn.close()