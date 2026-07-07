import streamlit as st

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
st.title("💼 Net Worth Calculator")

st.markdown("""
Track your overall financial position by comparing
your total assets and liabilities.
""")

# -------------------------
# INPUTS
# -------------------------
assets = st.number_input(
    "Total Assets (UGX)",
    min_value=0.0,
    value=0.0,
    format="%.2f"
)

liabilities = st.number_input(
    "Total Liabilities (UGX)",
    min_value=0.0,
    value=0.0,
    format="%.2f"
)

# -------------------------
# CALCULATE NET WORTH
# -------------------------
net_worth = assets - liabilities

st.metric(
    "Net Worth",
    f"UGX {net_worth:,.0f}"
)

# -------------------------
# STATUS MESSAGE
# -------------------------
if net_worth > 0:

    st.success(
        f"Your net worth is positive: UGX {net_worth:,.0f}"
    )

elif net_worth < 0:

    st.warning(
        f"Your liabilities exceed your assets by UGX {abs(net_worth):,.0f}"
    )

else:

    st.info(
        "Your net worth is currently zero."
    )

# -------------------------
# BREAKDOWN
# -------------------------
st.subheader("Financial Breakdown")

col1, col2 = st.columns(2)

with col1:

    st.metric(
        "Assets",
        f"UGX {assets:,.0f}"
    )

with col2:

    st.metric(
        "Liabilities",
        f"UGX {liabilities:,.0f}"
    )