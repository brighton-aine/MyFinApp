import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

from utils import (
    require_login,
    load_css,
    render_sidebar,
    page_header,
    money
)

from database.db import (
    get_connection,
    create_tables
)

# =====================================================
# APP SETUP
# =====================================================

load_css()
require_login()
render_sidebar()

page_header(
    "💼 Net Worth Analytics",
    "Track your assets, liabilities, and overall financial position over time."
)

# =====================================================
# DATABASE
# =====================================================

create_tables()

conn = get_connection()
cursor = conn.cursor()

# These tables are specific to this page — created here so the page
# works even if they aren't part of the main create_tables() schema yet.

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        category TEXT,
        name TEXT,
        amount REAL
    )
    """
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS liabilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        category TEXT,
        name TEXT,
        amount REAL
    )
    """
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS net_worth_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT UNIQUE,
        total_assets REAL,
        total_liabilities REAL,
        net_worth REAL
    )
    """
)

conn.commit()

# =====================================================
# CATEGORIES
# =====================================================

asset_categories = [
    "Cash",
    "Bank Savings",
    "Investments",
    "Property",
    "Vehicle",
    "Business",
    "Other"
]

liability_categories = [
    "Mortgage",
    "Loan",
    "Credit Card",
    "Student Loan",
    "Other"
]

# =====================================================
# ADD ASSET / LIABILITY
# =====================================================

add_asset_tab, add_liability_tab = st.tabs(
    ["➕ Add Asset", "➖ Add Liability"]
)

with add_asset_tab:

    with st.form("asset_form", clear_on_submit=True):

        col1, col2 = st.columns(2)

        with col1:

            asset_date = st.date_input(
                "Date",
                value=date.today(),
                key="asset_date"
            )

            asset_category = st.selectbox(
                "Category",
                asset_categories,
                key="asset_category"
            )

        with col2:

            asset_name = st.text_input(
                "Name / Description",
                key="asset_name"
            )

            asset_amount = st.number_input(
                "Amount (UGX)",
                min_value=0.0,
                format="%.2f",
                key="asset_amount"
            )

        save_asset = st.form_submit_button(
            "💾 Save Asset",
            use_container_width=True
        )

    if save_asset:

        if asset_name.strip() == "":

            st.warning(
                "Please enter a name for this asset."
            )

        elif asset_amount <= 0:

            st.warning(
                "Amount must be greater than zero."
            )

        else:

            try:

                cursor.execute(
                    """
                    INSERT INTO assets
                    (date, category, name, amount)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        str(asset_date),
                        asset_category,
                        asset_name.strip(),
                        asset_amount
                    )
                )

                conn.commit()

                st.success("Asset added successfully.")

                st.rerun()

            except Exception as e:

                st.error(f"Error: {e}")

with add_liability_tab:

    with st.form("liability_form", clear_on_submit=True):

        col1, col2 = st.columns(2)

        with col1:

            liability_date = st.date_input(
                "Date",
                value=date.today(),
                key="liability_date"
            )

            liability_category = st.selectbox(
                "Category",
                liability_categories,
                key="liability_category"
            )

        with col2:

            liability_name = st.text_input(
                "Name / Description",
                key="liability_name"
            )

            liability_amount = st.number_input(
                "Amount (UGX)",
                min_value=0.0,
                format="%.2f",
                key="liability_amount"
            )

        save_liability = st.form_submit_button(
            "💾 Save Liability",
            use_container_width=True
        )

    if save_liability:

        if liability_name.strip() == "":

            st.warning(
                "Please enter a name for this liability."
            )

        elif liability_amount <= 0:

            st.warning(
                "Amount must be greater than zero."
            )

        else:

            try:

                cursor.execute(
                    """
                    INSERT INTO liabilities
                    (date, category, name, amount)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        str(liability_date),
                        liability_category,
                        liability_name.strip(),
                        liability_amount
                    )
                )

                conn.commit()

                st.success("Liability added successfully.")

                st.rerun()

            except Exception as e:

                st.error(f"Error: {e}")

# =====================================================
# LOAD DATA
# =====================================================

assets_df = pd.read_sql(
    "SELECT * FROM assets ORDER BY id DESC",
    conn
)

liabilities_df = pd.read_sql(
    "SELECT * FROM liabilities ORDER BY id DESC",
    conn
)

if not assets_df.empty:
    assets_df["date"] = pd.to_datetime(assets_df["date"])

if not liabilities_df.empty:
    liabilities_df["date"] = pd.to_datetime(liabilities_df["date"])

# =====================================================
# CALCULATIONS
# =====================================================

total_assets = (
    assets_df["amount"].sum()
    if not assets_df.empty
    else 0
)

total_liabilities = (
    liabilities_df["amount"].sum()
    if not liabilities_df.empty
    else 0
)

net_worth = total_assets - total_liabilities

if total_assets > 0:

    health_score = max(
        0,
        min(100, (net_worth / total_assets) * 100)
    )

    debt_to_asset = (
        total_liabilities / total_assets
    ) * 100

else:

    health_score = 0
    debt_to_asset = 0

# =====================================================
# KPI CARDS
# =====================================================

st.divider()

c1, c2, c3, c4, c5 = st.columns(5)

with c1:

    st.metric(
        "🏦 Assets",
        money(total_assets)
    )

with c2:

    st.metric(
        "📉 Liabilities",
        money(total_liabilities)
    )

with c3:

    st.metric(
        "💰 Net Worth",
        money(net_worth)
    )

with c4:

    st.metric(
        "⚖️ Debt-to-Asset",
        f"{debt_to_asset:.1f}%"
    )

with c5:

    st.metric(
        "❤️ Health Score",
        f"{health_score:.0f}/100"
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
# SAVE SNAPSHOT
# =====================================================

snap_col1, snap_col2 = st.columns([3, 1])

with snap_col1:

    st.caption(
        "Save today's totals to track how your net worth changes over time."
    )

with snap_col2:

    save_snapshot = st.button(
        "📸 Save Today's Snapshot",
        use_container_width=True
    )

if save_snapshot:

    try:

        cursor.execute(
            """
            INSERT INTO net_worth_history
            (date, total_assets, total_liabilities, net_worth)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                total_assets=excluded.total_assets,
                total_liabilities=excluded.total_liabilities,
                net_worth=excluded.net_worth
            """,
            (
                str(date.today()),
                total_assets,
                total_liabilities,
                net_worth
            )
        )

        conn.commit()

        st.success("Snapshot saved for today.")

        st.rerun()

    except Exception as e:

        st.error(f"Error: {e}")

# =====================================================
# CHARTS — OVERVIEW
# =====================================================

st.divider()

left_chart, right_chart = st.columns(2)

with left_chart:

    st.subheader(
        "📊 Assets vs Liabilities"
    )

    chart_df = pd.DataFrame(
        {
            "Category": ["Assets", "Liabilities"],
            "Amount": [total_assets, total_liabilities]
        }
    )

    fig = px.bar(
        chart_df,
        x="Category",
        y="Amount",
        color="Category",
        text="Amount",
        color_discrete_map={
            "Assets": "#10B981",
            "Liabilities": "#EF4444"
        }
    )

    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside"
    )

    fig.update_layout(
        height=420,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

with right_chart:

    st.subheader(
        "🥧 Wealth Composition"
    )

    fig = px.pie(
        values=[total_assets, total_liabilities],
        names=["Assets", "Liabilities"],
        hole=0.70,
        color=["Assets", "Liabilities"],
        color_discrete_map={
            "Assets": "#10B981",
            "Liabilities": "#EF4444"
        }
    )

    fig.update_layout(height=420)

    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# CHARTS — BREAKDOWN BY CATEGORY
# =====================================================

if not assets_df.empty or not liabilities_df.empty:

    st.divider()

    bleft, bright = st.columns(2)

    with bleft:

        st.subheader(
            "🏦 Assets by Category"
        )

        if not assets_df.empty:

            asset_cat_chart = (
                assets_df
                .groupby("category")["amount"]
                .sum()
                .reset_index()
                .sort_values("amount", ascending=False)
            )

            fig = px.pie(
                asset_cat_chart,
                names="category",
                values="amount",
                hole=0.65,
                color_discrete_sequence=px.colors.sequential.Greens_r
            )

            fig.update_layout(height=400)

            st.plotly_chart(fig, use_container_width=True)

        else:

            st.info("No assets recorded yet.")

    with bright:

        st.subheader(
            "📉 Liabilities by Category"
        )

        if not liabilities_df.empty:

            liab_cat_chart = (
                liabilities_df
                .groupby("category")["amount"]
                .sum()
                .reset_index()
                .sort_values("amount", ascending=False)
            )

            fig = px.pie(
                liab_cat_chart,
                names="category",
                values="amount",
                hole=0.65,
                color_discrete_sequence=px.colors.sequential.Reds_r
            )

            fig.update_layout(height=400)

            st.plotly_chart(fig, use_container_width=True)

        else:

            st.info("No liabilities recorded yet.")

# =====================================================
# NET WORTH TREND
# =====================================================

st.divider()

st.subheader(
    "📈 Net Worth Trend"
)

history_df = pd.read_sql(
    "SELECT * FROM net_worth_history ORDER BY date ASC",
    conn
)

if not history_df.empty:

    history_df["date"] = pd.to_datetime(history_df["date"])

    trend_long = history_df.melt(
        id_vars="date",
        value_vars=["total_assets", "total_liabilities", "net_worth"],
        var_name="Metric",
        value_name="Amount"
    )

    trend_long["Metric"] = trend_long["Metric"].map({
        "total_assets": "Assets",
        "total_liabilities": "Liabilities",
        "net_worth": "Net Worth"
    })

    fig = px.line(
        trend_long,
        x="date",
        y="Amount",
        color="Metric",
        markers=True,
        color_discrete_map={
            "Assets": "#10B981",
            "Liabilities": "#EF4444",
            "Net Worth": "#2563EB"
        }
    )

    fig.update_traces(line=dict(width=3))

    fig.update_layout(
        height=450,
        xaxis_title="",
        yaxis_title="Amount",
        legend_title=""
    )

    st.plotly_chart(fig, use_container_width=True)

else:

    st.info(
        "No snapshots saved yet. Click \"📸 Save Today's Snapshot\" above "
        "to start tracking your net worth trend over time."
    )

# =====================================================
# HEALTH SCORE
# =====================================================

st.divider()

if health_score >= 75:

    health_message = "Excellent financial position. Assets significantly exceed liabilities."

elif health_score >= 40:

    health_message = "Moderate financial position. Continue building assets and reducing debt."

else:

    health_message = "Financial risk detected. Prioritize debt reduction and asset growth."

st.markdown(
    f"""
<div style="background:linear-gradient(135deg, #2563EB, #7C3AED); padding:25px; border-radius:18px; color:white;">
<h3 style="color:white; margin-top:0;">❤️ Financial Health Score</h3>
<h1 style="color:white;">{health_score:.0f}/100</h1>
<p style="color:white; margin-bottom:0;">{health_message}</p>
</div>
    """,
    unsafe_allow_html=True
)

# =====================================================
# EDIT / DELETE
# =====================================================

st.divider()

st.subheader(
    "✏️ Edit or Delete Entries"
)

edit_asset_tab, edit_liability_tab = st.tabs(
    ["🏦 Assets", "📉 Liabilities"]
)

with edit_asset_tab:

    if not assets_df.empty:

        selected_asset_id = st.selectbox(
            "Select Asset",
            assets_df["id"],
            format_func=lambda i: assets_df.loc[
                assets_df["id"] == i, "name"
            ].values[0],
            key="select_asset"
        )

        selected_asset = assets_df[
            assets_df["id"] == selected_asset_id
        ].iloc[0]

        with st.form("edit_asset_form"):

            edit_asset_date = st.date_input(
                "Date",
                value=pd.to_datetime(selected_asset["date"])
            )

            edit_asset_category = st.selectbox(
                "Category",
                asset_categories,
                index=(
                    asset_categories.index(selected_asset["category"])
                    if selected_asset["category"] in asset_categories
                    else 0
                )
            )

            edit_asset_name = st.text_input(
                "Name / Description",
                value=selected_asset["name"]
            )

            edit_asset_amount = st.number_input(
                "Amount",
                min_value=0.0,
                value=float(selected_asset["amount"])
            )

            ac1, ac2 = st.columns(2)

            with ac1:
                update_asset_btn = st.form_submit_button(
                    "💾 Update", use_container_width=True
                )

            with ac2:
                delete_asset_btn = st.form_submit_button(
                    "🗑 Delete", use_container_width=True
                )

        if update_asset_btn:

            if edit_asset_amount <= 0:

                st.error("Amount must be greater than zero.")

            else:

                cursor.execute(
                    """
                    UPDATE assets
                    SET date=?, category=?, name=?, amount=?
                    WHERE id=?
                    """,
                    (
                        str(edit_asset_date),
                        edit_asset_category,
                        edit_asset_name.strip(),
                        edit_asset_amount,
                        int(selected_asset_id)
                    )
                )

                conn.commit()

                st.success("Asset updated.")

                st.rerun()

        if delete_asset_btn:

            cursor.execute(
                "DELETE FROM assets WHERE id=?",
                (int(selected_asset_id),)
            )

            conn.commit()

            st.success("Asset deleted.")

            st.rerun()

    else:

        st.info("No assets to edit yet.")

with edit_liability_tab:

    if not liabilities_df.empty:

        selected_liability_id = st.selectbox(
            "Select Liability",
            liabilities_df["id"],
            format_func=lambda i: liabilities_df.loc[
                liabilities_df["id"] == i, "name"
            ].values[0],
            key="select_liability"
        )

        selected_liability = liabilities_df[
            liabilities_df["id"] == selected_liability_id
        ].iloc[0]

        with st.form("edit_liability_form"):

            edit_liability_date = st.date_input(
                "Date",
                value=pd.to_datetime(selected_liability["date"])
            )

            edit_liability_category = st.selectbox(
                "Category",
                liability_categories,
                index=(
                    liability_categories.index(selected_liability["category"])
                    if selected_liability["category"] in liability_categories
                    else 0
                )
            )

            edit_liability_name = st.text_input(
                "Name / Description",
                value=selected_liability["name"]
            )

            edit_liability_amount = st.number_input(
                "Amount",
                min_value=0.0,
                value=float(selected_liability["amount"])
            )

            lc1, lc2 = st.columns(2)

            with lc1:
                update_liability_btn = st.form_submit_button(
                    "💾 Update", use_container_width=True
                )

            with lc2:
                delete_liability_btn = st.form_submit_button(
                    "🗑 Delete", use_container_width=True
                )

        if update_liability_btn:

            if edit_liability_amount <= 0:

                st.error("Amount must be greater than zero.")

            else:

                cursor.execute(
                    """
                    UPDATE liabilities
                    SET date=?, category=?, name=?, amount=?
                    WHERE id=?
                    """,
                    (
                        str(edit_liability_date),
                        edit_liability_category,
                        edit_liability_name.strip(),
                        edit_liability_amount,
                        int(selected_liability_id)
                    )
                )

                conn.commit()

                st.success("Liability updated.")

                st.rerun()

        if delete_liability_btn:

            cursor.execute(
                "DELETE FROM liabilities WHERE id=?",
                (int(selected_liability_id),)
            )

            conn.commit()

            st.success("Liability deleted.")

            st.rerun()

    else:

        st.info("No liabilities to edit yet.")

# =====================================================
# RECORDS + EXPORT
# =====================================================

st.divider()

st.subheader(
    "📋 Records"
)

records_asset_tab, records_liability_tab = st.tabs(
    ["🏦 Assets", "📉 Liabilities"]
)

with records_asset_tab:

    if not assets_df.empty:

        search_asset = st.text_input(
            "Search assets",
            placeholder="e.g. car, savings account...",
            key="search_asset"
        )

        filtered_assets = assets_df.copy()

        if search_asset:

            filtered_assets = filtered_assets[
                filtered_assets["name"]
                .str.contains(search_asset, case=False, na=False)
            ]

        display_assets = filtered_assets.copy()

        display_assets["date"] = display_assets["date"].dt.strftime("%Y-%m-%d")

        display_assets["amount"] = display_assets["amount"].apply(money)

        st.dataframe(
            display_assets,
            use_container_width=True,
            height=350,
            hide_index=True
        )

        csv_assets = filtered_assets.to_csv(index=False).encode("utf-8")

        st.download_button(
            "📥 Export Assets",
            csv_assets,
            file_name="assets.csv",
            mime="text/csv",
            use_container_width=True
        )

    else:

        st.info("No assets recorded yet.")

with records_liability_tab:

    if not liabilities_df.empty:

        search_liability = st.text_input(
            "Search liabilities",
            placeholder="e.g. mortgage, credit card...",
            key="search_liability"
        )

        filtered_liabilities = liabilities_df.copy()

        if search_liability:

            filtered_liabilities = filtered_liabilities[
                filtered_liabilities["name"]
                .str.contains(search_liability, case=False, na=False)
            ]

        display_liabilities = filtered_liabilities.copy()

        display_liabilities["date"] = (
            display_liabilities["date"].dt.strftime("%Y-%m-%d")
        )

        display_liabilities["amount"] = (
            display_liabilities["amount"].apply(money)
        )

        st.dataframe(
            display_liabilities,
            use_container_width=True,
            height=350,
            hide_index=True
        )

        csv_liabilities = filtered_liabilities.to_csv(index=False).encode("utf-8")

        st.download_button(
            "📥 Export Liabilities",
            csv_liabilities,
            file_name="liabilities.csv",
            mime="text/csv",
            use_container_width=True
        )

    else:

        st.info("No liabilities recorded yet.")

# =====================================================
# WEALTH TIP
# =====================================================

st.divider()

if debt_to_asset > 50:

    wealth_tip = (
        "Your liabilities are a significant share of your assets. "
        "Prioritize paying down high-interest debt before adding new liabilities."
    )

elif total_assets == 0:

    wealth_tip = (
        "Start by logging your assets — even small ones like cash and savings — "
        "to get an accurate baseline for your net worth."
    )

else:

    wealth_tip = (
        "Focus on increasing income-generating assets while reducing "
        "high-interest liabilities. A steadily growing positive net worth "
        "is one of the strongest indicators of long-term financial success."
    )

st.markdown(
    f"""
<div style="background:linear-gradient(135deg, #10B981, #059669); padding:25px; border-radius:18px; color:white;">
<h3 style="color:white; margin-top:0;">💡 Wealth Building Tip</h3>
<p style="color:white; margin-bottom:0;">{wealth_tip}</p>
</div>
    """,
    unsafe_allow_html=True
)

# =====================================================
# CLOSE DATABASE
# =====================================================

conn.close()