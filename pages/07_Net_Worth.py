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
import streamlit as st

st.title("💼 Net Worth")

assets = st.number_input(
    "Total Assets",
    min_value=0.0
)

liabilities = st.number_input(
    "Total Liabilities",
    min_value=0.0
)

networth = assets - liabilities

st.metric(
    "Net Worth",
    f"UGX {networth:,.0f}"
)