import streamlit as st

# Security check
if "user" not in st.session_state:
    st.session_state["user"] = None

if st.session_state["user"] is None:
    st.warning(
        "Please login first."
    )
    st.switch_page("app.py")
    st.stop()

if "user" not in st.session_state:
    st.warning(
        "Please login first."
    )
    st.stop()

st.title("Financial Forecast")

conn = sqlite3.connect("database.db")

expenses = pd.read_sql(
    "SELECT * FROM expenses",
    conn
)

income = pd.read_sql(
    "SELECT * FROM income",
    conn
)

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

    average = monthly["amount"].mean()

    forecast = average * 1.05

    c1, c2 = st.columns(2)

    c1.metric(
        "Average Spending",
        f"UGX {average:,.0f}"
    )

    c2.metric(
        "Forecast Next Month",
        f"UGX {forecast:,.0f}"
    )

    trend = px.line(
        monthly,
        x="month",
        y="amount",
        markers=True
    )

    st.plotly_chart(
        trend,
        use_container_width=True
    )

else:

    st.info(
        "Add expense data first."
    )

conn.close()