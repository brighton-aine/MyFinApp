import streamlit as st

st.session_state["user"] = None

for key in list(st.session_state.keys()):
    del st.session_state[key]

st.success(
    "Logged out successfully."
)

st.switch_page("app.py")