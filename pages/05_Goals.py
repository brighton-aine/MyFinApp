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
    "🎯 Savings Goals",
    "Create, manage and track financial goals."
)

# =====================================================
# DATABASE
# =====================================================

create_tables()

conn = get_connection()
cursor = conn.cursor()

# =====================================================
# ADD GOAL
# =====================================================

with st.expander(
    "➕ Create New Goal",
    expanded=True
):

    with st.form("goal_form"):

        goal_name = st.text_input(
            "Goal Name"
        )

        col1, col2 = st.columns(2)

        with col1:

            target = st.number_input(
                "Target Amount (UGX)",
                min_value=0.0,
                format="%.2f"
            )

        with col2:

            current = st.number_input(
                "Current Savings (UGX)",
                min_value=0.0,
                format="%.2f"
            )

        save_goal = st.form_submit_button(
            "💾 Save Goal"
        )

if save_goal:

    if goal_name.strip() == "":

        st.warning(
            "Please enter a goal name."
        )

    else:

        try:

            cursor.execute(
                """
                INSERT INTO goals
                (
                    goal_name,
                    target,
                    current
                )
                VALUES
                (
                    ?, ?, ?
                )
                """,
                (
                    goal_name,
                    target,
                    current
                )
            )

            conn.commit()

            st.success(
                "Goal saved successfully."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Error: {e}"
            )

# =====================================================
# LOAD GOALS
# =====================================================

goals_df = pd.read_sql(
    """
    SELECT *
    FROM goals
    ORDER BY id DESC
    """,
    conn
)

# =====================================================
# KPI CARDS
# =====================================================

if not goals_df.empty:

    total_goals = len(
        goals_df
    )

    total_target = (
        goals_df["target"]
        .sum()
    )

    total_saved = (
        goals_df["current"]
        .sum()
    )

    completed_goals = len(
        goals_df[
            goals_df["current"]
            >= goals_df["target"]
        ]
    )

else:

    total_goals = 0
    total_target = 0
    total_saved = 0
    completed_goals = 0

st.divider()

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.metric(
        "🎯 Goals",
        total_goals
    )

with c2:

    st.metric(
        "💰 Saved",
        money(total_saved)
    )

with c3:

    st.metric(
        "🏁 Completed",
        completed_goals
    )

with c4:

    st.metric(
        "📈 Target",
        money(total_target)
    )

# =====================================================
# CHARTS
# =====================================================

if not goals_df.empty:

    st.divider()

    left, right = st.columns(2)

    with left:

        st.subheader(
            "📊 Goal Completion (%)"
        )

        chart_df = goals_df.copy()

        chart_df["progress"] = (
            chart_df["current"]
            /
            chart_df["target"]
            * 100
        )

        chart_df["progress"] = (
            chart_df["progress"]
            .clip(upper=100)
        )

        fig = px.bar(
            chart_df,
            x="goal_name",
            y="progress",
            color="progress",
            color_continuous_scale="Greens"
        )

        fig.update_layout(
            height=450,
            yaxis_title="Completion %"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with right:

        st.subheader(
            "🥧 Savings Distribution"
        )

        fig = px.pie(
            goals_df,
            names="goal_name",
            values="current",
            hole=0.65
        )

        fig.update_layout(
            height=450
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

# =====================================================
# EDIT / DELETE GOAL
# =====================================================

st.divider()

st.subheader(
    "✏️ Edit or Delete Goal"
)

if not goals_df.empty:

    selected_id = st.selectbox(
        "Select Goal",
        goals_df["id"]
    )

    selected_goal = goals_df[
        goals_df["id"] == selected_id
    ].iloc[0]

    with st.form(
        "edit_goal_form"
    ):

        edit_goal_name = st.text_input(
            "Goal Name",
            value=selected_goal[
                "goal_name"
            ]
        )

        col1, col2 = st.columns(2)

        with col1:

            edit_target = st.number_input(
                "Target Amount",
                min_value=0.0,
                value=float(
                    selected_goal[
                        "target"
                    ]
                )
            )

        with col2:

            edit_current = st.number_input(
                "Current Savings",
                min_value=0.0,
                value=float(
                    selected_goal[
                        "current"
                    ]
                )
            )

        c1, c2 = st.columns(2)

        with c1:

            update_btn = (
                st.form_submit_button(
                    "💾 Update"
                )
            )

        with c2:

            delete_btn = (
                st.form_submit_button(
                    "🗑 Delete"
                )
            )

    # UPDATE GOAL

    if update_btn:

        try:

            cursor.execute(
                """
                UPDATE goals
                SET
                    goal_name=?,
                    target=?,
                    current=?
                WHERE id=?
                """,
                (
                    edit_goal_name,
                    edit_target,
                    edit_current,
                    int(selected_id)
                )
            )

            conn.commit()

            st.success(
                "Goal updated successfully."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Error: {e}"
            )

    # DELETE GOAL

    if delete_btn:

        try:

            cursor.execute(
                """
                DELETE FROM goals
                WHERE id=?
                """,
                (
                    int(selected_id),
                )
            )

            conn.commit()

            st.success(
                "Goal deleted successfully."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Error: {e}"
            )

# =====================================================
# GOAL PROGRESS
# =====================================================

st.divider()

st.subheader(
    "📈 Goal Progress"
)

if not goals_df.empty:

    for _, row in goals_df.iterrows():

        progress = 0

        if row["target"] > 0:

            progress = (
                row["current"]
                /
                row["target"]
            )

        progress = min(
            progress,
            1
        )

        percentage = (
            progress * 100
        )

        st.markdown(
            f"### {row['goal_name']}"
        )

        st.write(
            f"Saved: {money(row['current'])}"
        )

        st.write(
            f"Target: {money(row['target'])}"
        )

        st.progress(
            float(progress)
        )

        st.caption(
            f"{percentage:.1f}% Complete"
        )

# =====================================================
# GOAL RECORDS
# =====================================================

st.divider()

st.subheader(
    "📋 Goal Records"
)

if not goals_df.empty:

    display_df = goals_df.copy()

    display_df["target"] = (
        display_df["target"]
        .apply(money)
    )

    display_df["current"] = (
        display_df["current"]
        .apply(money)
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        height=500
    )

else:

    st.info(
        "No goals created yet."
    )

# =====================================================
# EXPORT
# =====================================================

if not goals_df.empty:

    csv_data = goals_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "📥 Export Goals",
        csv_data,
        file_name="goals.csv",
        mime="text/csv"
    )

# =====================================================
# MOTIVATION CARD
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
        🚀 Goal Achievement Tip
        </h3>

        <p>
        Break large goals into smaller milestones.

        Contributing consistently every month is
        often more effective than waiting for large
        one-time savings opportunities.

        Track progress regularly and celebrate
        milestones along the way.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# =====================================================
# CLOSE DATABASE
# =====================================================

conn.close()