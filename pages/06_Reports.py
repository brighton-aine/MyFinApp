import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

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

from database.db import (
    get_connection,
    create_tables
)

# -------------------------
# SECURITY
# -------------------------
create_tables()

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
st.title("📑 Financial Reports")

# -------------------------
# DATABASE
# -------------------------
conn = get_connection()

# -------------------------
# DATE FILTERS
# -------------------------
col1, col2 = st.columns(2)

with col1:

    start_date = st.date_input(
        "Start Date",
        value=date(date.today().year, 1, 1)
    )

with col2:

    end_date = st.date_input(
        "End Date",
        value=date.today()
    )

# -------------------------
# LOAD DATA
# -------------------------
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
    "SELECT * FROM budgets",
    conn
)

goals = pd.read_sql(
    "SELECT * FROM goals",
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
    balance / total_income * 100
    if total_income > 0
    else 0
)

health_score = 100

if total_income > 0:

    spending_ratio = (
        total_expenses / total_income
    )

    if spending_ratio > 0.80:

        health_score = 45

    elif spending_ratio > 0.60:

        health_score = 70

    else:

        health_score = 90

# -------------------------
# KPI CARDS
# -------------------------
st.subheader("📊 Summary")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "Income",
    f"UGX {total_income:,.0f}"
)

c2.metric(
    "Expenses",
    f"UGX {total_expenses:,.0f}"
)

c3.metric(
    "Balance",
    f"UGX {balance:,.0f}"
)

c4.metric(
    "Savings %",
    f"{savings_rate:.1f}%"
)

c5.metric(
    "Health Score",
    f"{health_score}/100"
)

st.divider()

# -------------------------
# INCOME SUMMARY
# -------------------------
if not income.empty:

    st.subheader(
        "💵 Income by Category"
    )

    income_summary = (
        income
        .groupby("category")["amount"]
        .sum()
        .reset_index()
    )

    st.dataframe(
        income_summary,
        use_container_width=True
    )

# -------------------------
# EXPENSE SUMMARY
# -------------------------
if not expenses.empty:

    st.subheader(
        "💸 Expense by Category"
    )

    expense_summary = (
        expenses
        .groupby("category")["amount"]
        .sum()
        .reset_index()
    )

    st.dataframe(
        expense_summary,
        use_container_width=True
    )

# -------------------------
# PIE CHART
# -------------------------
if not expenses.empty:

    st.subheader(
        "📈 Expense Distribution"
    )

    fig, ax = plt.subplots(
        figsize=(6, 6)
    )

    chart_data = (
        expenses
        .groupby("category")["amount"]
        .sum()
    )

    ax.pie(
        chart_data,
        labels=chart_data.index,
        autopct="%1.1f%%"
    )

    st.pyplot(fig)

# -------------------------
# GOALS
# -------------------------
if not goals.empty:

    st.subheader(
        "🎯 Goal Progress Report"
    )

    st.dataframe(
        goals,
        use_container_width=True
    )

# -------------------------
# BUDGETS
# -------------------------
if not budgets.empty:

    st.subheader(
        "💰 Budget Report"
    )

    st.dataframe(
        budgets,
        use_container_width=True
    )

# -------------------------
# ANNUAL INCOME
# -------------------------
if not income.empty:

    income["date"] = pd.to_datetime(
        income["date"]
    )

    income["year"] = (
        income["date"]
        .dt.year
    )

    annual_income = (
        income
        .groupby("year")["amount"]
        .sum()
        .reset_index()
    )

    st.subheader(
        "📅 Annual Income Summary"
    )

    st.dataframe(
        annual_income,
        use_container_width=True
    )

# -------------------------
# EXCEL EXPORT
# -------------------------
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

# -------------------------
# PDF EXPORT
# -------------------------
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
        f"Total Income: UGX {total_income:,.0f}",
        styles["Normal"]
    )
)

story.append(
    Paragraph(
        f"Total Expenses: UGX {total_expenses:,.0f}",
        styles["Normal"]
    )
)

story.append(
    Paragraph(
        f"Balance: UGX {balance:,.0f}",
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

# -------------------------
# CLOSE CONNECTION
# -------------------------
conn.close()