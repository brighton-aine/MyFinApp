import streamlit as st
import pandas as pd
import plotly.express as px

from utils import (
    require_login,
    load_css,
    render_sidebar,
    page_header,
    money
)

from database.db import get_connection

# =====================================================
# APP SETUP
# =====================================================

load_css()
require_login()
render_sidebar()

page_header(
    "💰 Budget Management",
    "Create, update and monitor financial budgets."
)

# =====================================================
# DATABASE
# =====================================================

conn = get_connection()
cursor = conn.cursor()

# =====================================================
# ADD BUDGET
# =====================================================

with st.expander(
    "➕ Create Budget",
    expanded=True
):

    with st.form("add_budget_form"):

        category = st.text_input(
            "Budget Category"
        )

        budget = st.number_input(
            "Budget Amount (UGX)",
            min_value=0.0,
            format="%.2f"
        )

        save_budget = st.form_submit_button(
            "💾 Save Budget"
        )

if save_budget:

    if category.strip() == "":

        st.warning(
            "Please enter a category."
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

            st.rerun()

        except Exception as e:

            st.error(
                f"Error: {e}"
            )

# =====================================================
# LOAD BUDGETS
# =====================================================

budget_df = pd.read_sql(
    """
    SELECT *
    FROM budgets
    ORDER BY id DESC
    """,
    conn
)

# =====================================================
# KPI CARDS
# =====================================================

if not budget_df.empty:

    total_budget = (
        budget_df["budget"]
        .sum()
    )

    average_budget = (
        budget_df["budget"]
        .mean()
    )

    highest_budget = (
        budget_df["budget"]
        .max()
    )

    categories_count = len(
        budget_df
    )

else:

    total_budget = 0
    average_budget = 0
    highest_budget = 0
    categories_count = 0

st.divider()

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.metric(
        "💰 Total Budget",
        money(total_budget)
    )

with c2:

    st.metric(
        "📂 Categories",
        categories_count
    )

with c3:

    st.metric(
        "📊 Average Budget",
        money(average_budget)
    )

with c4:

    st.metric(
        "🏆 Highest Budget",
        money(highest_budget)
    )

# =====================================================
# CHARTS
# =====================================================

if not budget_df.empty:

    st.divider()

    left, right = st.columns(2)

    with left:

        st.subheader(
            "🥧 Budget Distribution"
        )

        fig = px.pie(
            budget_df,
            names="category",
            values="budget",
            hole=0.65
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with right:

        st.subheader(
            "📊 Budget Allocation"
        )

        fig = px.bar(
            budget_df,
            x="category",
            y="budget",
            color="budget",
            color_continuous_scale="Blues"
        )

        fig.update_layout(
            height=450
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# =====================================================
# EDIT / DELETE BUDGET
# =====================================================

st.divider()

st.subheader(
    "✏️ Edit or Delete Budget"
)

if not budget_df.empty:

    selected_id = st.selectbox(
        "Select Budget",
        budget_df["id"]
    )

    selected_budget = budget_df[
        budget_df["id"] == selected_id
    ].iloc[0]

    with st.form(
        "edit_budget_form"
    ):

        edit_category = st.text_input(
            "Category",
            value=selected_budget[
                "category"
            ]
        )

        edit_budget = st.number_input(
            "Budget Amount",
            min_value=0.0,
            value=float(
                selected_budget[
                    "budget"
                ]
            )
        )

        col1, col2 = st.columns(2)

        with col1:

            update_btn = (
                st.form_submit_button(
                    "💾 Update"
                )
            )

        with col2:

            delete_btn = (
                st.form_submit_button(
                    "🗑 Delete"
                )
            )

    # UPDATE

    if update_btn:

        try:

            cursor.execute(
                """
                UPDATE budgets
                SET
                    category=?,
                    budget=?
                WHERE id=?
                """,
                (
                    edit_category,
                    edit_budget,
                    int(selected_id)
                )
            )

            conn.commit()

            st.success(
                "Budget updated successfully."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Error: {e}"
            )

    # DELETE

    if delete_btn:

        try:

            cursor.execute(
                """
                DELETE FROM budgets
                WHERE id=?
                """,
                (
                    int(selected_id),
                )
            )

            conn.commit()

            st.success(
                "Budget deleted successfully."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Error: {e}"
            )

# =====================================================
# BUDGET PROGRESS
# =====================================================

if not budget_df.empty:

    st.divider()

    st.subheader(
        "📈 Budget Overview"
    )

    max_budget = (
        budget_df["budget"]
        .max()
    )

    for _, row in budget_df.iterrows():

        progress = (
            row["budget"] /
            max_budget
        )

        st.write(
            f"**{row['category']}** — {money(row['budget'])}"
        )

        st.progress(
            float(progress)
        )

# =====================================================
# BUDGET TABLE
# =====================================================

st.divider()

st.subheader(
    "📋 Budget Records"
)

if not budget_df.empty:

    display_df = budget_df.copy()

    display_df["budget"] = (
        display_df["budget"]
        .apply(money)
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        height=450
    )

else:

    st.info(
        "No budgets available."
    )

# =====================================================
# EXPORT
# =====================================================

if not budget_df.empty:

    csv_data = budget_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "📥 Export Budgets",
        csv_data,
        file_name="budgets.csv",
        mime="text/csv"
    )

# =====================================================
# BUDGET TIP
# =====================================================

st.divider()

st.markdown(
    """
    <div style="
    background:linear-gradient(
        135deg,
        #2563EB,
        #7C3AED
    );
    padding:25px;
    border-radius:18px;
    color:white;
    ">
        <h3 style="color:white;">
        💡 Budgeting Tip
        </h3>

        <p>
        Consider the 50/30/20 budgeting rule:

        <br><br>

        • 50% Needs

        <br>

        • 30% Wants

        <br>

        • 20% Savings & Investments

        <br><br>

        Review and adjust your budgets regularly
        as financial circumstances change.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# =====================================================
# CLOSE DATABASE
# =====================================================

conn.close()