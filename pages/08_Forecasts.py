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
    "📈 Financial Forecast Center",
    "Analyze trends and estimate future income, expenses and savings."
)

# =====================================================
# DATABASE
# =====================================================

conn = get_connection()

income = pd.read_sql(
    "SELECT * FROM income",
    conn
)

expenses = pd.read_sql(
    "SELECT * FROM expenses",
    conn
)

# =====================================================
# EXPENSE FORECAST
# =====================================================

forecast_expense = 0
average_expense = 0

if not expenses.empty:

    expenses["date"] = pd.to_datetime(
        expenses["date"]
    )

    expenses["month"] = (
        expenses["date"]
        .dt.strftime("%Y-%m")
    )

    monthly_expenses = (
        expenses
        .groupby("month")["amount"]
        .sum()
        .reset_index()
    )

    average_expense = (
        monthly_expenses["amount"]
        .mean()
    )

    forecast_expense = (
        average_expense * 1.05
    )

# =====================================================
# INCOME FORECAST
# =====================================================

forecast_income = 0
average_income = 0

if not income.empty:

    income["date"] = pd.to_datetime(
        income["date"]
    )

    income["month"] = (
        income["date"]
        .dt.strftime("%Y-%m")
    )

    monthly_income = (
        income
        .groupby("month")["amount"]
        .sum()
        .reset_index()
    )

    average_income = (
        monthly_income["amount"]
        .mean()
    )

    forecast_income = (
        average_income * 1.03
    )

# =====================================================
# KPI SECTION
# =====================================================

st.divider()

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.metric(
        "📉 Avg Expense",
        money(average_expense)
    )

with c2:

    st.metric(
        "📈 Avg Income",
        money(average_income)
    )

with c3:

    st.metric(
        "🔮 Forecast Income",
        money(forecast_income)
    )

with c4:

    st.metric(
        "🔮 Forecast Expense",
        money(forecast_expense)
    )

# =====================================================
# INCOME FORECAST CHART
# =====================================================

if not income.empty:

    st.divider()

    st.subheader(
        "📈 Income Forecast Trend"
    )

    forecast_df = monthly_income.copy()

    next_month = pd.Timestamp.today()

    future_income = pd.DataFrame(
        {
            "month": [
                next_month.strftime(
                    "%Y-%m"
                )
            ],
            "amount": [
                forecast_income
            ]
        }
    )

    forecast_df = pd.concat(
        [
            forecast_df,
            future_income
        ],
        ignore_index=True
    )

    fig = px.line(
        forecast_df,
        x="month",
        y="amount",
        markers=True
    )

    fig.update_traces(
        line=dict(
            width=4,
            color="#10B981"
        )
    )

    fig.update_layout(
        height=450
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =====================================================
# EXPENSE FORECAST CHART
# =====================================================

if not expenses.empty:

    st.subheader(
        "📉 Expense Forecast Trend"
    )

    forecast_exp_df = (
        monthly_expenses.copy()
    )

    next_month = pd.Timestamp.today()

    future_expense = pd.DataFrame(
        {
            "month": [
                next_month.strftime(
                    "%Y-%m"
                )
            ],
            "amount": [
                forecast_expense
            ]
        }
    )

    forecast_exp_df = pd.concat(
        [
            forecast_exp_df,
            future_expense
        ],
        ignore_index=True
    )

    fig = px.area(
        forecast_exp_df,
        x="month",
        y="amount",
        color_discrete_sequence=[
            "#EF4444"
        ]
    )

    fig.update_layout(
        height=450
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =====================================================
# PROJECTED SAVINGS
# =====================================================

projected_savings = (
    forecast_income -
    forecast_expense
)

st.divider()

c1, c2, c3 = st.columns(3)

with c1:

    st.metric(
        "💰 Projected Savings",
        money(projected_savings)
    )

with c2:

    st.metric(
        "Forecast Income",
        money(forecast_income)
    )

with c3:

    st.metric(
        "Forecast Expenses",
        money(forecast_expense)
    )

# =====================================================
# OUTLOOK CARD
# =====================================================

st.divider()

if projected_savings > 0:

    card_color = """
    linear-gradient(
        135deg,
        #10B981,
        #059669
    )
    """

    message = """
    ✅ Forecast indicates positive savings next month.

    Your current financial trend appears healthy and sustainable.
    """

else:

    card_color = """
    linear-gradient(
        135deg,
        #EF4444,
        #DC2626
    )
    """

    message = """
    ⚠ Forecast indicates a potential deficit.

    Consider reducing expenses or increasing income.
    """

st.markdown(
    f"""
    <div style="
    background:{card_color};
    padding:25px;
    border-radius:18px;
    color:white;
    ">
        <h3 style="color:white;">
        Financial Outlook
        </h3>

        <p>
        {message}
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# =====================================================
# FORECAST COMPARISON
# =====================================================

if (
    forecast_income > 0
    or
    forecast_expense > 0
):

    st.divider()

    st.subheader(
        "💹 Forecast Comparison"
    )

    comparison = pd.DataFrame(
        {
            "Category": [
                "Forecast Income",
                "Forecast Expense",
                "Projected Savings"
            ],
            "Amount": [
                forecast_income,
                forecast_expense,
                projected_savings
            ]
        }
    )

    fig = px.bar(
        comparison,
        x="Category",
        y="Amount",
        color="Category",
        color_discrete_map={
            "Forecast Income": "#10B981",
            "Forecast Expense": "#EF4444",
            "Projected Savings": "#2563EB"
        }
    )

    fig.update_layout(
        height=450
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =====================================================
# FORECAST ADVISOR
# =====================================================

st.divider()

st.markdown(
    f"""
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
        🤖 Forecast Advisor
        </h3>

        <p>
        Average Monthly Income:
        <strong>{money(average_income)}</strong>

        <br><br>

        Average Monthly Expenses:
        <strong>{money(average_expense)}</strong>

        <br><br>

        Projected Monthly Savings:
        <strong>{money(projected_savings)}</strong>

        <br><br>

        Use these projections to plan budgets,
        savings goals and future investments.
        </p>

    </div>
    """,
    unsafe_allow_html=True
)

# =====================================================
# CLOSE DATABASE
# =====================================================

conn.close()