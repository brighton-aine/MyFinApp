import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio

# Force a white background on every chart in this app, regardless of
# any dark theme Streamlit might be running under. Without this,
# charts can silently render on a black/dark canvas since none of
# the individual chart calls set their own background explicitly.
pio.templates.default = "plotly_white"

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

if not goals_df.empty:

    goals_df["progress_pct"] = goals_df.apply(
        lambda r: min((r["current"] / r["target"]) * 100, 100)
        if r["target"] > 0
        else 0,
        axis=1
    )

    goals_df["status"] = goals_df["progress_pct"].apply(
        lambda p: "Completed" if p >= 100
        else "On Track" if p >= 50
        else "Just Started"
    )

# =====================================================
# ADD GOAL
#
# Not wrapped in st.form — that would block the live progress
# preview and duplicate-name check below from updating as you type.
# =====================================================

existing_goal_names = (
    set(goals_df["goal_name"].str.lower())
    if not goals_df.empty
    else set()
)

with st.expander(
    "➕ Create New Goal",
    expanded=True
):

    goal_name = st.text_input(
        "Goal Name",
        key="add_goal_name"
    )

    if goal_name.strip() and goal_name.strip().lower() in existing_goal_names:

        st.warning(
            f"You already have a goal named \"{goal_name.strip()}\". "
            "Consider editing that one instead, or use a different name."
        )

    if st.session_state.get("_reset_goal_quick_target"):

        st.session_state["goal_quick_target_choice"] = "Custom amount"
        st.session_state["_reset_goal_quick_target"] = False

    quick_target_options = [
        "Custom amount", "+1,000,000", "+5,000,000", "+10,000,000", "+50,000,000"
    ]

    quick_choice = st.selectbox(
        "⚡ Quick target amount",
        quick_target_options,
        key="goal_quick_target_choice",
        help="Pick a preset to add it to the Target Amount field below."
    )

    if quick_choice != "Custom amount":

        qt_value = int(quick_choice.replace("+", "").replace(",", ""))

        st.session_state["add_goal_target"] = (
            st.session_state.get("add_goal_target", 0.0) + qt_value
        )

        st.session_state["_reset_goal_quick_target"] = True

        st.rerun()

    col1, col2 = st.columns(2)

    with col1:

        target = st.number_input(
            "Target Amount (UGX)",
            min_value=0.0,
            format="%.2f",
            key="add_goal_target"
        )

    with col2:

        current = st.number_input(
            "Current Savings (UGX)",
            min_value=0.0,
            format="%.2f",
            key="add_goal_current"
        )

    if target > 0:

        preview_pct = min((current / target) * 100, 100)

        if current >= target:

            st.caption(
                f"🎉 This goal would already be **100% complete** "
                f"at creation."
            )

        else:

            st.caption(
                f"📊 This goal would start at **{preview_pct:.0f}%** "
                f"complete — {money(target - current)} left to save."
            )

    save_goal = st.button(
        "💾 Save Goal",
        use_container_width=True,
        type="primary"
    )

if save_goal:

    if goal_name.strip() == "":

        st.warning(
            "Please enter a goal name."
        )

    elif target <= 0:

        st.warning(
            "Target amount must be greater than zero."
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
                    goal_name.strip(),
                    target,
                    current
                )
            )

            conn.commit()

            st.session_state["add_goal_name"] = ""
            st.session_state["add_goal_target"] = 0.0
            st.session_state["add_goal_current"] = 0.0

            st.success(
                "Goal saved successfully."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Error: {e}"
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

    overall_progress = (
        (total_saved / total_target) * 100
        if total_target > 0
        else 0
    )

else:

    total_goals = 0
    total_target = 0
    total_saved = 0
    completed_goals = 0
    overall_progress = 0

st.divider()

c1, c2, c3, c4, c5 = st.columns(5)

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
        "📈 Target",
        money(total_target)
    )

with c4:

    st.metric(
        "🏁 Completed",
        completed_goals
    )

with c5:

    st.metric(
        "📊 Overall Progress",
        f"{overall_progress:.1f}%"
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

        chart_df = goals_df.sort_values(
            "progress_pct",
            ascending=True
        )

        fig = px.bar(
            chart_df,
            x="progress_pct",
            y="goal_name",
            orientation="h",
            color="status",
            color_discrete_map={
                "Completed": "#10B981",
                "On Track": "#3B82F6",
                "Just Started": "#F59E0B"
            },
            text="progress_pct"
        )

        fig.update_traces(
            texttemplate="%{text:.0f}%",
            textposition="outside"
        )

        fig.update_layout(
            height=450,
            xaxis_title="Completion %",
            yaxis_title="",
            xaxis_range=[0, 110],
            legend_title=""
        )

        st.plotly_chart(
    fig,
    use_container_width=True,
    theme=None,
    config={"displayModeBar": False}
)

    with right:

        st.subheader(
            "🥧 Savings Distribution"
        )

        fig = px.pie(
            goals_df,
            names="goal_name",
            values="current",
            hole=0.65,
            color_discrete_sequence=px.colors.sequential.Greens_r
        )

        fig.update_layout(
            height=450
        )

        st.plotly_chart(
    fig,
    use_container_width=True,
    theme=None,
    config={"displayModeBar": False}
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
        goals_df["id"],
        format_func=lambda gid: goals_df.loc[
            goals_df["id"] == gid, "goal_name"
        ].values[0]
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
                    "💾 Update",
                    use_container_width=True
                )
            )

        with c2:

            delete_btn = (
                st.form_submit_button(
                    "🗑 Delete",
                    use_container_width=True
                )
            )

    # UPDATE GOAL

    if update_btn:

        if edit_goal_name.strip() == "":

            st.warning(
                "Please enter a goal name."
            )

        elif edit_target <= 0:

            st.warning(
                "Target amount must be greater than zero."
            )

        else:

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
                        edit_goal_name.strip(),
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

else:

    st.info(
        "No goals to edit yet."
    )

# =====================================================
# GOAL PROGRESS
# =====================================================

st.divider()

st.subheader(
    "📈 Goal Progress"
)

if not goals_df.empty:

    status_filter = st.radio(
        "Filter",
        options=["All", "Completed", "On Track", "Just Started"],
        horizontal=True,
        label_visibility="collapsed"
    )

    progress_view = goals_df.sort_values(
        "progress_pct",
        ascending=False
    )

    if status_filter != "All":

        progress_view = progress_view[
            progress_view["status"] == status_filter
        ]

    status_badge = {
        "Completed": "🟢 Completed",
        "On Track": "🔵 On Track",
        "Just Started": "🟡 Just Started"
    }

    if progress_view.empty:

        st.caption(
            f"No goals with status \"{status_filter}\"."
        )

    for _, row in progress_view.iterrows():

        remaining = max(
            row["target"] - row["current"],
            0
        )

        badge = status_badge.get(row["status"], "")

        st.markdown(
            f"### {row['goal_name']} · {badge}"
        )

        gcol1, gcol2, gcol3 = st.columns(3)

        with gcol1:
            st.write(f"Saved: {money(row['current'])}")

        with gcol2:
            st.write(f"Target: {money(row['target'])}")

        with gcol3:
            st.write(
                "Remaining: " +
                (money(remaining) if remaining > 0 else "🎉 Goal reached!")
            )

        st.progress(
            float(row["progress_pct"]) / 100
        )

        st.caption(
            f"{row['progress_pct']:.1f}% Complete"
        )

        st.write("")

# =====================================================
# GOAL RECORDS
# =====================================================

st.divider()

st.subheader(
    "📋 Goal Records"
)

if not goals_df.empty:

    display_df = goals_df.drop(
        columns=["progress_pct"]
    ).copy()

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
        height=500,
        hide_index=True
    )

    # =====================================================
    # EXPORT
    # =====================================================

    csv_data = goals_df.drop(
        columns=["progress_pct"]
    ).to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "📥 Export Goals",
        csv_data,
        file_name="goals.csv",
        mime="text/csv",
        use_container_width=True
    )

else:

    st.info(
        "No goals created yet."
    )

# =====================================================
# MOTIVATION CARD
# =====================================================

st.divider()

if total_goals > 0 and completed_goals == total_goals:

    tip_text = (
        "All your goals are complete — incredible work. "
        "Consider setting a new, bigger goal to keep the momentum going."
    )

elif not goals_df.empty and (goals_df["status"] == "Just Started").sum() > 0:

    tip_text = (
        "Break large goals into smaller milestones. "
        "Contributing consistently every month is "
        "often more effective than waiting for large "
        "one-time savings opportunities."
    )

else:

    tip_text = (
        "Track progress regularly and celebrate milestones along the way — "
        "small, consistent contributions compound into big results."
    )

st.markdown(
    f"""
<div style="background:linear-gradient(135deg, #10B981, #059669); padding:25px; border-radius:18px; color:white;">
<h3 style="color:white; margin-top:0;">🚀 Goal Achievement Tip</h3>
<p style="color:white; margin-bottom:0;">{tip_text}</p>
</div>
    """,
    unsafe_allow_html=True
)

# =====================================================
# CLOSE DATABASE
# =====================================================

conn.close()