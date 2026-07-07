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
    st.warning("Please login first.")
    st.switch_page("app.py")
    st.stop()

# -------------------------
# PAGE TITLE
# -------------------------
st.title("Financial Health Dashboard")

# -------------------------
# DATABASE
# -------------------------
conn = get_connection()

income = pd.read_sql(
    "SELECT * FROM income",
    conn
)

expenses = pd.read_sql(
    "SELECT * FROM expenses",
    conn
)

# -------------------------
# CALCULATIONS
# -------------------------
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

balance = total_income - total_expenses

savings_rate = (
    (balance / total_income) * 100
    if total_income > 0
    else 0
)

health_score = 100

if total_income > 0:

    ratio = total_expenses / total_income

    if ratio >= 0.8:
        health_score = 45

    elif ratio >= 0.6:
        health_score = 70

    else:
        health_score = 90

# -------------------------
# HEADER
# -------------------------
st.markdown("""
### Welcome Back

Monitor your financial health, savings and spending trends.
""")

# -------------------------
# METRICS
# -------------------------
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Income",
    f"UGX {total_income:,.0f}"
)

col2.metric(
    "Expenses",
    f"UGX {total_expenses:,.0f}"
)

col3.metric(
    "Balance",
    f"UGX {balance:,.0f}"
)

col4.metric(
    "Savings Rate",
    f"{savings_rate:.1f}%"
)

col5.metric(
    "Health Score",
    f"{health_score}/100"
)

# -------------------------
# CHARTS
# -------------------------
if not expenses.empty:

    chart1, chart2 = st.columns(2)

    with chart1:

        st.subheader("Expense Breakdown")

        pie = px.pie(
            expenses,
            names="category",
            values="amount",
            hole=0.65
        )

        pie.update_layout(
            height=400
        )

        st.plotly_chart(
            pie,
            use_container_width=True
        )

    with chart2:

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

        trend = px.area(
            monthly,
            x="month",
            y="amount"
        )

        trend.update_layout(
            title="Monthly Spending Trend",
            height=400
        )

        st.plotly_chart(
            trend,
            use_container_width=True
        )

# -------------------------
# AI FINANCIAL COACH
# -------------------------
st.subheader("AI Financial Coach")

if savings_rate > 30:

    st.success(
        "Excellent savings habits. Your financial health is strong."
    )

elif savings_rate > 10:

    st.info(
        "You are saving consistently. Look for additional savings opportunities."
    )

else:

    st.warning(
        "Savings are low. Consider reducing discretionary expenses."
    )

# -------------------------
# CLOSE CONNECTION
# -------------------------
conn.close()