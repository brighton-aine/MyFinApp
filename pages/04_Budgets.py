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

from database.db import get_connection

# =====================================================
# APP SETUP
# =====================================================

load_css()
require_login()
render_sidebar()

page_header(
    "💰 Budget Management",
    "Create, update and monitor financial budgets."
)

# =====================================================
# DATABASE
# =====================================================

conn = get_connection()
cursor = conn.cursor()

# =====================================================
# CATEGORIES
#
# Deliberately the SAME list as Expense Management. Budgets used to
# be free-text here, which meant a typo or different casing (e.g.
# "food" vs "Food") would silently break every budget-vs-actual
# comparison elsewhere in the app (Dashboard, Expenses, Reports) —
# those all match on exact category string.
# =====================================================

categories = [
    "Housing",
    "Food",
    "Transport",
    "Utilities",
    "Healthcare",
    "Education",
    "Entertainment",
    "Shopping",
    "Travel",
    "Savings",
    "Other"
]

# =====================================================
# LOAD DATA
# =====================================================

budget_df = pd.read_sql(
    """
    SELECT *
    FROM budgets
    ORDER BY id DESC
    """,
    conn
)

expenses_df = pd.read_sql(
    """
    SELECT *
    FROM expenses
    """,
    conn
)

if not expenses_df.empty:

    expenses_df["date"] = pd.to_datetime(
        expenses_df["date"]
    )

today = date.today()

if not expenses_df.empty:

    this_month_expenses = expenses_df[
        (expenses_df["date"].dt.month == today.month) &
        (expenses_df["date"].dt.year == today.year)
    ]

else:

    this_month_expenses = expenses_df

spent_by_category = (
    this_month_expenses
    .groupby("category")["amount"]
    .sum()
    if not this_month_expenses.empty
    else pd.Series(dtype=float)
)

budgeted_categories = (
    set(budget_df["category"])
    if not budget_df.empty
    else set()
)

# =====================================================
# ADD BUDGET
#
# Not wrapped in st.form, so picking a category live-updates the
# "already spent this month" hint below — useful context for
# deciding what to actually budget.
# =====================================================

with st.expander(
    "➕ Create Budget",
    expanded=True
):

    available_categories = [
        c for c in categories
        if c not in budgeted_categories
    ]

    if not available_categories:

        st.info(
            "Every category already has a budget set. Use "
            "\"Edit or Delete Budget\" below to adjust an existing one."
        )

    else:

        category = st.selectbox(
            "Budget Category",
            available_categories,
            key="add_budget_category"
        )

        category_spent = spent_by_category.get(category, 0)

        if category_spent > 0:

            st.caption(
                f"💡 You've already spent {money(category_spent)} on "
                f"**{category}** this month — consider budgeting at "
                f"least that much."
            )

        budget = st.number_input(
            "Budget Amount (UGX)",
            min_value=0.0,
            format="%.2f",
            key="add_budget_amount"
        )

        save_budget = st.button(
            "💾 Save Budget",
            use_container_width=True,
            type="primary"
        )

        if save_budget:

            if budget <= 0:

                st.warning(
                    "Budget amount must be greater than zero."
                )

            else:

                try:

                    cursor.execute(
                        """
                        INSERT INTO budgets
                        (
                            category,
                            budget
                        )
                        VALUES
                        (
                            ?, ?
                        )
                        """,
                        (
                            category,
                            budget
                        )
                    )

                    conn.commit()

                    st.session_state["add_budget_amount"] = 0.0

                    st.success(
                        "Budget saved successfully."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Error: {e}"
                    )

# =====================================================
# KPI CARDS
# =====================================================

if not budget_df.empty:

    total_budget = (
        budget_df["budget"]
        .sum()
    )

    average_budget = (
        budget_df["budget"]
        .mean()
    )

    highest_budget = (
        budget_df["budget"]
        .max()
    )

    categories_count = len(
        budget_df
    )

    total_spent_this_month = sum(
        spent_by_category.get(cat, 0)
        for cat in budget_df["category"]
    )

    overall_utilization = (
        (total_spent_this_month / total_budget) * 100
        if total_budget > 0
        else 0
    )

else:

    total_budget = 0
    average_budget = 0
    highest_budget = 0
    categories_count = 0
    total_spent_this_month = 0
    overall_utilization = 0

st.divider()

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.metric(
        "💰 Total Budget",
        money(total_budget)
    )

with c2:

    st.metric(
        "📂 Categories",
        categories_count
    )

with c3:

    st.metric(
        "💸 Spent This Month",
        money(total_spent_this_month)
    )

with c4:

    st.metric(
        "🎯 Overall Utilization",
        f"{overall_utilization:.0f}%"
    )

# =====================================================
# CHARTS
# =====================================================

if not budget_df.empty:

    st.divider()

    left, right = st.columns(2)

    with left:

        st.subheader(
            "🥧 Budget Distribution"
        )

        fig = px.pie(
            budget_df,
            names="category",
            values="budget",
            hole=0.65,
            color_discrete_sequence=px.colors.sequential.Purples_r
        )

        fig.update_layout(height=420)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with right:

        st.subheader(
            "📊 Budget vs Actual Spend (This Month)"
        )

        comparison_rows = []

        for _, row in budget_df.iterrows():

            comparison_rows.append({
                "category": row["category"],
                "Budget": row["budget"],
                "Spent": spent_by_category.get(row["category"], 0)
            })

        comparison_df = pd.DataFrame(comparison_rows)

        fig = px.bar(
            comparison_df,
            x="category",
            y=["Budget", "Spent"],
            barmode="group",
            color_discrete_map={
                "Budget": "#8B5CF6",
                "Spent": "#F59E0B"
            }
        )

        fig.update_layout(
            height=420,
            xaxis_title="",
            yaxis_title="Amount",
            legend_title=""
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# =====================================================
# EDIT / DELETE BUDGET
# =====================================================

st.divider()

st.subheader(
    "✏️ Edit or Delete Budget"
)

if not budget_df.empty:

    selected_id = st.selectbox(
        "Select Budget",
        budget_df["id"],
        format_func=lambda i: budget_df.loc[
            budget_df["id"] == i, "category"
        ].values[0]
    )

    selected_budget = budget_df[
        budget_df["id"] == selected_id
    ].iloc[0]

    with st.form(
        "edit_budget_form"
    ):

        edit_category = st.selectbox(
            "Category",
            categories,
            index=(
                categories.index(selected_budget["category"])
                if selected_budget["category"] in categories
                else 0
            )
        )

        edit_budget = st.number_input(
            "Budget Amount",
            min_value=0.0,
            value=float(
                selected_budget[
                    "budget"
                ]
            )
        )

        col1, col2 = st.columns(2)

        with col1:

            update_btn = (
                st.form_submit_button(
                    "💾 Update",
                    use_container_width=True
                )
            )

        with col2:

            delete_btn = (
                st.form_submit_button(
                    "🗑 Delete",
                    use_container_width=True
                )
            )

    # UPDATE

    if update_btn:

        duplicate_category = (
            edit_category != selected_budget["category"]
            and edit_category in budgeted_categories
        )

        if edit_budget <= 0:

            st.error(
                "Budget amount must be greater than zero."
            )

        elif duplicate_category:

            st.error(
                f"\"{edit_category}\" already has a budget. "
                "Edit that one instead, or delete it first."
            )

        else:

            try:

                cursor.execute(
                    """
                    UPDATE budgets
                    SET
                        category=?,
                        budget=?
                    WHERE id=?
                    """,
                    (
                        edit_category,
                        edit_budget,
                        int(selected_id)
                    )
                )

                conn.commit()

                st.success(
                    "Budget updated successfully."
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Error: {e}"
                )

    # DELETE

    if delete_btn:

        try:

            cursor.execute(
                """
                DELETE FROM budgets
                WHERE id=?
                """,
                (
                    int(selected_id),
                )
            )

            conn.commit()

            st.success(
                "Budget deleted successfully."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Error: {e}"
            )

else:

    st.info(
        "No budgets to edit yet."
    )

# =====================================================
# BUDGET PROGRESS — actual spend vs budget, not just
# relative budget size (which is what this used to show)
# =====================================================

if not budget_df.empty:

    st.divider()

    st.subheader(
        "📈 Budget Overview — This Month"
    )

    for _, row in budget_df.iterrows():

        cat = row["category"]
        cat_budget = row["budget"]
        cat_spent = spent_by_category.get(cat, 0)

        progress = (
            min(cat_spent / cat_budget, 1.0)
            if cat_budget > 0
            else 0
        )

        status_icon = (
            "🔴" if cat_spent > cat_budget
            else "🟡" if progress > 0.8
            else "🟢"
        )

        st.write(
            f"{status_icon} **{cat}** — {money(cat_spent)} of "
            f"{money(cat_budget)} spent this month "
            f"({progress * 100:.0f}%)"
        )

        st.progress(
            float(progress)
        )

# =====================================================
# BUDGET TABLE
# =====================================================

st.divider()

st.subheader(
    "📋 Budget Records"
)

if not budget_df.empty:

    display_df = budget_df.copy()

    display_df["Spent This Month"] = display_df["category"].apply(
        lambda c: money(spent_by_category.get(c, 0))
    )

    display_df["budget"] = (
        display_df["budget"]
        .apply(money)
    )

    display_df = display_df.rename(
        columns={"budget": "Budget", "category": "Category"}
    )

    st.dataframe(
        display_df[["Category", "Budget", "Spent This Month"]],
        use_container_width=True,
        height=450,
        hide_index=True
    )

    # =====================================================
    # EXPORT
    # =====================================================

    csv_data = budget_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "📥 Export Budgets",
        csv_data,
        file_name="budgets.csv",
        mime="text/csv",
        use_container_width=True
    )

else:

    st.info(
        "No budgets available."
    )

# =====================================================
# BUDGET TIP
# =====================================================

st.divider()

over_budget_categories = [
    row["category"]
    for _, row in budget_df.iterrows()
    if spent_by_category.get(row["category"], 0) > row["budget"]
] if not budget_df.empty else []

if over_budget_categories:

    tip_text = (
        f"You're currently over budget in "
        f"<strong>{', '.join(over_budget_categories)}</strong> this "
        f"month. Review recent spending in the Expenses page to see "
        f"what's driving it before it compounds next month."
    )

else:

    tip_text = (
        "Consider the 50/30/20 budgeting rule: 50% Needs, 30% Wants, "
        "20% Savings &amp; Investments. Review and adjust your budgets "
        "regularly as circumstances change."
    )

st.markdown(
    f"""
<div style="background:linear-gradient(135deg, #2563EB, #7C3AED); padding:25px; border-radius:18px; color:white;">
<h3 style="color:white; margin-top:0;">💡 Budgeting Tip</h3>
<p style="color:white; margin-bottom:0;">{tip_text}</p>
</div>
    """,
    unsafe_allow_html=True
)

# =====================================================
# CLOSE DATABASE
# =====================================================

conn.close()