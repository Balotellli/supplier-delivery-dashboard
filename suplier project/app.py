"""Supplier delivery dashboard for the original KNIME CSV exports."""
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Supplier Delivery Performance Dashboard", layout="wide")
BASE_DIR = Path(__file__).resolve().parent
SUMMARY_COLUMNS = [
    "supplier", "total_orders", "avg_delay_days", "avg_fill_rate_percent", "high_priority_orders"
]
ORDER_COLUMNS = [
    "order_id", "order_date", "supplier", "part_category", "ordered_qty", "delivered_qty",
    "planned_lead_days", "actual_lead_days", "unit_cost_eur", "delivery_delay_days",
    "fill_rate_percent", "issue_priority", "high_priority_flag"
]


@st.cache_data(show_spinner=False)
def load_csv(path: str, modified_ns: int, required: tuple[str, ...]) -> pd.DataFrame:
    """Cache each export; its modification time invalidates the cached data."""
    df = pd.read_csv(path, encoding="utf-8-sig")
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise ValueError(f"{Path(path).name}: missing required columns: {', '.join(missing)}")
    return df


def read_export(name: str, columns: list[str]) -> pd.DataFrame:
    path = BASE_DIR / name
    if not path.is_file():
        raise ValueError(f"Missing file: {name}. Place the original KNIME CSV beside app.py.")
    return load_csv(str(path), path.stat().st_mtime_ns, tuple(columns)).copy()


def validate_numeric(df: pd.DataFrame, columns: list[str], name: str) -> None:
    for column in columns:
        values = pd.to_numeric(df[column], errors="coerce")
        if not np.isfinite(values.to_numpy(dtype=float)).all():
            raise ValueError(f"{name}: '{column}' contains missing or invalid numeric values.")
        df[column] = values


def calculate_kpis(orders: pd.DataFrame) -> tuple[int, float | None, float | None, int]:
    count = len(orders)
    return (
        count,
        float(orders["delivery_delay_days"].le(0).mean() * 100) if count else None,
        float(orders["fill_rate_percent"].mean()) if count else None,
        int(orders["issue_priority"].eq("High").sum()),
    )


st.markdown("""
<style>
.block-container {max-width: 1500px; padding-top: 2.5rem;}
h1 {letter-spacing: -0.035em;}
[data-testid="stMetric"] {background: #191e26; border-top: 3px solid #338bff;
    border-radius: 8px; padding: 1rem;}
</style>
""", unsafe_allow_html=True)
st.title("Supplier Delivery Performance Dashboard")
st.caption("Procurement operations · KNIME delivery performance exports")

try:
    summary = read_export("supplier_summary.csv", SUMMARY_COLUMNS)
    orders = read_export("supplier_orders_scored.csv", ORDER_COLUMNS)
    validate_numeric(summary, SUMMARY_COLUMNS[1:], "supplier_summary.csv")
    validate_numeric(orders, ORDER_COLUMNS[4:11] + ["high_priority_flag"], "supplier_orders_scored.csv")
    for name, frame, columns in [
        ("supplier_summary.csv", summary, ["supplier"]),
        ("supplier_orders_scored.csv", orders, ["order_id", "supplier", "issue_priority"]),
    ]:
        for column in columns:
            if frame[column].isna().any() or frame[column].astype(str).str.strip().eq("").any():
                raise ValueError(f"{name}: '{column}' contains blank values.")
    if orders["order_id"].duplicated().any():
        raise ValueError("supplier_orders_scored.csv: duplicate order_id values; expected one row per purchase order.")
    if not orders["issue_priority"].isin(["High", "Medium", "Low"]).all():
        raise ValueError("supplier_orders_scored.csv: issue_priority must contain only High, Medium, or Low.")
except (OSError, ValueError, pd.errors.ParserError) as exc:
    st.error(str(exc))
    st.stop()

st.caption("KPIs cover all purchase orders. Filters below affect purchase order details and the CSV download only.")
total, on_time, fill, high = calculate_kpis(orders)
for column, label, value in zip(
    st.columns(4),
    ["Total Orders", "On-Time Delivery Rate", "Average Fill Rate", "High-Priority Orders"],
    [f"{total:,}", f"{on_time:.1f}%" if on_time is not None else "N/A",
     f"{fill:.1f}%" if fill is not None else "N/A", f"{high:,}"],
):
    column.metric(label, value)
st.caption("On time: delivery delay ≤ 0 days. Average Fill Rate: mean order-level fill rate, with equal weight per order.")

st.subheader("Supplier Performance")
st.dataframe(
    summary[SUMMARY_COLUMNS], hide_index=True, width="stretch",
    column_config={
        "supplier": st.column_config.TextColumn("Supplier"),
        "total_orders": st.column_config.NumberColumn("Order Count", format="%d"),
        "avg_delay_days": st.column_config.NumberColumn("Average Delay (days)", format="%.2f"),
        "avg_fill_rate_percent": st.column_config.NumberColumn("Average Fill Rate", format="%.2f%%"),
        "high_priority_orders": st.column_config.NumberColumn("High-Priority Orders", format="%d"),
    },
)
st.caption("Supplier figures are shown directly from supplier_summary.csv.")

st.subheader("Purchase Order Details")
left, right = st.columns([2, 1])
suppliers = sorted(orders["supplier"].unique().tolist())
selected_suppliers = left.multiselect("Supplier", suppliers, default=suppliers)
selected_priorities = right.multiselect("Issue Priority", ["High", "Medium", "Low"], default=["High", "Medium", "Low"])
filtered = orders.loc[
    orders["supplier"].isin(selected_suppliers) & orders["issue_priority"].isin(selected_priorities)
]
st.caption(f"Showing {len(filtered):,} of {total:,} purchase orders")
if filtered.empty:
    st.info("No purchase orders match these filters. Select at least one supplier and issue priority.")
st.dataframe(
    filtered, hide_index=True, width="stretch",
    column_config={
        "order_id": "Order ID", "order_date": "Order Date", "supplier": "Supplier",
        "part_category": "Part Category", "ordered_qty": "Ordered Quantity",
        "delivered_qty": "Delivered Quantity", "planned_lead_days": "Planned Lead (days)",
        "actual_lead_days": "Actual Lead (days)",
        "unit_cost_eur": st.column_config.NumberColumn("Unit Cost (EUR)", format="%.2f"),
        "delivery_delay_days": "Delivery Delay (days)",
        "fill_rate_percent": st.column_config.NumberColumn("Fill Rate", format="%.2f%%"),
        "issue_priority": "Issue Priority", "high_priority_flag": "High-Priority Flag",
    },
)
st.download_button(
    "Download Filtered Purchase Orders", data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="filtered_purchase_orders.csv", mime="text/csv", disabled=filtered.empty,
)
st.divider()
st.markdown("**Issue classifications**")
st.caption(
    "High = more than 3 days late or fill rate below 95%. "
    "Medium = late or incomplete without meeting High conditions. Low = otherwise. "
    "The dashboard displays the issue priorities exported by KNIME."
)
