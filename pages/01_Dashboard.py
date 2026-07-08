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
    "💰 Financial Health Dashboard",
    "Monitor income, expenses, savings and financial health."
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
# SAFETY
# =====================================================

if "amount" not in income.columns:
    income["amount"] = 0

if "amount" not in expenses.columns:
    expenses["amount"] = 0

# =====================================================
# CALCULATIONS
# =====================================================

total_income = (
    income["amount"].sum()
    if not income.empty
    else 0
)

total_expenses = (
    expenses["amount"].sum()
    if not expenses.empty
    else 0
)

balance = (
    total_income -
    total_expenses
)

savings_rate = (
    (balance / total_income) * 100
    if total_income > 0
    else 0
)

if total_income > 0:

    ratio = (
        total_expenses /
        total_income
    )

    if ratio >= 0.80:

        health_score = 45

    elif ratio >= 0.60:

        health_score = 70

    else:

        health_score = 90

else:

    health_score = 100

# =====================================================
# KPI CARDS
# =====================================================

col1, col2, col3, col4, col5 = st.columns(5)

with col1:

    st.metric(
        "💵 Income",
        money(total_income)
    )

with col2:

    st.metric(
        "💸 Expenses",
        money(total_expenses)
    )

with col3:

    st.metric(
        "🏦 Balance",
        money(balance)
    )

with col4:

    st.metric(
        "📈 Savings Rate",
        f"{savings_rate:.1f}%"
    )

with col5:

    st.metric(
        "❤️ Health Score",
        f"{health_score}/100"
    )

st.divider()

# =====================================================
# OVERVIEW CHARTS
# =====================================================

left_chart, right_chart = st.columns([2, 1])

with left_chart:

    st.subheader(
        "📊 Income vs Expenses"
    )

    compare_df = pd.DataFrame(
        {
            "Category": [
                "Income",
                "Expenses"
            ],
            "Amount": [
                total_income,
                total_expenses
            ]
        }
    )

    fig = px.bar(
        compare_df,
        x="Category",
        y="Amount",
        color="Category",
        color_discrete_map={
            "Income": "#10B981",
            "Expenses": "#EF4444"
        }
    )

    fig.update_layout(
        height=450,
        showlegend=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

with right_chart:

    st.subheader(
        "💹 Financial Score"
    )

    fig = px.pie(
        values=[
            health_score,
            100 - health_score
        ],
        names=[
            "Health",
            "Remaining"
        ],
        hole=0.75
    )

    fig.update_layout(
        height=450
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =====================================================
# EXPENSE ANALYSIS
# =====================================================

if not expenses.empty:

    st.divider()

    left, right = st.columns(2)

    with left:

        st.subheader(
            "🥧 Expense Breakdown"
        )

        expense_categories = (
            expenses
            .groupby("category")["amount"]
            .sum()
            .reset_index()
        )

        fig = px.pie(
            expense_categories,
            names="category",
            values="amount",
            hole=0.65
        )

        fig.update_layout(
            height=450
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with right:

        st.subheader(
            "📉 Spending Trend"
        )

        chart_df = expenses.copy()

        chart_df["date"] = pd.to_datetime(
            chart_df["date"]
        )

        chart_df["month"] = (
            chart_df["date"]
            .dt.strftime("%Y-%m")
        )

        monthly = (
            chart_df
            .groupby("month")["amount"]
            .sum()
            .reset_index()
        )

        fig = px.area(
            monthly,
            x="month",
            y="amount",
            color_discrete_sequence=[
                "#2563EB"
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
# AI FINANCIAL COACH
# =====================================================

st.divider()

st.subheader(
    "🤖 Financial Coach"
)

if savings_rate >= 30:

    advice = """
    Excellent work.

    Your savings rate is strong and spending is under control.

    Continue investing and growing your wealth.
    """

elif savings_rate >= 10:

    advice = """
    Good progress.

    Look for opportunities to increase monthly savings
    and reduce non-essential spending.
    """

else:

    advice = """
    Savings are currently low.

    Focus on reducing discretionary spending
    and increasing income sources.
    """

st.markdown(
    f"""
    <div style="
    background:linear-gradient(
        135deg,
        #2563EB,
        #8B5CF6
    );
    padding:25px;
    border-radius:18px;
    color:white;
    ">
        <h3 style="color:white;">
        Financial Recommendation
        </h3>

        <p>
        {advice}
        </p>

    </div>
    """,
    unsafe_allow_html=True
)

# =====================================================
# RECENT EXPENSES
# =====================================================

st.divider()

st.subheader(
    "📋 Recent Expenses"
)

if not expenses.empty:

    recent_expenses = expenses.copy()

    recent_expenses["date"] = pd.to_datetime(
        recent_expenses["date"]
    )

    recent_expenses = (
        recent_expenses
        .sort_values(
            "date",
            ascending=False
        )
        .head(20)
    )

    st.dataframe(
        recent_expenses,
        use_container_width=True,
        height=400
    )

else:

    st.info(
        "No expenses available."
    )

# =====================================================
# CLOSE DATABASE
# =====================================================

conn.close()