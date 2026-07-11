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
    "💸 Expense Management",
    "Track, update and control your spending."
)

# =====================================================
# DATABASE
# =====================================================

conn = get_connection()
cursor = conn.cursor()

# =====================================================
# CATEGORIES
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

expense_df = pd.read_sql(
    """
    SELECT *
    FROM expenses
    ORDER BY id DESC
    """,
    conn
)

if not expense_df.empty:

    expense_df["date"] = pd.to_datetime(
        expense_df["date"]
    )

# Budget table — actual schema is `budgets` (plural) with a `budget`
# column; renamed to `amount` here so the rest of this file's logic
# (written against a generic "amount" column) doesn't need to change.
try:
    budget_df = pd.read_sql(
        "SELECT * FROM budgets",
        conn
    )
    budget_df = budget_df.rename(columns={"budget": "amount"})
except Exception:
    budget_df = pd.DataFrame(columns=["category", "amount"])

has_budget = (
    not budget_df.empty and
    "amount" in budget_df.columns and
    budget_df["amount"].sum() > 0
)

# =====================================================
# ADD EXPENSE
#
# Deliberately NOT wrapped in st.form — a form only reruns on submit,
# which would block the quick-amount buttons, the live "budget
# remaining for this category" hint, and the duplicate check below
# from reacting as you fill the form in.
# =====================================================

if not expense_df.empty:

    default_category = (
        expense_df["category"]
        .value_counts()
        .idxmax()
    )

else:

    default_category = categories[0]

default_category_index = (
    categories.index(default_category)
    if default_category in categories
    else 0
)

today_add = date.today()

if not expense_df.empty:

    this_month_so_far_expense = expense_df[
        (expense_df["date"].dt.month == today_add.month) &
        (expense_df["date"].dt.year == today_add.year)
    ]["amount"].sum()

else:

    this_month_so_far_expense = 0

with st.expander(
    "➕ Add New Expense",
    expanded=True
):

    st.caption(
        f"📅 Logged so far this month: **{money(this_month_so_far_expense)}**"
    )

    st.caption("Quick amounts (tap to add)")

    quick_amounts = [5_000, 10_000, 50_000, 100_000, 500_000]

    quick_cols = st.columns(len(quick_amounts))

    for i, qa in enumerate(quick_amounts):

        with quick_cols[i]:

            if st.button(
                f"+{qa:,.0f}",
                key=f"quick_expense_{qa}",
                use_container_width=True
            ):

                st.session_state["expense_amount_input"] = (
                    st.session_state.get("expense_amount_input", 0.0) + qa
                )

                st.rerun()

    col1, col2 = st.columns(2)

    with col1:

        expense_date = st.date_input(
            "Date",
            value=date.today(),
            key="expense_date_input"
        )

        category = st.selectbox(
            "Category",
            categories,
            index=default_category_index,
            key="expense_category_input"
        )

    with col2:

        description = st.text_input(
            "Description",
            placeholder='e.g. "Rent, July"',
            key="expense_description_input"
        )

        amount = st.number_input(
            "Amount (UGX)",
            min_value=0.0,
            format="%.2f",
            key="expense_amount_input"
        )

    # Live budget context for whichever category is currently selected —
    # this only updates in real time because category lives outside a form.
    if has_budget:

        category_budget = (
            budget_df[budget_df["category"] == category]["amount"].sum()
        )

        if category_budget > 0:

            category_spent_this_month = (
                expense_df[
                    (expense_df["category"] == category) &
                    (expense_df["date"].dt.month == today_add.month) &
                    (expense_df["date"].dt.year == today_add.year)
                ]["amount"].sum()
                if not expense_df.empty
                else 0
            )

            category_remaining = category_budget - category_spent_this_month
            projected_remaining = category_remaining - amount

            if projected_remaining < 0:

                st.warning(
                    f"⚠️ This entry would put **{category}** "
                    f"{money(abs(projected_remaining))} over budget "
                    f"this month (budget: {money(category_budget)})."
                )

            else:

                st.caption(
                    f"🎯 {category} budget remaining after this entry: "
                    f"**{money(projected_remaining)}** of {money(category_budget)}"
                )

    potential_duplicate = False

    if not expense_df.empty and amount > 0:

        potential_duplicate = not expense_df[
            (expense_df["date"] == pd.Timestamp(expense_date)) &
            (expense_df["category"] == category) &
            (expense_df["amount"] == amount)
        ].empty

    if potential_duplicate:

        st.warning(
            "⚠️ A very similar expense (same date, category and amount) "
            "already exists."
        )

    save_col1, save_col2 = st.columns([3, 1])

    with save_col1:

        save_btn = st.button(
            "💾 Save Anyway" if potential_duplicate else "💾 Save Expense",
            use_container_width=True,
            type="primary"
        )

    with save_col2:

        if st.session_state.get("expense_amount_input", 0.0) > 0:

            if st.button("↺ Clear", use_container_width=True):

                st.session_state["expense_amount_input"] = 0.0
                st.rerun()

if save_btn:

    if amount <= 0:

        st.error(
            "Amount must be greater than zero."
        )

    else:

        try:

            cursor.execute(
                """
                INSERT INTO expenses
                (
                    date,
                    category,
                    description,
                    amount
                )
                VALUES
                (
                    ?, ?, ?, ?
                )
                """,
                (
                    str(expense_date),
                    category,
                    description.strip(),
                    amount
                )
            )

            conn.commit()

            st.session_state["expense_amount_input"] = 0.0
            st.session_state["expense_description_input"] = ""

            st.success(
                "Expense added successfully."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Error: {e}"
            )

# =====================================================
# KPI CARDS
# =====================================================

if not expense_df.empty:

    total_expense = (
        expense_df["amount"]
        .sum()
    )

    average_expense = (
        expense_df["amount"]
        .mean()
    )

    highest_expense = (
        expense_df["amount"]
        .max()
    )

    records = len(
        expense_df
    )

    today = pd.Timestamp(
        date.today()
    )

    current_month_df = expense_df[
        (expense_df["date"].dt.month == today.month) &
        (expense_df["date"].dt.year == today.year)
    ]

    this_month_expense = (
        current_month_df["amount"].sum()
        if not current_month_df.empty
        else 0
    )

    last_month = (
        today.month - 1
        if today.month > 1
        else 12
    )

    last_month_year = (
        today.year
        if today.month > 1
        else today.year - 1
    )

    last_month_df = expense_df[
        (expense_df["date"].dt.month == last_month) &
        (expense_df["date"].dt.year == last_month_year)
    ]

    last_month_expense = (
        last_month_df["amount"].sum()
        if not last_month_df.empty
        else 0
    )

    month_over_month = (
        ((this_month_expense - last_month_expense) / last_month_expense) * 100
        if last_month_expense > 0
        else None
    )

    top_category = (
        expense_df
        .groupby("category")["amount"]
        .sum()
        .idxmax()
    )

else:

    total_expense = 0
    average_expense = 0
    highest_expense = 0
    records = 0
    this_month_expense = 0
    month_over_month = None
    top_category = "—"

st.divider()

c1, c2, c3, c4, c5 = st.columns(5)

with c1:

    st.metric(
        "💰 Total Expenses",
        money(total_expense)
    )

with c2:

    st.metric(
        "📅 This Month",
        money(this_month_expense),
        delta=(
            f"{month_over_month:+.1f}% vs last month"
            if month_over_month is not None
            else None
        ),
        delta_color="inverse"
    )

with c3:

    st.metric(
        "📊 Average",
        money(average_expense)
    )

with c4:

    st.metric(
        "⚠ Highest",
        money(highest_expense)
    )

with c5:

    st.metric(
        "🔥 Top Category",
        top_category
    )

# =====================================================
# CHARTS
# =====================================================

if not expense_df.empty:

    st.divider()

    left, right = st.columns(2)

    with left:

        st.subheader(
            "🥧 Expense Breakdown"
        )

        category_chart = (
            expense_df
            .groupby("category")["amount"]
            .sum()
            .reset_index()
            .sort_values("amount", ascending=False)
        )

        fig = px.pie(
            category_chart,
            names="category",
            values="amount",
            hole=0.65,
            color_discrete_sequence=px.colors.sequential.Reds_r
        )

        fig.update_layout(height=420)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with right:

        st.subheader(
            "📉 Monthly Spending Trend"
        )

        trend_df = expense_df.copy()

        trend_df["month"] = (
            trend_df["date"]
            .dt.strftime("%Y-%m")
        )

        trend = (
            trend_df
            .groupby("month")["amount"]
            .sum()
            .reset_index()
            .sort_values("month")
        )

        fig = px.area(
            trend,
            x="month",
            y="amount",
            markers=True,
            color_discrete_sequence=[
                "#EF4444"
            ]
        )

        fig.update_layout(
            height=420,
            xaxis_title="",
            yaxis_title="Amount"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# =====================================================
# BUDGET STATUS BY CATEGORY
# =====================================================

if not expense_df.empty and has_budget:

    st.divider()

    st.subheader(
        "🎯 Budget Status by Category"
    )

    actual_by_cat = (
        expense_df
        .groupby("category")["amount"]
        .sum()
    )

    budget_by_cat = (
        budget_df
        .groupby("category")["amount"]
        .sum()
    )

    all_cats = sorted(
        set(actual_by_cat.index) | set(budget_by_cat.index)
    )

    for cat in all_cats:

        cat_budget = budget_by_cat.get(cat, 0)
        cat_actual = actual_by_cat.get(cat, 0)

        if cat_budget <= 0:
            continue

        pct = min(cat_actual / cat_budget, 1.0)

        bar_color = (
            "🔴" if cat_actual > cat_budget
            else "🟡" if pct > 0.8
            else "🟢"
        )

        st.markdown(
            f"{bar_color} **{cat}** — "
            f"{money(cat_actual)} of {money(cat_budget)} "
            f"({(cat_actual / cat_budget) * 100:.0f}%)"
        )

        st.progress(pct)

# =====================================================
# EDIT / DELETE EXPENSE
# =====================================================

st.divider()

st.subheader(
    "✏️ Edit or Delete Expense"
)

if not expense_df.empty:

    selected_id = st.selectbox(
        "Select Expense Record",
        expense_df["id"]
    )

    selected = expense_df[
        expense_df["id"] == selected_id
    ].iloc[0]

    with st.form(
        "edit_expense_form"
    ):

        edit_date = st.date_input(
            "Date",
            value=pd.to_datetime(
                selected["date"]
            )
        )

        current_category = (
            categories.index(
                selected["category"]
            )
            if selected["category"] in categories
            else 0
        )

        edit_category = st.selectbox(
            "Category",
            categories,
            index=current_category
        )

        edit_description = st.text_input(
            "Description",
            value=selected["description"]
        )

        edit_amount = st.number_input(
            "Amount",
            min_value=0.0,
            value=float(
                selected["amount"]
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

        if edit_amount <= 0:

            st.error(
                "Amount must be greater than zero."
            )

        else:

            try:

                cursor.execute(
                    """
                    UPDATE expenses
                    SET
                        date=?,
                        category=?,
                        description=?,
                        amount=?
                    WHERE id=?
                    """,
                    (
                        str(edit_date),
                        edit_category,
                        edit_description.strip(),
                        edit_amount,
                        int(selected_id)
                    )
                )

                conn.commit()

                st.success(
                    "Expense updated successfully."
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
                DELETE FROM expenses
                WHERE id=?
                """,
                (
                    int(selected_id),
                )
            )

            conn.commit()

            st.success(
                "Expense deleted successfully."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Error: {e}"
            )

else:

    st.info(
        "No expense records to edit yet."
    )

# =====================================================
# FILTERS + RECORDS TABLE
# =====================================================

st.divider()

st.subheader(
    "📋 Expense Records"
)

if not expense_df.empty:

    f1, f2, f3 = st.columns([1, 1, 2])

    with f1:

        min_date = expense_df["date"].min().date()
        max_date = expense_df["date"].max().date()

        date_range = st.date_input(
            "Date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

    with f2:

        category_filter = st.multiselect(
            "Category",
            options=sorted(expense_df["category"].unique()),
            default=[]
        )

    with f3:

        search_term = st.text_input(
            "Search description",
            placeholder="e.g. merchant, receipt #..."
        )

    filtered_df = expense_df.copy()

    if isinstance(date_range, tuple) and len(date_range) == 2:

        start_date, end_date = date_range

        filtered_df = filtered_df[
            (filtered_df["date"].dt.date >= start_date) &
            (filtered_df["date"].dt.date <= end_date)
        ]

    if category_filter:

        filtered_df = filtered_df[
            filtered_df["category"].isin(category_filter)
        ]

    if search_term:

        filtered_df = filtered_df[
            filtered_df["description"]
            .str.contains(search_term, case=False, na=False)
        ]

    st.caption(
        f"Showing {len(filtered_df)} of {len(expense_df)} records "
        f"— total {money(filtered_df['amount'].sum())}"
    )

    display_df = filtered_df.copy()

    display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")

    display_df["amount"] = (
        display_df["amount"]
        .apply(money)
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        height=500,
        hide_index=True
    )

    # =====================================================
    # EXPORT
    # =====================================================

    csv_data = filtered_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "📥 Export Filtered Expenses",
        csv_data,
        file_name="expenses.csv",
        mime="text/csv",
        use_container_width=True
    )

else:

    st.info(
        "No expenses recorded yet."
    )

# =====================================================
# EXPENSE INSIGHT
# =====================================================

if not expense_df.empty:

    st.divider()

    budget_line = ""

    if has_budget:

        top_cat_budget = (
            budget_df[budget_df["category"] == top_category]["amount"].sum()
        )

        top_cat_actual = (
            expense_df[expense_df["category"] == top_category]["amount"].sum()
        )

        if top_cat_budget > 0 and top_cat_actual > top_cat_budget:

            budget_line = (
                f" You've also gone over budget in this category by "
                f"{money(top_cat_actual - top_cat_budget)}."
            )

    st.markdown(
        f"""
        <div style="
        background:linear-gradient(
            135deg,
            #EF4444,
            #F97316
        );
        padding:25px;
        border-radius:18px;
        color:white;
        ">
            <h3 style="color:white;">
            💡 Spending Insight
            </h3>

            <p>
            Your highest spending category is
            <strong>{top_category}</strong>.

            Reviewing this category regularly
            may help improve your savings rate.{budget_line}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

# =====================================================
# CLOSE DATABASE
# =====================================================

conn.close()