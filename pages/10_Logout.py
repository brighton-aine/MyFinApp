import streamlit as st

from utils import (
    load_css,
    render_sidebar
)

# =====================================================
# APP SETUP
# =====================================================

load_css()

# Note: intentionally NOT calling require_login() here — a logout
# page needs to work even when the session is already gone (e.g.
# double-click, browser back button, expired session).

# =====================================================
# ALREADY LOGGED OUT
# =====================================================

current_user = st.session_state.get("user")

if not current_user:

    st.info(
        "You're already logged out."
    )

    if st.button("Go to Login", use_container_width=True):

        st.switch_page("app.py")

    st.stop()

# =====================================================
# LOGOUT CONFIRMATION
# =====================================================

render_sidebar()

st.markdown(
    f"""
    <div style="
    background:linear-gradient(
        135deg,
        #EF4444,
        #DC2626
    );
    padding:25px;
    border-radius:20px;
    color:white;
    margin-bottom:20px;
    ">

        <h2 style="color:white;">
        🚪 Log Out
        </h2>

        <p>
        You are currently logged in as <strong>{current_user}</strong>.
        </p>

    </div>
    """,
    unsafe_allow_html=True
)

st.write(
    "Logging out will end your current session. "
    "You'll need to sign in again to access your data."
)

confirm_logout = st.button(
    "✅ Confirm Logout",
    type="primary",
    use_container_width=True
)

st.caption(
    "Changed your mind? Use the sidebar to go back to any page instead."
)

# =====================================================
# PERFORM LOGOUT
# =====================================================

if confirm_logout:

    for key in list(st.session_state.keys()):

        del st.session_state[key]

    # st.session_state is now empty, so we can't use it to carry a
    # "logged out" message across the page switch below. Query params
    # survive the switch, so app.py can check for this and show a
    # success message there instead:
    #
    #     if st.query_params.get("logged_out") == "true":
    #         st.success("You have been logged out successfully.")
    #         del st.query_params["logged_out"]
    #
    st.query_params["logged_out"] = "true"

    st.switch_page("app.py")