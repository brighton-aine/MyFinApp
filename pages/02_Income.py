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

    with st.form("income_form", clear_on_submit=True):

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
            "💾 Save Income",
            use_container_width=True
        )

if submit:

    if amount <= 0:

        st.error(
            "Amount must be greater than zero."
        )

    else:

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
                    description.strip(),
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

if not income_df.empty:

    income_df["date"] = pd.to_datetime(
        income_df["date"]
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

    today = pd.Timestamp(
        date.today()
    )

    current_month_df = income_df[
        (income_df["date"].dt.month == today.month) &
        (income_df["date"].dt.year == today.year)
    ]

    this_month_income = (
        current_month_df["amount"].sum()
        if not current_month_df.empty
        else 0
    )

    last_month = (
        today.month - 1
        if today.month > 1
        else 12
    )

    last_month_year = (
        today.year
        if today.month > 1
        else today.year - 1
    )

    last_month_df = income_df[
        (income_df["date"].dt.month == last_month) &
        (income_df["date"].dt.year == last_month_year)
    ]

    last_month_income = (
        last_month_df["amount"].sum()
        if not last_month_df.empty
        else 0
    )

    month_over_month = (
        ((this_month_income - last_month_income) / last_month_income) * 100
        if last_month_income > 0
        else None
    )

    top_category = (
        income_df
        .groupby("category")["amount"]
        .sum()
        .idxmax()
    )

else:

    total_income = 0
    average_income = 0
    highest_income = 0
    records = 0
    this_month_income = 0
    month_over_month = None
    top_category = "—"

st.divider()

c1, c2, c3, c4, c5 = st.columns(5)

with c1:

    st.metric(
        "💰 Total Income",
        money(total_income)
    )

with c2:

    st.metric(
        "📅 This Month",
        money(this_month_income),
        delta=(
            f"{month_over_month:+.1f}% vs last month"
            if month_over_month is not None
            else None
        )
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

with c5:

    st.metric(
        "⭐ Top Category",
        top_category
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
            .sort_values("amount", ascending=False)
        )

        fig = px.pie(
            chart_df,
            names="category",
            values="amount",
            hole=0.65,
            color_discrete_sequence=px.colors.sequential.Greens_r
        )

        fig.update_layout(height=420)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with right:

        st.subheader(
            "Monthly Income Trend"
        )

        trend_df = income_df.copy()

        trend_df["month"] = (
            trend_df["date"]
            .dt.strftime("%Y-%m")
        )

        trend = (
            trend_df
            .groupby("month")["amount"]
            .sum()
            .reset_index()
            .sort_values("month")
        )

        fig = px.bar(
            trend,
            x="month",
            y="amount",
            text="amount"
        )

        fig.update_traces(
            marker_color="#10B981",
            texttemplate="%{text:,.0f}",
            textposition="outside"
        )

        fig.update_layout(
            height=420,
            xaxis_title="",
            yaxis_title="Amount"
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
                    "💾 Update",
                    use_container_width=True
                )
            )

        with col2:

            delete_btn = (
                st.form_submit_button(
                    "🗑 Delete",
                    use_container_width=True
                )
            )

    # UPDATE

    if update_btn:

        if edit_amount <= 0:

            st.error(
                "Amount must be greater than zero."
            )

        else:

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
                        edit_description.strip(),
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

else:

    st.info(
        "No income records to edit yet."
    )

# =====================================================
# FILTERS
# =====================================================

st.divider()

st.subheader(
    "📋 Income Records"
)

if not income_df.empty:

    f1, f2, f3 = st.columns([1, 1, 2])

    with f1:

        min_date = income_df["date"].min().date()
        max_date = income_df["date"].max().date()

        date_range = st.date_input(
            "Date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

    with f2:

        category_filter = st.multiselect(
            "Category",
            options=sorted(income_df["category"].unique()),
            default=[]
        )

    with f3:

        search_term = st.text_input(
            "Search description",
            placeholder="e.g. client name, invoice #..."
        )

    filtered_df = income_df.copy()

    if isinstance(date_range, tuple) and len(date_range) == 2:

        start_date, end_date = date_range

        filtered_df = filtered_df[
            (filtered_df["date"].dt.date >= start_date) &
            (filtered_df["date"].dt.date <= end_date)
        ]

    if category_filter:

        filtered_df = filtered_df[
            filtered_df["category"].isin(category_filter)
        ]

    if search_term:

        filtered_df = filtered_df[
            filtered_df["description"]
            .str.contains(search_term, case=False, na=False)
        ]

    st.caption(
        f"Showing {len(filtered_df)} of {len(income_df)} records "
        f"— total {money(filtered_df['amount'].sum())}"
    )

    display_df = filtered_df.copy()

    display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")

    display_df["amount"] = (
        display_df["amount"]
        .apply(money)
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        height=500,
        hide_index=True
    )

    # =====================================================
    # EXPORT
    # =====================================================

    csv_data = filtered_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "📥 Export Filtered Income",
        csv_data,
        file_name="income.csv",
        mime="text/csv",
        use_container_width=True
    )

else:

    st.info(
        "No income records available."
    )

# =====================================================
# CLOSE DB
# =====================================================

conn.close()