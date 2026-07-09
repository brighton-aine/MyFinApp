import streamlit as st
import hashlib
import base64
import os

from database.db import (
    create_tables,
    get_connection
)

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="MyFinApp",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# =====================================================
# HELPERS
# =====================================================

def get_base64_image(path):
    """Read an image from disk and return a base64 string, or None if missing."""
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


logo_base64 = get_base64_image("assets/logo.png")

# =====================================================
# CSS
# =====================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], [class*="st-"] {
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
}

/* Hide Streamlit chrome */
#MainMenu {visibility:hidden;}
header {visibility:hidden;}
footer {visibility:hidden;}
[data-testid="stSidebar"]{ display:none !important; }

/* Page background */
.stApp{
    background: linear-gradient(180deg, #F4F7FA 0%, #EAF0EE 100%);
}

.main .block-container{
    max-width:460px;
    padding-top:56px;
    padding-bottom:40px;
}

/* ---------- Brand block (logo + title + tagline), all in one
   flex container so alignment never drifts ---------- */
.brand-wrapper{
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    text-align:center;
    margin-bottom:6px;
}

/* NOTE: no border-radius here on purpose. The source logo PNG already
   has its corners rounded internally (baked in at export time). Adding
   a second, slightly different border-radius in CSS on top of an
   already-rounded image is what causes thin pale slivers in the
   corners where the two curves don't quite line up. Letting the image's
   own rounding be the only rounding fixes it cleanly. */
.brand-logo{
    width:88px;
    height:88px;
    display:block;
    box-shadow:0 10px 26px rgba(15,76,62,0.28);
    margin-bottom:16px;
}

.brand-logo-fallback{
    width:88px;
    height:88px;
    border-radius:20px;
    background:linear-gradient(135deg,#0F4C3E,#0B3D2E);
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:38px;
    margin-bottom:16px;
    box-shadow:0 10px 26px rgba(15,76,62,0.28);
}

.brand-title{
    font-size:42px;
    font-weight:800;
    color:#0F4C3E;
    line-height:1.1;
    margin:0;
    letter-spacing:-0.5px;
}

.brand-tagline{
    font-size:14px;
    font-weight:700;
    color:#6B8A80;
    margin-top:8px;
    letter-spacing:1.2px;
    text-transform:uppercase;
}

/* ---------- Welcome heading ---------- */
.welcome-title{
    text-align:center;
    font-size:24px;
    font-weight:800;
    color:#0F172A;
    margin-bottom:22px;
}

/* ---------- Card container (native Streamlit bordered container) ---------- */
div[data-testid="stVerticalBlockBorderWrapper"]{
    border-radius:20px !important;
    border:1px solid rgba(15,76,62,0.14) !important;
    box-shadow:0 12px 36px rgba(15,23,42,0.07);
    background:#FFFFFF;
    margin-top:26px;
    padding:8px 6px;
}

/* ---------- Tabs ---------- */
button[data-baseweb="tab"]{
    font-size:16px !important;
    font-weight:700 !important;
    color:#94A3B8 !important;
}
button[data-baseweb="tab"][aria-selected="true"]{
    color:#0F4C3E !important;
}
[data-baseweb="tab-highlight"]{
    background-color:#E7B04A !important;
    height:3px !important;
}
[data-baseweb="tab-border"]{
    background-color:#EDF1F0 !important;
}

/* ---------- Labels ---------- */
.stTextInput label{
    font-size:13px !important;
    font-weight:700 !important;
    color:#334155 !important;
    text-transform:uppercase;
    letter-spacing:0.5px;
}

/* ---------- Inputs ---------- */
.stTextInput input{
    height:52px !important;
    font-size:16px !important;
    border-radius:12px !important;
    border:1.5px solid #E2E8F0 !important;
    background:#F8FAFC !important;
}
.stTextInput input:focus{
    border:1.5px solid #0F4C3E !important;
    box-shadow:0 0 0 3px rgba(15,76,62,0.12) !important;
}

/* ---------- Buttons ---------- */
.stButton button{
    width:100% !important;
    height:54px !important;
    font-size:17px !important;
    font-weight:700 !important;
    border-radius:12px !important;
    border:none !important;
    margin-top:10px;
    background:linear-gradient(135deg, #0F4C3E, #16694F) !important;
    color:#FFFFFF !important;
    transition:all 0.2s ease;
}
.stButton button:hover{
    background:linear-gradient(135deg, #0C3D33, #12563F) !important;
    box-shadow:0 10px 22px rgba(15,76,62,0.32);
    transform:translateY(-1px);
}
.stButton button:active{
    transform:translateY(0);
}

/* ---------- Footer ---------- */
.footer{
    text-align:center;
    color:#94A3B8;
    font-size:13px;
    margin-top:30px;
    letter-spacing:0.3px;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# DATABASE
# =====================================================

create_tables()

conn = get_connection()
cursor = conn.cursor()

# =====================================================
# SESSION
# =====================================================

if "user" not in st.session_state:
    st.session_state["user"] = None

if st.session_state["user"]:
    st.switch_page("pages/01_Dashboard.py")

# =====================================================
# BRAND BLOCK — logo, title, tagline
# Rendered as ONE html block so the logo and text always
# share the same flex container and stay perfectly centered.
# =====================================================

if logo_base64:
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" class="brand-logo" />'
else:
    # Fallback so the page still looks intentional if assets/logo.png is missing
    logo_html = '<div class="brand-logo-fallback">💰</div>'

st.markdown(f"""
<div class="brand-wrapper">
    {logo_html}
    <div class="brand-title">MyFinApp</div>
    <div class="brand-tagline">Track &bull; Save &bull; Budget &bull; Grow</div>
</div>
""", unsafe_allow_html=True)

# =====================================================
# AUTH CARD — welcome heading + login/register tabs
# =====================================================

with st.container(border=True):

    st.markdown(
        '<div class="welcome-title">Welcome Back 👋</div>',
        unsafe_allow_html=True
    )

    tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register"])

    # -------------------------------------------------
    # LOGIN
    # -------------------------------------------------
    with tab_login:

        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Sign In  →", use_container_width=True, key="login_btn"):

            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            user = cursor.execute(
                """
                SELECT *
                FROM users
                WHERE username = ?
                AND password = ?
                """,
                (username, hashed_password)
            ).fetchone()

            if user:
                st.session_state["user"] = username
                st.success(f"Welcome {username}")
                st.switch_page("pages/01_Dashboard.py")
            else:
                st.error("Invalid username or password.")

    # -------------------------------------------------
    # REGISTER
    # -------------------------------------------------
    with tab_register:

        new_user = st.text_input("Username", key="reg_user")
        email = st.text_input("Email", key="reg_email")
        new_password = st.text_input("Password", type="password", key="reg_pass")

        if st.button("Create Account", use_container_width=True, key="reg_btn"):

            try:
                hashed_password = hashlib.sha256(new_password.encode()).hexdigest()

                cursor.execute(
                    """
                    INSERT INTO users
                    (username, email, password)
                    VALUES (?, ?, ?)
                    """,
                    (new_user, email, hashed_password)
                )

                conn.commit()
                st.success("Account created successfully.")

            except Exception:
                st.error("Username or email already exists.")

# =====================================================
# FOOTER
# =====================================================

st.markdown("""
<div class="footer">
MyFinApp © 2026 &bull; Track &bull; Save &bull; Budget &bull; Grow
</div>
""", unsafe_allow_html=True)

conn.close()