import streamlit as st
import pandas as pd
import plotly.express as px

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
st.title("📈 Financial Forecast")

st.markdown("""
Analyze spending trends and estimate future expenses
based on historical data.
""")

# -------------------------
# DATABASE
# -------------------------
conn = get_connection()

expenses = pd.read_sql(
    "SELECT * FROM expenses",
    conn
)

income = pd.read_sql(
    "SELECT * FROM income",
    conn
)

# -------------------------
# EXPENSE FORECAST
# -------------------------
if not expenses.empty:

    expenses["date"] = pd.to_datetime(
        expenses["date"]
    )

    expenses["month"] = (
        expenses["date"]
        .dt.strftime("%Y-%m")
    )

    monthly = (
        expenses
        .groupby("month")["amount"]
        .sum()
        .reset_index()
    )

    average_expense = monthly[
        "amount"
    ].mean()

    forecast_expense = (
        average_expense * 1.05
    )

    st.subheader(
        "Expense Forecast"
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "Average Monthly Spending",
        f"UGX {average_expense:,.0f}"
    )

    col2.metric(
        "Forecast Next Month",
        f"UGX {forecast_expense:,.0f}"
    )

    trend = px.line(
        monthly,
        x="month",
        y="amount",
        markers=True,
        title="Monthly Expense Trend"
    )

    st.plotly_chart(
        trend,
        use_container_width=True
    )

else:

    st.info(
        "Add expense data first."
    )

# -------------------------
# INCOME FORECAST
# -------------------------
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

    avg_income = monthly_income[
        "amount"
    ].mean()

    forecast_income = (
        avg_income * 1.03
    )

    st.subheader(
        "Income Forecast"
    )

    col3, col4 = st.columns(2)

    col3.metric(
        "Average Monthly Income",
        f"UGX {avg_income:,.0f}"
    )

    col4.metric(
        "Forecast Next Month",
        f"UGX {forecast_income:,.0f}"
    )

    income_chart = px.line(
        monthly_income,
        x="month",
        y="amount",
        markers=True,
        title="Monthly Income Trend"
    )

    st.plotly_chart(
        income_chart,
        use_container_width=True
    )

# -------------------------
# FINANCIAL OUTLOOK
# -------------------------
if not income.empty and not expenses.empty:

    projected_savings = (
        forecast_income -
        forecast_expense
    )

    st.subheader(
        "Financial Outlook"
    )

    st.metric(
        "Projected Monthly Savings",
        f"UGX {projected_savings:,.0f}"
    )

    if projected_savings > 0:

        st.success(
            "Your forecast indicates positive savings."
        )

    else:

        st.warning(
            "Your forecast indicates a potential deficit."
        )

# -------------------------
# CLOSE CONNECTION
# -------------------------
conn.close()