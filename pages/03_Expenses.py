import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

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
    "💸 Expense Management",
    "Track, update and control your spending."
)

# =====================================================
# DATABASE
# =====================================================

conn = get_connection()
cursor = conn.cursor()

# =====================================================
# CATEGORIES
# =====================================================

categories = [
    "Housing",
    "Food",
    "Transport",
    "Utilities",
    "Healthcare",
    "Education",
    "Entertainment",
    "Shopping",
    "Travel",
    "Savings",
    "Other"
]

# =====================================================
# ADD EXPENSE
# =====================================================

with st.expander(
    "➕ Add New Expense",
    expanded=True
):

    with st.form("expense_form"):

        col1, col2 = st.columns(2)

        with col1:

            expense_date = st.date_input(
                "Date",
                value=date.today()
            )

            category = st.selectbox(
                "Category",
                categories
            )

        with col2:

            description = st.text_input(
                "Description"
            )

            amount = st.number_input(
                "Amount (UGX)",
                min_value=0.0,
                format="%.2f"
            )

        save_btn = st.form_submit_button(
            "💾 Save Expense"
        )

if save_btn:

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

        st.rerun()

    except Exception as e:

        st.error(
            f"Error: {e}"
        )

# =====================================================
# LOAD DATA
# =====================================================

expense_df = pd.read_sql(
    """
    SELECT *
    FROM expenses
    ORDER BY id DESC
    """,
    conn
)

# =====================================================
# KPI CARDS
# =====================================================

if not expense_df.empty:

    total_expense = (
        expense_df["amount"]
        .sum()
    )

    average_expense = (
        expense_df["amount"]
        .mean()
    )

    highest_expense = (
        expense_df["amount"]
        .max()
    )

    records = len(
        expense_df
    )

else:

    total_expense = 0
    average_expense = 0
    highest_expense = 0
    records = 0

st.divider()

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.metric(
        "💰 Total Expenses",
        money(total_expense)
    )

with c2:

    st.metric(
        "📄 Records",
        records
    )

with c3:

    st.metric(
        "📊 Average",
        money(average_expense)
    )

with c4:

    st.metric(
        "⚠ Highest",
        money(highest_expense)
    )

# =====================================================
# CHARTS
# =====================================================

if not expense_df.empty:

    st.divider()

    left, right = st.columns(2)

    with left:

        st.subheader(
            "🥧 Expense Breakdown"
        )

        category_chart = (
            expense_df
            .groupby("category")["amount"]
            .sum()
            .reset_index()
        )

        fig = px.pie(
            category_chart,
            names="category",
            values="amount",
            hole=0.65
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with right:

        st.subheader(
            "📉 Spending Trend"
        )

        trend_df = expense_df.copy()

        trend_df["date"] = pd.to_datetime(
            trend_df["date"]
        )

        trend = (
            trend_df
            .groupby("date")["amount"]
            .sum()
            .reset_index()
        )

        fig = px.area(
            trend,
            x="date",
            y="amount",
            color_discrete_sequence=[
                "#EF4444"
            ]
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# =====================================================
# EDIT / DELETE EXPENSE
# =====================================================

st.divider()

st.subheader(
    "✏️ Edit or Delete Expense"
)

if not expense_df.empty:

    selected_id = st.selectbox(
        "Select Expense Record",
        expense_df["id"]
    )

    selected = expense_df[
        expense_df["id"] == selected_id
    ].iloc[0]

    with st.form(
        "edit_expense_form"
    ):

        edit_date = st.date_input(
            "Date",
            value=pd.to_datetime(
                selected["date"]
            )
        )

        current_category = (
            categories.index(
                selected["category"]
            )
            if selected["category"] in categories
            else 0
        )

        edit_category = st.selectbox(
            "Category",
            categories,
            index=current_category
        )

        edit_description = st.text_input(
            "Description",
            value=selected["description"]
        )

        edit_amount = st.number_input(
            "Amount",
            min_value=0.0,
            value=float(
                selected["amount"]
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
                UPDATE expenses
                SET
                    date=?,
                    category=?,
                    description=?,
                    amount=?
                WHERE id=?
                """,
                (
                    str(edit_date),
                    edit_category,
                    edit_description,
                    edit_amount,
                    int(selected_id)
                )
            )

            conn.commit()

            st.success(
                "Expense updated successfully."
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
                DELETE FROM expenses
                WHERE id=?
                """,
                (
                    int(selected_id),
                )
            )

            conn.commit()

            st.success(
                "Expense deleted successfully."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Error: {e}"
            )

# =====================================================
# EXPENSE RECORDS
# =====================================================

st.divider()

st.subheader(
    "📋 Expense Records"
)

if not expense_df.empty:

    display_df = expense_df.copy()

    display_df["amount"] = (
        display_df["amount"]
        .apply(money)
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        height=500
    )

else:

    st.info(
        "No expenses recorded yet."
    )

# =====================================================
# EXPORT
# =====================================================

if not expense_df.empty:

    csv_data = expense_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "📥 Export Expenses",
        csv_data,
        file_name="expenses.csv",
        mime="text/csv"
    )

# =====================================================
# EXPENSE INSIGHT
# =====================================================

if not expense_df.empty:

    st.divider()

    top_category = (
        expense_df
        .groupby("category")["amount"]
        .sum()
        .idxmax()
    )

    st.markdown(
        f"""
        <div style="
        background:linear-gradient(
            135deg,
            #EF4444,
            #F97316
        );
        padding:25px;
        border-radius:18px;
        color:white;
        ">
            <h3 style="color:white;">
            💡 Spending Insight
            </h3>

            <p>
            Your highest spending category is
            <strong>{top_category}</strong>.

            Reviewing this category regularly
            may help improve your savings rate.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

# =====================================================
# CLOSE DATABASE
# =====================================================

conn.close()