import streamlit as st
import pandas as pd
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

if income.empty and expenses.empty:

    st.info(
        "No income or expense records yet. Add some data on the "
        "Income and Expenses pages to unlock forecasting."
    )

    conn.close()

    st.stop()

# =====================================================
# MONTHLY AGGREGATION
# =====================================================

monthly_income = pd.DataFrame(columns=["month", "amount"])
monthly_expenses = pd.DataFrame(columns=["month", "amount"])

if not income.empty:

    income["date"] = pd.to_datetime(income["date"])
    income["month"] = income["date"].dt.strftime("%Y-%m")

    monthly_income = (
        income
        .groupby("month")["amount"]
        .sum()
        .reset_index()
        .sort_values("month")
    )

if not expenses.empty:

    expenses["date"] = pd.to_datetime(expenses["date"])
    expenses["month"] = expenses["date"].dt.strftime("%Y-%m")

    monthly_expenses = (
        expenses
        .groupby("month")["amount"]
        .sum()
        .reset_index()
        .sort_values("month")
    )

# =====================================================
# FORECAST SETTINGS
# =====================================================

st.divider()

settings_col1, settings_col2 = st.columns(2)

with settings_col1:

    horizon = st.select_slider(
        "Forecast horizon (months ahead)",
        options=[1, 3, 6, 12],
        value=3
    )

with settings_col2:

    forecast_method = st.radio(
        "Forecast method",
        options=["Trend-based", "Flat (no growth)"],
        horizontal=True,
        help=(
            "Trend-based estimates a monthly growth rate from your recent "
            "history. Flat simply repeats your recent average with no "
            "growth assumption."
        )
    )

# =====================================================
# FORECAST HELPERS
# =====================================================

GROWTH_CAP = 0.15  # cap estimated monthly growth at +/-15% to avoid
                    # wild projections from a couple of noisy months


def estimate_growth_rate(monthly_df):

    if len(monthly_df) < 2:
        return 0.0

    pct_changes = monthly_df["amount"].pct_change().dropna()

    if pct_changes.empty:
        return 0.0

    rate = pct_changes.mean()

    return max(min(rate, GROWTH_CAP), -GROWTH_CAP)


def trailing_baseline(monthly_df, window=3):

    if monthly_df.empty:
        return 0.0

    return monthly_df["amount"].tail(window).mean()


def build_forecast(monthly_df, horizon_months, growth_rate):
    """Returns (forecast_df, plot_df) where forecast_df has just the
    future months/values, and plot_df prepends the last actual point
    so the forecast line connects visually to the historical line."""

    baseline = trailing_baseline(monthly_df)

    if monthly_df.empty:

        last_period = pd.Period(pd.Timestamp.today(), freq="M")
        last_value = 0.0

    else:

        last_period = pd.Period(monthly_df["month"].max(), freq="M")
        last_value = monthly_df.loc[
            monthly_df["month"] == monthly_df["month"].max(), "amount"
        ].values[0]

    future_months = []
    future_values = []

    for i in range(1, horizon_months + 1):

        period = last_period + i
        value = baseline * ((1 + growth_rate) ** i)

        future_months.append(str(period))
        future_values.append(value)

    forecast_df = pd.DataFrame({
        "month": future_months,
        "amount": future_values
    })

    connector = pd.DataFrame({
        "month": [str(last_period)] if not monthly_df.empty else [],
        "amount": [last_value] if not monthly_df.empty else []
    })

    plot_df = pd.concat([connector, forecast_df], ignore_index=True)

    return forecast_df, plot_df, baseline


income_growth = (
    estimate_growth_rate(monthly_income)
    if forecast_method == "Trend-based"
    else 0.0
)

expense_growth = (
    estimate_growth_rate(monthly_expenses)
    if forecast_method == "Trend-based"
    else 0.0
)

forecast_income_df, income_plot_df, income_baseline = build_forecast(
    monthly_income, horizon, income_growth
)

forecast_expense_df, expense_plot_df, expense_baseline = build_forecast(
    monthly_expenses, horizon, expense_growth
)

# =====================================================
# KPI SECTION
# =====================================================

st.divider()

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.metric(
        "📈 Avg Monthly Income",
        money(income_baseline),
        help="Average of your last 3 months of income."
    )

with c2:

    st.metric(
        "📉 Avg Monthly Expense",
        money(expense_baseline),
        help="Average of your last 3 months of expenses."
    )

with c3:

    st.metric(
        "🔺 Income Growth Rate",
        f"{income_growth * 100:+.1f}% / mo"
    )

with c4:

    st.metric(
        "🔻 Expense Growth Rate",
        f"{expense_growth * 100:+.1f}% / mo"
    )

# =====================================================
# INCOME FORECAST CHART
# =====================================================

if not monthly_income.empty:

    st.divider()

    st.subheader(
        "📈 Income Trend & Forecast"
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=monthly_income["month"],
            y=monthly_income["amount"],
            mode="lines+markers",
            name="Actual",
            line=dict(color="#10B981", width=3)
        )
    )

    fig.add_trace(
        go.Scatter(
            x=income_plot_df["month"],
            y=income_plot_df["amount"],
            mode="lines+markers",
            name="Forecast",
            line=dict(color="#10B981", width=3, dash="dash")
        )
    )

    fig.update_layout(
        height=420,
        xaxis_title="",
        yaxis_title="Amount",
        legend_title=""
    )

    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# EXPENSE FORECAST CHART
# =====================================================

if not monthly_expenses.empty:

    st.subheader(
        "📉 Expense Trend & Forecast"
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=monthly_expenses["month"],
            y=monthly_expenses["amount"],
            mode="lines+markers",
            name="Actual",
            line=dict(color="#EF4444", width=3)
        )
    )

    fig.add_trace(
        go.Scatter(
            x=expense_plot_df["month"],
            y=expense_plot_df["amount"],
            mode="lines+markers",
            name="Forecast",
            line=dict(color="#EF4444", width=3, dash="dash")
        )
    )

    fig.update_layout(
        height=420,
        xaxis_title="",
        yaxis_title="Amount",
        legend_title=""
    )

    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# FORECAST SUMMARY TABLE
# =====================================================

st.divider()

st.subheader(
    "🗓️ Forecast Summary"
)

st.caption(
    "Projected relative to each stream's own most recent recorded month — "
    "\"Month 1\" is the next month after your latest income/expense entry."
)

summary_rows = []

for i in range(horizon):

    month_income = (
        forecast_income_df["amount"].iloc[i]
        if i < len(forecast_income_df)
        else 0
    )

    month_expense = (
        forecast_expense_df["amount"].iloc[i]
        if i < len(forecast_expense_df)
        else 0
    )

    summary_rows.append({
        "Period": f"Month {i + 1}",
        "Forecast Income": money(month_income),
        "Forecast Expense": money(month_expense),
        "Projected Savings": money(month_income - month_expense)
    })

summary_df = pd.DataFrame(summary_rows)

st.dataframe(
    summary_df,
    use_container_width=True,
    hide_index=True
)

# =====================================================
# PROJECTED SAVINGS (NEXT MONTH)
# =====================================================

next_month_income = (
    forecast_income_df["amount"].iloc[0]
    if not forecast_income_df.empty
    else 0
)

next_month_expense = (
    forecast_expense_df["amount"].iloc[0]
    if not forecast_expense_df.empty
    else 0
)

projected_savings = next_month_income - next_month_expense

total_forecast_income = forecast_income_df["amount"].sum()
total_forecast_expense = forecast_expense_df["amount"].sum()
total_projected_savings = total_forecast_income - total_forecast_expense

st.divider()

c1, c2, c3 = st.columns(3)

with c1:

    st.metric(
        "💰 Next Month Savings",
        money(projected_savings)
    )

with c2:

    st.metric(
        f"Total Forecast Income ({horizon}mo)",
        money(total_forecast_income)
    )

with c3:

    st.metric(
        f"Total Forecast Expenses ({horizon}mo)",
        money(total_forecast_expense)
    )

# =====================================================
# OUTLOOK CARD
# =====================================================

st.divider()

if projected_savings > 0:

    card_color = "linear-gradient(135deg, #10B981, #059669)"

    message = (
        "✅ Forecast indicates positive savings next month.<br><br>"
        "Your current financial trend appears healthy and sustainable."
    )

else:

    card_color = "linear-gradient(135deg, #EF4444, #DC2626)"

    message = (
        "⚠ Forecast indicates a potential deficit next month.<br><br>"
        "Consider reducing expenses or increasing income."
    )

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

st.divider()

st.subheader(
    f"💹 Forecast Comparison — Next {horizon} Month(s) Total"
)

comparison = pd.DataFrame(
    {
        "Category": [
            "Forecast Income",
            "Forecast Expense",
            "Projected Savings"
        ],
        "Amount": [
            total_forecast_income,
            total_forecast_expense,
            total_projected_savings
        ]
    }
)

fig = go.Figure(
    go.Bar(
        x=comparison["Category"],
        y=comparison["Amount"],
        marker_color=["#10B981", "#EF4444", "#2563EB"],
        text=comparison["Amount"],
        texttemplate="%{text:,.0f}",
        textposition="outside"
    )
)

fig.update_layout(
    height=420,
    yaxis_title="Amount"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# =====================================================
# FORECAST ADVISOR
# =====================================================

st.divider()

method_note = (
    "using your recent month-over-month growth trend"
    if forecast_method == "Trend-based"
    else "assuming no growth (flat average)"
)

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
        Avg Monthly Income (last 3 months):
        <strong>{money(income_baseline)}</strong>

        <br><br>

        Avg Monthly Expenses (last 3 months):
        <strong>{money(expense_baseline)}</strong>

        <br><br>

        Projected Savings Next Month:
        <strong>{money(projected_savings)}</strong>

        <br><br>

        This forecast was generated {method_note}, projected
        {horizon} month(s) ahead. Use these projections to plan
        budgets, savings goals and future investments — treat them
        as an estimate, not a guarantee.
        </p>

    </div>
    """,
    unsafe_allow_html=True
)

# =====================================================
# CLOSE DATABASE
# =====================================================

conn.close()