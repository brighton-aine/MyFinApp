import streamlit as st


def require_login():

    if (
        "user" not in st.session_state
        or st.session_state["user"] is None
    ):

        st.warning(
            "Please login first."
        )

        st.switch_page("app.py")
        st.stop()


def load_css():

    try:

        with open(
            "assets/styles.css",
            encoding="utf-8"
        ) as f:

            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True
            )

    except Exception:
        pass


def render_sidebar():

    with st.sidebar:

        try:

            st.image(
                "assets/logo.png",
                width=90
            )

        except Exception:
            pass

        st.markdown("---")

        if "user" in st.session_state:

            st.success(
                f"👤 {st.session_state['user']}"
            )

        st.markdown("---")

        st.caption(
            "MyFinApp v1.0"
        )


def page_header(
    title,
    subtitle=""
):

    st.markdown(
        f"""
        <div style="
        background:white;
        padding:20px;
        border-radius:20px;
        margin-bottom:20px;
        box-shadow:0 4px 15px rgba(0,0,0,0.08);
        ">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def money(value):

    try:
        return f"UGX {float(value):,.0f}"
    except Exception:
        return "UGX 0"