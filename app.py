"""Supplier Delivery Performance Dashboard.

A compact Streamlit view of supplier metrics and individual purchase-order
records exported from a KNIME Analytics Platform workflow. Synthetic data only.
"""

from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Supplier Delivery Performance Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).resolve().parent
NAVY = "#0A1420"
SLATE = "#172431"
YELLOW = "#F4C95D"
BLUE = "#6299D5"
PALE = "#F5F7FB"
MUTED = "#AAB8C8"
GREY = "#7B8897"

SUMMARY_COLUMNS = [
    "supplier", "total_orders", "avg_delay_days", "avg_fill_rate_percent",
    "high_priority_orders",
]
ORDER_COLUMNS = [
    "order_id", "order_date", "supplier", "part_category", "ordered_qty",
    "delivered_qty", "planned_lead_days", "actual_lead_days",
    "unit_cost_eur", "delivery_delay_days", "fill_rate_percent",
    "issue_priority", "high_priority_flag",
]


@st.cache_data(show_spinner=False)
def load_csv(path: str, modified_ns: int) -> pd.DataFrame:
    """Read the KNIME export and refresh the cache after its file changes."""
    return pd.read_csv(path, encoding="utf-8-sig")


def read_export(name: str, required_columns: list[str]) -> pd.DataFrame:
    path = BASE_DIR / name
    if not path.is_file():
        raise ValueError(f"Missing {name}. Place it in the same folder as app.py.")
    df = load_csv(str(path), path.stat().st_mtime_ns).copy()
    missing = sorted(set(required_columns) - set(df.columns))
    if missing:
        raise ValueError(f"{name} is missing columns: {', '.join(missing)}")
    return df


def require_numbers(df: pd.DataFrame, names: list[str], filename: str) -> None:
    for name in names:
        values = pd.to_numeric(df[name], errors="coerce")
        if not np.isfinite(values.to_numpy(dtype=float)).all():
            raise ValueError(f"{filename}: '{name}' contains a missing or invalid number.")
        df[name] = values


def chart_style(chart: alt.Chart | alt.LayerChart) -> alt.Chart | alt.LayerChart:
    """Apply a restrained dark theme to each Altair chart."""
    return (
        chart.configure_view(stroke=None)
        .configure_axis(
            labelColor=MUTED, titleColor=MUTED, labelFontSize=12,
            titleFontSize=11, gridColor="#2B3745", domain=False,
            tickColor="#2B3745",
        )
        .configure_title(color=PALE)
    )


st.markdown(
    """
    <style>
      .stApp {background: #0A1420; color: #F5F7FB;}
      .block-container {max-width: 1390px; padding-top: 2rem; padding-bottom: 3rem;}
      h1, h2, h3 {color: #F5F7FB; letter-spacing: -0.025em;}
      h2 {font-size: 1.4rem;}
      [data-testid="stHeader"] {background: transparent;}
      [data-testid="stMetric"] {
        background: #172431; border: 1px solid #2A3A4C;
        border-top: 3px solid #F4C95D; border-radius: 10px;
        padding: 1.05rem 1.15rem;
      }
      [data-testid="stMetricLabel"] {color: #BFCAD6;}
      [data-testid="stMetricValue"] {color: #F5F7FB;}
      [data-testid="stVerticalBlockBorderWrapper"]:has(.chart-title) {
        background: #13202D; border-radius: 12px;
      }
      .eyebrow {color:#F4C95D; font-size:.77rem; font-weight:700;
        letter-spacing:.16em; padding-bottom:.45rem;}
      .subtitle {color:#B4C1CF; margin-top:-.25rem; margin-bottom:1.2rem;}
      .divider-line {border-top:1px solid #2A3A4C; margin:1.5rem 0 1.1rem;}
      div.stButton > button[kind="primary"] {background:#F4C95D; color:#0A1420;}
      .small-note {color:#AAB8C8; font-size:.86rem;}
    </style>
    <div class="eyebrow">SUPPLIER ANALYTICS / KNIME</div>
    """,
    unsafe_allow_html=True,
)
st.title("Delivery Performance Dashboard")
st.markdown(
    '<div class="subtitle">Purchase-order reliability, supplier comparisons, and delivery issues</div>',
    unsafe_allow_html=True,
)

try:
    summary = read_export("supplier_summary.csv", SUMMARY_COLUMNS)
    orders = read_export("supplier_orders_scored.csv", ORDER_COLUMNS)
    require_numbers(summary, SUMMARY_COLUMNS[1:], "supplier_summary.csv")
    require_numbers(
        orders,
        ["ordered_qty", "delivered_qty", "planned_lead_days", "actual_lead_days",
         "unit_cost_eur", "delivery_delay_days", "fill_rate_percent", "high_priority_flag"],
        "supplier_orders_scored.csv",
    )
    for filename, frame, columns in [
        ("supplier_summary.csv", summary, ["supplier"]),
        ("supplier_orders_scored.csv", orders, ["order_id", "supplier", "issue_priority"]),
    ]:
        for name in columns:
            if frame[name].isna().any() or frame[name].astype(str).str.strip().eq("").any():
                raise ValueError(f"{filename}: '{name}' contains blank values.")
    if orders["order_id"].duplicated().any():
        raise ValueError("Duplicate order IDs found in supplier_orders_scored.csv.")
    if not orders["issue_priority"].isin(["High", "Medium", "Low"]).all():
        raise ValueError("Issue priority must be High, Medium, or Low.")
    if int(summary["total_orders"].sum()) != len(orders):
        raise ValueError("Supplier totals do not match the number of order records.")
    if int(summary["high_priority_orders"].sum()) != int(orders["issue_priority"].eq("High").sum()):
        raise ValueError("High-priority counts differ between the two KNIME exports.")
except (OSError, ValueError, pd.errors.ParserError) as error:
    st.error(str(error))
    st.stop()

# Summary KPIs always represent the complete dataset; table filters act only below.
order_count = len(orders)
on_time_percent = 100 * orders["delivery_delay_days"].le(0).mean() if order_count else 0
mean_fill_percent = orders["fill_rate_percent"].mean() if order_count else 0
high_count = int(orders["issue_priority"].eq("High").sum())

kpi_columns = st.columns(4, gap="medium")
for column, label, value in zip(
    kpi_columns,
    ["Purchase orders", "On-time delivery", "Average fill rate", "High-priority orders"],
    [f"{order_count:,}", f"{on_time_percent:.1f}%", f"{mean_fill_percent:.1f}%", f"{high_count:,}"],
):
    column.metric(label, value)

st.markdown('<div class="divider-line"></div>', unsafe_allow_html=True)
st.subheader("Performance at a glance")

# Percentages are based on each supplier's own order count, not raw counts.
supplier_stats = summary.copy()
supplier_stats["high_priority_rate"] = np.where(
    supplier_stats["total_orders"].gt(0),
    100 * supplier_stats["high_priority_orders"] / supplier_stats["total_orders"],
    0,
)
supplier_stats = supplier_stats.sort_values("high_priority_rate", ascending=False)
priority_counts = (
    orders["issue_priority"].value_counts().reindex(["High", "Medium", "Low"], fill_value=0)
    .rename_axis("priority").reset_index(name="orders")
)

left_chart, right_chart = st.columns([1.35, 1], gap="large")
with left_chart:
    st.markdown("**High-priority rate by supplier**")
    st.caption("Percentage of each supplier's orders classified as High priority")
    bars = alt.Chart(supplier_stats).mark_bar(color=YELLOW, cornerRadiusEnd=5).encode(
        x=alt.X(
            "high_priority_rate:Q", title="High-priority orders (%)",
            scale=alt.Scale(domain=[0, min(100, max(34, float(supplier_stats["high_priority_rate"].max()) + 9))]),
            axis=alt.Axis(format=".0f"),
        ),
        y=alt.Y("supplier:N", sort="-x", title=None, axis=alt.Axis(labelLimit=170)),
        tooltip=[
            alt.Tooltip("supplier:N", title="Supplier"),
            alt.Tooltip("total_orders:Q", title="Orders", format=".0f"),
            alt.Tooltip("high_priority_orders:Q", title="High-priority orders", format=".0f"),
            alt.Tooltip("high_priority_rate:Q", title="Rate (%)", format=".1f"),
        ],
    )
    labels = bars.mark_text(align="left", baseline="middle", dx=7, color=PALE, fontSize=12).encode(
        text=alt.Text("high_priority_rate:Q", format=".1f")
    )
    st.altair_chart(chart_style((bars + labels).properties(height=265)), use_container_width=True, theme=None)

with right_chart:
    st.markdown("**Delivery issue distribution**")
    st.caption("Number of orders by KNIME priority classification")
    bar = alt.Chart(priority_counts).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
        x=alt.X("priority:N", sort=["High", "Medium", "Low"], title=None),
        y=alt.Y("orders:Q", title="Purchase orders", axis=alt.Axis(tickMinStep=1)),
        color=alt.Color(
            "priority:N", legend=None,
            scale=alt.Scale(domain=["High", "Medium", "Low"], range=[YELLOW, BLUE, GREY]),
        ),
        tooltip=[alt.Tooltip("priority:N", title="Priority"), alt.Tooltip("orders:Q", title="Orders")],
    )
    count_labels = bar.mark_text(dy=-9, color=PALE, fontSize=13, fontWeight="bold").encode(text="orders:Q")
    st.altair_chart(chart_style((bar + count_labels).properties(height=265)), use_container_width=True, theme=None)

if not supplier_stats.empty:
    top = supplier_stats.iloc[0]
    st.caption(
        f"Highest High-priority rate: {top['supplier']} — "
        f"{top['high_priority_rate']:.1f}% "
        f"({int(top['high_priority_orders'])} of {int(top['total_orders'])} orders)."
    )

st.markdown('<div class="divider-line"></div>', unsafe_allow_html=True)
st.subheader("Supplier performance")
st.caption("Aggregated KNIME results. Sorted by the share of High-priority orders.")

performance = supplier_stats[
    ["supplier", "total_orders", "avg_delay_days", "avg_fill_rate_percent",
     "high_priority_orders", "high_priority_rate"]
]
st.dataframe(
    performance, hide_index=True, use_container_width=True,
    column_config={
        "supplier": st.column_config.TextColumn("Supplier"),
        "total_orders": st.column_config.NumberColumn("Orders", format="%d"),
        "avg_delay_days": st.column_config.NumberColumn("Avg. delay (days)", format="%.2f"),
        "avg_fill_rate_percent": st.column_config.NumberColumn("Avg. fill rate", format="%.1f%%"),
        "high_priority_orders": st.column_config.NumberColumn("High-priority orders", format="%d"),
        "high_priority_rate": st.column_config.NumberColumn("High-priority rate", format="%.1f%%"),
    },
)

st.markdown('<div class="divider-line"></div>', unsafe_allow_html=True)
st.subheader("Purchase-order details")
filter_left, filter_right = st.columns([2, 1], gap="medium")
with filter_left:
    supplier_choices = sorted(orders["supplier"].unique().tolist())
    chosen_suppliers = st.multiselect("Suppliers", supplier_choices, default=supplier_choices)
with filter_right:
    chosen_priorities = st.multiselect(
        "Priority", ["High", "Medium", "Low"], default=["High", "Medium", "Low"]
    )

filtered = orders.loc[
    orders["supplier"].isin(chosen_suppliers)
    & orders["issue_priority"].isin(chosen_priorities)
].copy()
filtered["_sort_priority"] = filtered["issue_priority"].map({"High": 0, "Medium": 1, "Low": 2})
filtered = filtered.sort_values(["_sort_priority", "order_date"], kind="stable").drop(columns="_sort_priority")
st.caption(f"Showing {len(filtered):,} of {order_count:,} orders. Filters affect this table and its download only.")
if filtered.empty:
    st.info("No matching orders. Adjust the supplier or priority filters.")

st.dataframe(
    filtered, hide_index=True, use_container_width=True,
    column_config={
        "order_id": "Order ID", "order_date": "Order date", "supplier": "Supplier",
        "part_category": "Part category", "ordered_qty": "Ordered quantity",
        "delivered_qty": "Delivered quantity", "planned_lead_days": "Planned lead (days)",
        "actual_lead_days": "Actual lead (days)",
        "unit_cost_eur": st.column_config.NumberColumn("Unit cost (EUR)", format="%.2f"),
        "delivery_delay_days": "Delay (days)",
        "fill_rate_percent": st.column_config.NumberColumn("Fill rate", format="%.1f%%"),
        "issue_priority": "Priority", "high_priority_flag": "High-priority flag",
    },
    height=290,
)
st.download_button(
    "Download filtered orders",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="filtered_purchase_orders.csv",
    mime="text/csv",
    disabled=filtered.empty,
)

st.markdown('<div class="divider-line"></div>', unsafe_allow_html=True)
st.caption(
    "Classification rules: High = more than 3 days late or fill rate below 95%; "
    "Medium = late or incomplete without meeting High conditions; Low = otherwise. "
    "Synthetic dataset; rules assess completed orders, not future delivery risk."
)
