import streamlit as st
import pandas as pd
import plotly.express as px

from io import BytesIO
from datetime import date

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import (
    getSampleStyleSheet
)

from utils import (
    require_login,
    load_css,
    render_sidebar,
    page_header,
    money
)

from database.db import (
    get_connection,
    create_tables
)

# =====================================================
# APP SETUP
# =====================================================

load_css()
require_login()
render_sidebar()

page_header(
    "📑 Financial Reports Center",
    "Analyze income, expenses, goals and budgets."
)

# =====================================================
# DATABASE
# =====================================================

create_tables()

conn = get_connection()

# =====================================================
# DATE FILTERS
# =====================================================

st.subheader("📅 Report Period")

col1, col2 = st.columns(2)

with col1:

    start_date = st.date_input(
        "Start Date",
        value=date(
            date.today().year,
            1,
            1
        )
    )

with col2:

    end_date = st.date_input(
        "End Date",
        value=date.today()
    )

# =====================================================
# LOAD DATA
# =====================================================

income = pd.read_sql(
    """
    SELECT *
    FROM income
    WHERE date BETWEEN ? AND ?
    """,
    conn,
    params=[
        str(start_date),
        str(end_date)
    ]
)

expenses = pd.read_sql(
    """
    SELECT *
    FROM expenses
    WHERE date BETWEEN ? AND ?
    """,
    conn,
    params=[
        str(start_date),
        str(end_date)
    ]
)

budgets = pd.read_sql(
    """
    SELECT *
    FROM budgets
    """,
    conn
)

goals = pd.read_sql(
    """
    SELECT *
    FROM goals
    """,
    conn
)

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

health_score = 100

if total_income > 0:

    spending_ratio = (
        total_expenses /
        total_income
    )

    if spending_ratio >= 0.80:

        health_score = 45

    elif spending_ratio >= 0.60:

        health_score = 70

    else:

        health_score = 90

# =====================================================
# KPI CARDS
# =====================================================

st.divider()

c1, c2, c3, c4, c5 = st.columns(5)

with c1:

    st.metric(
        "💵 Income",
        money(total_income)
    )

with c2:

    st.metric(
        "💸 Expenses",
        money(total_expenses)
    )

with c3:

    st.metric(
        "🏦 Balance",
        money(balance)
    )

with c4:

    st.metric(
        "📈 Savings %",
        f"{savings_rate:.1f}%"
    )

with c5:

    st.metric(
        "❤️ Health Score",
        f"{health_score}/100"
    )

# =====================================================
# OVERVIEW CHARTS
# =====================================================

st.divider()

left, right = st.columns(2)

with left:

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
        showlegend=False,
        title="Income vs Expenses"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

with right:

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
        height=450,
        title="Financial Health"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =====================================================
# EXPENSE DISTRIBUTION
# =====================================================

if not expenses.empty:

    st.divider()

    st.subheader(
        "📊 Expense Distribution"
    )

    expense_chart = (
        expenses
        .groupby("category")["amount"]
        .sum()
        .reset_index()
    )

    fig = px.pie(
        expense_chart,
        names="category",
        values="amount",
        hole=0.65
    )

    fig.update_layout(
        height=500
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =====================================================
# MONTHLY EXPENSE TREND
# =====================================================

if not expenses.empty:

    st.divider()

    expenses["date"] = pd.to_datetime(
        expenses["date"]
    )

    monthly_expenses = (
        expenses
        .groupby(
            expenses["date"]
            .dt.strftime("%Y-%m")
        )["amount"]
        .sum()
        .reset_index()
    )

    fig = px.area(
        monthly_expenses,
        x="date",
        y="amount",
        color_discrete_sequence=[
            "#2563EB"
        ]
    )

    fig.update_layout(
        height=450,
        title="Monthly Spending Trend"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =====================================================
# INCOME SUMMARY
# =====================================================

if not income.empty:

    st.divider()

    st.subheader(
        "💵 Income by Category"
    )

    income_summary = (
        income
        .groupby("category")["amount"]
        .sum()
        .reset_index()
    )

    income_summary["amount"] = (
        income_summary["amount"]
        .apply(money)
    )

    st.dataframe(
        income_summary,
        use_container_width=True,
        height=350
    )

# =====================================================
# EXPENSE SUMMARY
# =====================================================

if not expenses.empty:

    st.subheader(
        "💸 Expenses by Category"
    )

    expense_summary = (
        expenses
        .groupby("category")["amount"]
        .sum()
        .reset_index()
    )

    expense_summary["amount"] = (
        expense_summary["amount"]
        .apply(money)
    )

    st.dataframe(
        expense_summary,
        use_container_width=True,
        height=350
    )

# =====================================================
# GOALS REPORT
# =====================================================

if not goals.empty:

    st.divider()

    st.subheader(
        "🎯 Goals Report"
    )

    st.dataframe(
        goals,
        use_container_width=True
    )

# =====================================================
# BUDGET REPORT
# =====================================================

if not budgets.empty:

    st.divider()

    st.subheader(
        "💰 Budget Report"
    )

    st.dataframe(
        budgets,
        use_container_width=True
    )

# =====================================================
# FINANCIAL ADVICE
# =====================================================

st.divider()

if savings_rate >= 30:

    advice = """
    Excellent financial discipline.
    Continue investing and
    growing wealth.
    """

elif savings_rate >= 10:

    advice = """
    Good performance.
    Look for opportunities
    to increase savings.
    """

else:

    advice = """
    Savings are currently low.
    Reduce expenses and
    increase income sources.
    """

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
        🤖 Financial Recommendation
        </h3>

        <p>
        {advice}
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# =====================================================
# EXCEL EXPORT
# =====================================================

st.divider()

excel_buffer = BytesIO()

with pd.ExcelWriter(
    excel_buffer,
    engine="openpyxl"
) as writer:

    income.to_excel(
        writer,
        sheet_name="Income",
        index=False
    )

    expenses.to_excel(
        writer,
        sheet_name="Expenses",
        index=False
    )

    budgets.to_excel(
        writer,
        sheet_name="Budgets",
        index=False
    )

    goals.to_excel(
        writer,
        sheet_name="Goals",
        index=False
    )

st.download_button(
    "📊 Download Excel Report",
    excel_buffer.getvalue(),
    file_name="MyFinApp_Report.xlsx"
)

# =====================================================
# PDF EXPORT
# =====================================================

pdf_buffer = BytesIO()

doc = SimpleDocTemplate(
    pdf_buffer
)

styles = getSampleStyleSheet()

story = []

story.append(
    Paragraph(
        "MyFinApp Financial Report",
        styles["Title"]
    )
)

story.append(
    Spacer(1, 12)
)

story.append(
    Paragraph(
        f"Period: {start_date} to {end_date}",
        styles["Normal"]
    )
)

story.append(
    Paragraph(
        f"Total Income: {money(total_income)}",
        styles["Normal"]
    )
)

story.append(
    Paragraph(
        f"Total Expenses: {money(total_expenses)}",
        styles["Normal"]
    )
)

story.append(
    Paragraph(
        f"Balance: {money(balance)}",
        styles["Normal"]
    )
)

story.append(
    Paragraph(
        f"Savings Rate: {savings_rate:.1f}%",
        styles["Normal"]
    )
)

doc.build(story)

st.download_button(
    "📄 Download PDF Report",
    pdf_buffer.getvalue(),
    file_name="MyFinApp_Report.pdf",
    mime="application/pdf"
)

# =====================================================
# CLOSE CONNECTION
# =====================================================

conn.close()