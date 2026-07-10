import streamlit as st
import pandas as pd
import plotly.express as px

from io import BytesIO
from datetime import date

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)

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
# DISPLAY FORMATTING HELPERS
# =====================================================

CURRENCY_LIKE_COLUMNS = {
    "amount", "target", "current", "saved", "balance",
    "budget", "spent", "remaining", "limit", "value"
}


def format_numeric_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """Comma-format every numeric column for display. Currency-like
    columns (amount, target, current, etc.) get full money() formatting
    with the currency symbol; other numeric columns (ids, counts) just
    get comma separators, e.g. 1,000,000."""

    display_df = df.copy()

    for col in display_df.columns:

        if pd.api.types.is_numeric_dtype(display_df[col]):

            if str(col).lower() in CURRENCY_LIKE_COLUMNS:

                display_df[col] = display_df[col].apply(
                    lambda v: money(v) if pd.notna(v) else ""
                )

            else:

                display_df[col] = display_df[col].apply(
                    lambda v: f"{v:,.0f}" if pd.notna(v) else ""
                )

    return display_df


# =====================================================
# APP SETUP
# =====================================================

load_css()
require_login()
render_sidebar()

page_header(
    "📑 Financial Reports Center",
    "Analyze income, expenses, goals and budgets."
)

# =====================================================
# DATABASE
# =====================================================

create_tables()

conn = get_connection()

# =====================================================
# DATE FILTERS
# =====================================================

st.subheader("📅 Report Period")

col1, col2 = st.columns(2)

with col1:

    start_date = st.date_input(
        "Start Date",
        value=date(
            date.today().year,
            1,
            1
        )
    )

with col2:

    end_date = st.date_input(
        "End Date",
        value=date.today()
    )

if start_date > end_date:

    st.error(
        "Start date must be before end date."
    )

    st.stop()

# =====================================================
# LOAD DATA
# =====================================================

income = pd.read_sql(
    """
    SELECT *
    FROM income
    WHERE date BETWEEN ? AND ?
    """,
    conn,
    params=[
        str(start_date),
        str(end_date)
    ]
)

expenses = pd.read_sql(
    """
    SELECT *
    FROM expenses
    WHERE date BETWEEN ? AND ?
    """,
    conn,
    params=[
        str(start_date),
        str(end_date)
    ]
)

try:

    budgets = pd.read_sql(
        """
        SELECT *
        FROM budget
        """,
        conn
    )

except Exception:

    budgets = pd.DataFrame(columns=["category", "amount"])

goals = pd.read_sql(
    """
    SELECT *
    FROM goals
    """,
    conn
)

if not income.empty:
    income["date"] = pd.to_datetime(income["date"])

if not expenses.empty:
    expenses["date"] = pd.to_datetime(expenses["date"])

# =====================================================
# CALCULATIONS
# =====================================================

total_income = (
    income["amount"].sum()
    if not income.empty
    else 0
)

total_expenses = (
    expenses["amount"].sum()
    if not expenses.empty
    else 0
)

balance = (
    total_income -
    total_expenses
)

savings_rate = (
    (balance / total_income) * 100
    if total_income > 0
    else 0
)

health_score = 100

if total_income > 0:

    spending_ratio = (
        total_expenses /
        total_income
    )

    if spending_ratio >= 0.80:

        health_score = 45

    elif spending_ratio >= 0.60:

        health_score = 70

    else:

        health_score = 90

if income.empty and expenses.empty:

    st.info(
        "No income or expense records found for this period. "
        "KPIs and charts below will be empty until data is added."
    )

# =====================================================
# KPI CARDS
# =====================================================

st.divider()

c1, c2, c3, c4, c5 = st.columns(5)

with c1:

    st.metric(
        "💵 Income",
        money(total_income)
    )

with c2:

    st.metric(
        "💸 Expenses",
        money(total_expenses)
    )

with c3:

    st.metric(
        "🏦 Balance",
        money(balance)
    )

with c4:

    st.metric(
        "📈 Savings %",
        f"{savings_rate:.1f}%"
    )

with c5:

    st.metric(
        "❤️ Health Score",
        f"{health_score}/100"
    )

# =====================================================
# OVERVIEW CHARTS
# =====================================================

st.divider()

left, right = st.columns(2)

with left:

    compare_df = pd.DataFrame(
        {
            "Category": [
                "Income",
                "Expenses"
            ],
            "Amount": [
                total_income,
                total_expenses
            ]
        }
    )

    fig = px.bar(
        compare_df,
        x="Category",
        y="Amount",
        color="Category",
        text="Amount",
        color_discrete_map={
            "Income": "#10B981",
            "Expenses": "#EF4444"
        }
    )

    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside"
    )

    fig.update_layout(
        height=450,
        showlegend=False,
        title="Income vs Expenses"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

with right:

    fig = px.pie(
        values=[
            health_score,
            100 - health_score
        ],
        names=[
            "Health",
            "Remaining"
        ],
        hole=0.75,
        color_discrete_sequence=["#2563EB", "#E5E7EB"]
    )

    fig.update_layout(
        height=450,
        showlegend=False,
        title="Financial Health"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =====================================================
# EXPENSE DISTRIBUTION
# =====================================================

if not expenses.empty:

    st.divider()

    st.subheader(
        "📊 Expense Distribution"
    )

    expense_chart = (
        expenses
        .groupby("category")["amount"]
        .sum()
        .reset_index()
        .sort_values("amount", ascending=False)
    )

    fig = px.pie(
        expense_chart,
        names="category",
        values="amount",
        hole=0.65,
        color_discrete_sequence=px.colors.sequential.Reds_r
    )

    fig.update_layout(
        height=500
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =====================================================
# MONTHLY EXPENSE TREND
# =====================================================

if not expenses.empty:

    st.divider()

    monthly_expenses = (
        expenses
        .groupby(
            expenses["date"]
            .dt.strftime("%Y-%m")
        )["amount"]
        .sum()
        .reset_index()
        .rename(columns={"date": "month"})
        .sort_values("month")
    )

    fig = px.area(
        monthly_expenses,
        x="month",
        y="amount",
        markers=True,
        color_discrete_sequence=[
            "#2563EB"
        ]
    )

    fig.update_layout(
        height=450,
        title="Monthly Spending Trend",
        xaxis_title="",
        yaxis_title="Amount"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =====================================================
# INCOME SUMMARY
# =====================================================

income_summary = pd.DataFrame()
expense_summary = pd.DataFrame()

if not income.empty:

    st.divider()

    st.subheader(
        "💵 Income by Category"
    )

    income_summary = (
        income
        .groupby("category")["amount"]
        .sum()
        .reset_index()
        .sort_values("amount", ascending=False)
    )

    display_income = income_summary.copy()

    display_income["amount"] = (
        display_income["amount"]
        .apply(money)
    )

    st.dataframe(
        display_income,
        use_container_width=True,
        height=350,
        hide_index=True
    )

# =====================================================
# EXPENSE SUMMARY
# =====================================================

if not expenses.empty:

    st.subheader(
        "💸 Expenses by Category"
    )

    expense_summary = (
        expenses
        .groupby("category")["amount"]
        .sum()
        .reset_index()
        .sort_values("amount", ascending=False)
    )

    display_expense = expense_summary.copy()

    display_expense["amount"] = (
        display_expense["amount"]
        .apply(money)
    )

    st.dataframe(
        display_expense,
        use_container_width=True,
        height=350,
        hide_index=True
    )

# =====================================================
# GOALS REPORT
# =====================================================

if not goals.empty:

    st.divider()

    st.subheader(
        "🎯 Goals Report"
    )

    st.dataframe(
        format_numeric_for_display(goals),
        use_container_width=True,
        hide_index=True
    )

# =====================================================
# BUDGET REPORT
# =====================================================

if not budgets.empty:

    st.divider()

    st.subheader(
        "💰 Budget Report"
    )

    st.dataframe(
        format_numeric_for_display(budgets),
        use_container_width=True,
        hide_index=True
    )

# =====================================================
# FINANCIAL ADVICE
# =====================================================

st.divider()

if savings_rate >= 30:

    advice = """
    Excellent financial discipline.
    Continue investing and
    growing wealth.
    """

elif savings_rate >= 10:

    advice = """
    Good performance.
    Look for opportunities
    to increase savings.
    """

else:

    advice = """
    Savings are currently low.
    Reduce expenses and
    increase income sources.
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
        🤖 Financial Recommendation
        </h3>

        <p>
        {advice}
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# =====================================================
# EXCEL EXPORT
# =====================================================

st.divider()

excel_buffer = BytesIO()

with pd.ExcelWriter(
    excel_buffer,
    engine="openpyxl"
) as writer:

    income.to_excel(
        writer,
        sheet_name="Income",
        index=False
    )

    expenses.to_excel(
        writer,
        sheet_name="Expenses",
        index=False
    )

    budgets.to_excel(
        writer,
        sheet_name="Budgets",
        index=False
    )

    goals.to_excel(
        writer,
        sheet_name="Goals",
        index=False
    )

st.download_button(
    "📊 Download Excel Report",
    excel_buffer.getvalue(),
    file_name="MyFinApp_Report.xlsx",
    use_container_width=True
)

# =====================================================
# PDF EXPORT — STYLED, TABLE-BASED REPORT
# =====================================================

BRAND_BLUE = colors.HexColor("#1D4ED8")
BRAND_PURPLE = colors.HexColor("#7C3AED")
BRAND_GREEN = colors.HexColor("#10B981")
BRAND_RED = colors.HexColor("#EF4444")
BRAND_ORANGE = colors.HexColor("#F59E0B")
BRAND_GRAY = colors.HexColor("#F9FAFB")
BRAND_BORDER = colors.HexColor("#E5E7EB")
BRAND_TEXT_DARK = colors.HexColor("#111827")

base_styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "ReportTitle",
    parent=base_styles["Title"],
    textColor=colors.white,
    alignment=TA_CENTER,
    fontSize=24,
    leading=28,
    spaceAfter=6
)

subtitle_style = ParagraphStyle(
    "ReportSubtitle",
    parent=base_styles["Normal"],
    textColor=colors.HexColor("#DBEAFE"),
    alignment=TA_CENTER,
    fontSize=10,
    leading=14
)

section_style = ParagraphStyle(
    "SectionHeading",
    parent=base_styles["Heading2"],
    textColor=BRAND_TEXT_DARK,
    fontSize=14,
    spaceBefore=18,
    spaceAfter=8
)

cell_style = ParagraphStyle(
    "TableCell",
    parent=base_styles["Normal"],
    fontSize=9,
    leading=12,
    textColor=BRAND_TEXT_DARK
)

header_cell_style = ParagraphStyle(
    "TableHeaderCell",
    parent=base_styles["Normal"],
    fontSize=9,
    leading=12,
    textColor=colors.white,
    fontName="Helvetica-Bold"
)


def styled_table(df: pd.DataFrame, header_color, col_widths=None):
    """Build a reportlab Table from a DataFrame with a colored header
    row, alternating row shading, and wrapped text cells."""

    display_df = df.copy()

    for col in display_df.columns:

        is_numeric = pd.api.types.is_numeric_dtype(df[col])

        if is_numeric and str(col).lower() in CURRENCY_LIKE_COLUMNS:

            display_df[col] = display_df[col].apply(
                lambda v: money(v) if pd.notna(v) else ""
            )

        elif is_numeric:

            display_df[col] = display_df[col].apply(
                lambda v: f"{v:,.0f}" if pd.notna(v) else ""
            )

        else:

            display_df[col] = display_df[col].apply(
                lambda v: "" if pd.isna(v) else str(v)
            )

    header_row = [
        Paragraph(str(c).replace("_", " ").title(), header_cell_style)
        for c in display_df.columns
    ]

    data_rows = [
        [Paragraph(val, cell_style) for val in row]
        for row in display_df.values.tolist()
    ]

    table_data = [header_row] + data_rows

    table = Table(
        table_data,
        colWidths=col_widths,
        repeatRows=1
    )

    style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), header_color),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, BRAND_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]

    for i in range(1, len(table_data)):

        if i % 2 == 0:

            style_commands.append(
                ("BACKGROUND", (0, i), (-1, i), BRAND_GRAY)
            )

    table.setStyle(TableStyle(style_commands))

    return table


pdf_buffer = BytesIO()

doc = SimpleDocTemplate(
    pdf_buffer,
    pagesize=letter,
    topMargin=0.5 * inch,
    bottomMargin=0.6 * inch,
    leftMargin=0.6 * inch,
    rightMargin=0.6 * inch
)

content_width = (
    letter[0] - doc.leftMargin - doc.rightMargin
)

story = []

# ---------- Colored header banner ----------

header_cell_content = [
    Paragraph("MyFinApp Financial Report", title_style),
    Paragraph(
        f"Report Period: {start_date.strftime('%d %b %Y')} "
        f"&ndash; {end_date.strftime('%d %b %Y')}",
        subtitle_style
    ),
    Paragraph(
        f"Generated on {date.today().strftime('%d %b %Y')}",
        subtitle_style
    )
]

header_banner = Table(
    [[header_cell_content]],
    colWidths=[content_width]
)

header_banner.setStyle(
    TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_BLUE),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 22),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 22),
    ])
)

story.append(header_banner)

# Thin accent stripe under the banner for a polished, branded feel
accent_stripe = Table(
    [["", "", ""]],
    colWidths=[content_width / 3] * 3,
    rowHeights=[6]
)

accent_stripe.setStyle(
    TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), BRAND_GREEN),
        ("BACKGROUND", (1, 0), (1, 0), BRAND_ORANGE),
        ("BACKGROUND", (2, 0), (2, 0), BRAND_RED),
    ])
)

story.append(accent_stripe)

story.append(Spacer(1, 20))

# ---------- Summary KPI table ----------

story.append(Paragraph("Summary", section_style))

summary_df = pd.DataFrame({
    "Metric": [
        "Total Income",
        "Total Expenses",
        "Balance",
        "Savings Rate",
        "Health Score"
    ],
    "Value": [
        money(total_income),
        money(total_expenses),
        money(balance),
        f"{savings_rate:.1f}%",
        f"{health_score}/100"
    ]
})

story.append(
    styled_table(
        summary_df,
        BRAND_BLUE,
        col_widths=[content_width * 0.5, content_width * 0.5]
    )
)

# ---------- Income by category ----------

if not income_summary.empty:

    story.append(Paragraph("Income by Category", section_style))

    story.append(
        styled_table(
            income_summary.rename(
                columns={"category": "Category", "amount": "Amount"}
            ),
            BRAND_GREEN,
            col_widths=[content_width * 0.6, content_width * 0.4]
        )
    )

# ---------- Expenses by category ----------

if not expense_summary.empty:

    story.append(Paragraph("Expenses by Category", section_style))

    story.append(
        styled_table(
            expense_summary.rename(
                columns={"category": "Category", "amount": "Amount"}
            ),
            BRAND_RED,
            col_widths=[content_width * 0.6, content_width * 0.4]
        )
    )

# ---------- Budget report ----------

if not budgets.empty:

    story.append(Paragraph("Budget Report", section_style))

    story.append(
        styled_table(budgets, BRAND_PURPLE)
    )

# ---------- Goals report ----------

if not goals.empty:

    story.append(Paragraph("Goals Report", section_style))

    story.append(
        styled_table(goals, BRAND_ORANGE)
    )

# ---------- Recommendation ----------

story.append(Paragraph("Recommendation", section_style))

recommendation_style = ParagraphStyle(
    "Recommendation",
    parent=base_styles["Normal"],
    textColor=colors.white,
    fontSize=11,
    leading=16
)

advice_clean = " ".join(advice.split())

recommendation_box = Table(
    [[Paragraph(advice_clean, recommendation_style)]],
    colWidths=[content_width]
)

recommendation_box.setStyle(
    TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_PURPLE),
        ("TOPPADDING", (0, 0), (-1, -1), 16),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
    ])
)

story.append(recommendation_box)

doc.build(story)

st.download_button(
    "📄 Download PDF Report",
    pdf_buffer.getvalue(),
    file_name="MyFinApp_Report.pdf",
    mime="application/pdf",
    use_container_width=True
)

# =====================================================
# CLOSE CONNECTION
# =====================================================

conn.close()