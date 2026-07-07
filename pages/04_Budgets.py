import streamlit as st
import pandas as pd

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
st.title("💰 Budget Management")

# -------------------------
# DATABASE
# -------------------------
conn = get_connection()
cursor = conn.cursor()

# -------------------------
# BUDGET FORM
# -------------------------
st.subheader("Create Budget")

category = st.text_input(
    "Category"
)

budget = st.number_input(
    "Monthly Budget",
    min_value=0.0,
    format="%.2f"
)

if st.button("💾 Save Budget"):

    if category.strip() == "":

        st.warning(
            "Please enter a budget category."
        )

    else:

        try:

            cursor.execute(
                """
                INSERT INTO budgets
                (
                    category,
                    budget
                )
                VALUES
                (
                    ?, ?
                )
                """,
                (
                    category,
                    budget
                )
            )

            conn.commit()

            st.success(
                "Budget saved successfully."
            )

        except Exception as e:

            st.error(
                f"Error saving budget: {e}"
            )

# -------------------------
# DISPLAY BUDGETS
# -------------------------
try:

    budgets = pd.read_sql(
        """
        SELECT *
        FROM budgets
        ORDER BY id DESC
        """,
        conn
    )

    st.subheader(
        "Budget Records"
    )

    st.dataframe(
        budgets,
        use_container_width=True
    )

    if not budgets.empty:

        total_budget = budgets[
            "budget"
        ].sum()

        st.metric(
            "Total Budget",
            f"UGX {total_budget:,.0f}"
        )

except Exception as e:

    st.error(
        f"Error loading budgets: {e}"
    )

# -------------------------
# CLOSE CONNECTION
# -------------------------
conn.close()