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
    "💵 Income Management",
    "Manage, update and analyze income records."
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
    "Salary",
    "Bonus",
    "Business",
    "Freelance",
    "Rental Income",
    "Interest",
    "Other"
]

# =====================================================
# ADD INCOME
# =====================================================

with st.expander(
    "➕ Add New Income",
    expanded=True
):

    with st.form("income_form"):

        col1, col2 = st.columns(2)

        with col1:

            income_date = st.date_input(
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

        submit = st.form_submit_button(
            "💾 Save Income"
        )

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
            "Income saved successfully."
        )

        st.rerun()

    except Exception as e:

        st.error(
            f"Error: {e}"
        )

# =====================================================
# LOAD INCOME
# =====================================================

income_df = pd.read_sql(
    """
    SELECT *
    FROM income
    ORDER BY id DESC
    """,
    conn
)

# =====================================================
# KPI CARDS
# =====================================================

if not income_df.empty:

    total_income = (
        income_df["amount"]
        .sum()
    )

    average_income = (
        income_df["amount"]
        .mean()
    )

    highest_income = (
        income_df["amount"]
        .max()
    )

    records = len(
        income_df
    )

else:

    total_income = 0
    average_income = 0
    highest_income = 0
    records = 0

st.divider()

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.metric(
        "💰 Total Income",
        money(total_income)
    )

with c2:

    st.metric(
        "📄 Records",
        records
    )

with c3:

    st.metric(
        "📊 Average",
        money(average_income)
    )

with c4:

    st.metric(
        "🏆 Highest",
        money(highest_income)
    )

# =====================================================
# CHARTS
# =====================================================

if not income_df.empty:

    st.divider()

    left, right = st.columns(2)

    with left:

        st.subheader(
            "Income by Category"
        )

        chart_df = (
            income_df
            .groupby("category")["amount"]
            .sum()
            .reset_index()
        )

        fig = px.pie(
            chart_df,
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
            "Income Trend"
        )

        trend_df = income_df.copy()

        trend_df["date"] = pd.to_datetime(
            trend_df["date"]
        )

        trend = (
            trend_df
            .groupby("date")["amount"]
            .sum()
            .reset_index()
        )

        fig = px.line(
            trend,
            x="date",
            y="amount",
            markers=True
        )

        fig.update_traces(
            line=dict(
                width=4,
                color="#10B981"
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# =====================================================
# EDIT / DELETE SECTION
# =====================================================

st.divider()

st.subheader(
    "✏️ Edit or Delete Income"
)

if not income_df.empty:

    selected_id = st.selectbox(
        "Select Record",
        income_df["id"]
    )

    selected_record = income_df[
        income_df["id"] == selected_id
    ].iloc[0]

    with st.form(
        "edit_income_form"
    ):

        edit_date = st.date_input(
            "Date",
            value=pd.to_datetime(
                selected_record["date"]
            )
        )

        edit_category = st.selectbox(
            "Category",
            categories,
            index=categories.index(
                selected_record["category"]
            )
            if selected_record["category"] in categories
            else 0
        )

        edit_description = st.text_input(
            "Description",
            value=selected_record[
                "description"
            ]
        )

        edit_amount = st.number_input(
            "Amount",
            min_value=0.0,
            value=float(
                selected_record["amount"]
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
                UPDATE income
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
                "Income updated."
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
                DELETE FROM income
                WHERE id=?
                """,
                (
                    int(selected_id),
                )
            )

            conn.commit()

            st.success(
                "Income deleted."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Error: {e}"
            )

# =====================================================
# RECORDS TABLE
# =====================================================

st.divider()

st.subheader(
    "📋 Income Records"
)

if not income_df.empty:

    display_df = income_df.copy()

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
        "No income records available."
    )

# =====================================================
# EXPORT
# =====================================================

if not income_df.empty:

    csv_data = income_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "📥 Export Income",
        csv_data,
        file_name="income.csv",
        mime="text/csv"
    )

# =====================================================
# CLOSE DB
# =====================================================

conn.close()