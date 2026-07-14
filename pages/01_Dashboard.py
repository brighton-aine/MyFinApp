import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
    "Monitor income, expenses, budget performance and financial health."
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

# Budget table — actual schema is `budgets` (plural) with a `budget`
# column; renamed to `amount` here so the rest of this file's logic
# (written against a generic "amount" column) doesn't need to change.
try:
    budget = pd.read_sql(
        "SELECT * FROM budgets",
        conn
    )
    budget = budget.rename(columns={"budget": "amount"})
except Exception:
    budget = pd.DataFrame(columns=["category", "amount"])

# =====================================================
# SAFETY
# =====================================================

if "amount" not in income.columns:
    income["amount"] = 0

if "amount" not in expenses.columns:
    expenses["amount"] = 0

if "category" not in expenses.columns:
    expenses["category"] = "Uncategorized"

if "amount" not in budget.columns:
    budget["amount"] = 0

if "category" not in budget.columns:
    budget["category"] = pd.Series(dtype="object")

# =====================================================
# CALCULATIONS — INCOME / EXPENSES
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
# CALCULATIONS — BUDGET
# =====================================================

has_budget = not budget.empty and budget["amount"].sum() > 0

total_budget = (
    budget["amount"].sum()
    if has_budget
    else 0
)

budget_variance = total_budget - total_expenses  # positive = under budget

budget_utilization = (
    (total_expenses / total_budget) * 100
    if total_budget > 0
    else 0
)

# Per-category budget vs actual
if has_budget and not expenses.empty:

    actual_by_category = (
        expenses
        .groupby("category")["amount"]
        .sum()
        .reset_index()
        .rename(columns={"amount": "Actual"})
    )

    budget_by_category = (
        budget
        .groupby("category")["amount"]
        .sum()
        .reset_index()
        .rename(columns={"amount": "Budget"})
    )

    budget_vs_actual = pd.merge(
        budget_by_category,
        actual_by_category,
        on="category",
        how="outer"
    ).fillna(0)

    budget_vs_actual["Variance"] = (
        budget_vs_actual["Budget"] -
        budget_vs_actual["Actual"]
    )

    budget_vs_actual["Status"] = budget_vs_actual["Variance"].apply(
        lambda v: "Over Budget" if v < 0 else "Under Budget"
    )

else:

    budget_vs_actual = pd.DataFrame(
        columns=["category", "Budget", "Actual", "Variance", "Status"]
    )

# =====================================================
# KPI CARDS
# =====================================================

col1, col2, col3, col4, col5, col6 = st.columns(6)

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

    if has_budget:

        st.metric(
            "🎯 Budget Left",
            money(budget_variance),
            delta=f"{budget_utilization:.0f}% used"
        )

    else:

        st.metric(
            "🎯 Budget Left",
            "No budget set"
        )

with col6:

    st.metric(
        "❤️ Health Score",
        f"{health_score}/100"
    )

st.divider()

# =====================================================
# OVERVIEW CHARTS — INCOME VS EXPENSES
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
        text="Amount",
        color_discrete_map={
            "Income": "#10B981",
            "Expenses": "#EF4444"
        }
    )

    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside"
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
        hole=0.75,
        color_discrete_sequence=["#2563EB", "#E5E7EB"]
    )

    fig.update_layout(
        height=450,
        showlegend=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

st.divider()

# =====================================================
# BUDGET VS EXPENDITURE
# =====================================================

st.subheader(
    "🎯 Budget vs Expenditure"
)

if has_budget:

    budget_left, budget_right = st.columns([2, 1])

    with budget_left:

        st.markdown("**By Category**")

        fig = px.bar(
            budget_vs_actual.sort_values("Budget", ascending=False),
            x="category",
            y=["Budget", "Actual"],
            barmode="group",
            color_discrete_map={
                "Budget": "#8B5CF6",
                "Actual": "#F59E0B"
            }
        )

        fig.update_layout(
            height=420,
            xaxis_title="",
            yaxis_title="Amount",
            legend_title=""
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with budget_right:

        st.markdown("**Overall Utilization**")

        gauge_color = (
            "#EF4444" if budget_utilization > 100
            else "#F59E0B" if budget_utilization > 80
            else "#10B981"
        )

        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=budget_utilization,
                number={"suffix": "%"},
                gauge={
                    "axis": {"range": [0, max(120, budget_utilization + 10)]},
                    "bar": {"color": gauge_color},
                    "steps": [
                        {"range": [0, 80], "color": "#D1FAE5"},
                        {"range": [80, 100], "color": "#FEF3C7"},
                        {"range": [100, max(120, budget_utilization + 10)], "color": "#FEE2E2"}
                    ],
                    "threshold": {
                        "line": {"color": "black", "width": 3},
                        "thickness": 0.8,
                        "value": 100
                    }
                }
            )
        )

        fig.update_layout(height=420)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # Highlight categories over budget
    over_budget = budget_vs_actual[budget_vs_actual["Status"] == "Over Budget"]

    if not over_budget.empty:

        st.markdown("**⚠️ Categories Over Budget**")

        st.dataframe(
            over_budget[["category", "Budget", "Actual", "Variance"]]
            .sort_values("Variance"),
            use_container_width=True,
            hide_index=True
        )

else:

    st.info(
        "No budget data found. Add entries to a `budget` table "
        "(columns: `category`, `amount`) to unlock budget tracking, "
        "utilization, and over/under-budget alerts."
    )

st.divider()

# =====================================================
# EXPENSE ANALYSIS
# =====================================================

if not expenses.empty:

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

    st.divider()

# =====================================================
# AI FINANCIAL COACH
# =====================================================

st.subheader(
    "🤖 Financial Coach"
)

budget_note = ""

if has_budget:

    if budget_utilization > 100:

        budget_note = (
            "\n\n    You're currently over your total budget — "
            "review the categories flagged above first."
        )

    elif budget_utilization > 80:

        budget_note = (
            "\n\n    You're close to your budget limit this period — "
            "keep an eye on discretionary categories."
        )

if savings_rate >= 30:

    advice = (
        "Excellent work.<br><br>"
        "Your savings rate is strong and spending is under control.<br><br>"
        f"Continue investing and growing your wealth.{budget_note}"
    )

elif savings_rate >= 10:

    advice = (
        "Good progress.<br><br>"
        "Look for opportunities to increase monthly savings "
        f"and reduce non-essential spending.{budget_note}"
    )

else:

    advice = (
        "Savings are currently low.<br><br>"
        "Focus on reducing discretionary spending "
        f"and increasing income sources.{budget_note}"
    )

st.markdown(
    f"""
<div style="background:linear-gradient(135deg, #2563EB, #8B5CF6); padding:25px; border-radius:18px; color:white;">
<h3 style="color:white; margin-top:0;">Financial Recommendation</h3>
<p style="color:white; margin-bottom:0;">{advice}</p>
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