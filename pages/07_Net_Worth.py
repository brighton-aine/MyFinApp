import streamlit as st
import pandas as pd
import plotly.express as px

from utils import (
    require_login,
    load_css,
    render_sidebar,
    page_header,
    money
)

# =====================================================
# APP SETUP
# =====================================================

load_css()
require_login()
render_sidebar()

page_header(
    "💼 Net Worth Analytics",
    "Measure your overall financial position."
)

# =====================================================
# INPUTS
# =====================================================

st.subheader(
    "🏦 Financial Position"
)

col1, col2 = st.columns(2)

with col1:

    assets = st.number_input(
        "Total Assets (UGX)",
        min_value=0.0,
        value=0.0,
        format="%.2f"
    )

with col2:

    liabilities = st.number_input(
        "Total Liabilities (UGX)",
        min_value=0.0,
        value=0.0,
        format="%.2f"
    )

# =====================================================
# CALCULATIONS
# =====================================================

net_worth = assets - liabilities

if assets > 0:

    health_score = max(
        0,
        min(
            100,
            (net_worth / assets) * 100
        )
    )

else:

    health_score = 0

# =====================================================
# KPI CARDS
# =====================================================

st.divider()

c1, c2, c3 = st.columns(3)

with c1:

    st.metric(
        "🏦 Assets",
        money(assets)
    )

with c2:

    st.metric(
        "📉 Liabilities",
        money(liabilities)
    )

with c3:

    st.metric(
        "💰 Net Worth",
        money(net_worth)
    )

# =====================================================
# STATUS
# =====================================================

st.divider()

if net_worth > 0:

    st.success(
        f"✅ Positive Net Worth: {money(net_worth)}"
    )

elif net_worth < 0:

    st.error(
        f"⚠ Negative Net Worth: {money(abs(net_worth))}"
    )

else:

    st.info(
        "ℹ Net worth is currently zero."
    )

# =====================================================
# CHARTS
# =====================================================

st.divider()

left_chart, right_chart = st.columns(2)

with left_chart:

    st.subheader(
        "📊 Assets vs Liabilities"
    )

    chart_df = pd.DataFrame(
        {
            "Category": [
                "Assets",
                "Liabilities"
            ],
            "Amount": [
                assets,
                liabilities
            ]
        }
    )

    fig = px.bar(
        chart_df,
        x="Category",
        y="Amount",
        color="Category",
        color_discrete_map={
            "Assets": "#10B981",
            "Liabilities": "#EF4444"
        }
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
        "🥧 Wealth Composition"
    )

    fig = px.pie(
        values=[
            assets,
            liabilities
        ],
        names=[
            "Assets",
            "Liabilities"
        ],
        hole=0.70,
        color_discrete_map={
            "Assets": "#10B981",
            "Liabilities": "#EF4444"
        }
    )

    fig.update_layout(
        height=450
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =====================================================
# HEALTH SCORE
# =====================================================

st.divider()

if health_score >= 75:

    health_message = """
    Excellent financial position.
    Assets significantly exceed liabilities.
    """

elif health_score >= 40:

    health_message = """
    Moderate financial position.
    Continue building assets and reducing debt.
    """

else:

    health_message = """
    Financial risk detected.
    Prioritize debt reduction and asset growth.
    """

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
    ❤️ Financial Health Score
    </h3>

    <h1 style="color:white;">
    {health_score:.0f}/100
    </h1>

    <p>
    {health_message}
    </p>

    </div>
    """,
    unsafe_allow_html=True
)

# =====================================================
# BREAKDOWN TABLE
# =====================================================

st.divider()

st.subheader(
    "📋 Net Worth Breakdown"
)

summary_df = pd.DataFrame(
    {
        "Item": [
            "Assets",
            "Liabilities",
            "Net Worth"
        ],
        "Amount": [
            money(assets),
            money(liabilities),
            money(net_worth)
        ]
    }
)

st.dataframe(
    summary_df,
    use_container_width=True,
    hide_index=True
)

# =====================================================
# WEALTH TIP
# =====================================================

st.divider()

st.markdown(
    """
    <div style="
    background:linear-gradient(
        135deg,
        #10B981,
        #059669
    );
    padding:25px;
    border-radius:18px;
    color:white;
    ">

    <h3 style="color:white;">
    💡 Wealth Building Tip
    </h3>

    <p>
    Focus on increasing income-generating assets
    while reducing high-interest liabilities.

    A steadily growing positive net worth is one of
    the strongest indicators of long-term financial success.
    </p>

    </div>
    """,
    unsafe_allow_html=True
)