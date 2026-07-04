import streamlit as st

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