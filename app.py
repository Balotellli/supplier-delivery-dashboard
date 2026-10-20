"""Supplier delivery dashboard for the original KNIME CSV exports (Material design)."""
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

# Material icon paths (24x24 viewBox)
ICONS = {
    "orders": "M3 13h2v-2H3v2zm0 4h2v-2H3v2zm0-8h2V7H3v2zm4 4h14v-2H7v2zm0 4h14v-2H7v2zM7 7v2h14V7H7z",
    "on_time": "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z",
    "fill": "M11 2v20c-5.07-.5-9-4.79-9-10s3.93-9.5 9-10zm2.03 0v8.99H22c-.47-4.74-4.24-8.52-8.97-8.99zm0 11.01V22c4.74-.47 8.5-4.25 8.97-8.99h-8.97z",
    "high": "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z",
}


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


def kpi_card(label: str, value: str, note: str, icon: str, tone: str, delay_ms: int) -> str:
    return f"""
    <div class="kpi kpi-{tone}" style="animation-delay:{delay_ms}ms">
      <div class="kpi-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="{ICONS[icon]}"/></svg></div>
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      <div class="kpi-note">{note}</div>
    </div>"""


def priority_style(value: str) -> str:
    colors = {
        "High": "background-color:#fce8e6;color:#a50e0e;font-weight:500",
        "Medium": "background-color:#fef7e0;color:#8a5a00;font-weight:500",
        "Low": "background-color:#e6f4ea;color:#0d652d;font-weight:500",
    }
    return colors.get(value, "")


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto+Flex:wght@400;500;600;700&family=Roboto:wght@400;500&display=swap');

:root {
    --primary: #1a73e8;  --primary-container: #d3e3fd;  --on-primary-container: #041e49;
    --green: #1e8e3e;    --green-container: #ddf3e4;
    --amber: #f9ab00;    --amber-container: #fdf0c9;
    --red: #d93025;      --red-container: #fcdad7;
    --surface: #ffffff;  --background: #f4f6fb;  --outline: #dadce0;
    --text: #1f1f1f;     --text-muted: #5f6368;
    --shadow-1: 0 1px 2px rgba(60,64,67,.30), 0 1px 3px 1px rgba(60,64,67,.15);
    --shadow-2: 0 1px 3px rgba(60,64,67,.30), 0 4px 8px 3px rgba(60,64,67,.15);
    --ease: cubic-bezier(.2, 0, 0, 1);
}

html, body, .stApp, [data-testid="stAppViewContainer"] {
    background: var(--background); color: var(--text);
    font-family: 'Roboto', system-ui, sans-serif;
}
[data-testid="stHeader"] {background: transparent;}
.block-container {max-width: 1400px; padding-top: 2rem; padding-bottom: 4rem;}
h1, h2, h3, .kpi-value {font-family: 'Roboto Flex', 'Roboto', sans-serif; color: var(--text);}
h3 {font-weight: 500; letter-spacing: 0;}

/* Hero */
.hero {
    background: linear-gradient(120deg, var(--primary-container) 0%, #e8f0fe 55%, #fde7f3 100%);
    border-radius: 28px; padding: 2.2rem 2.4rem; margin-bottom: 1.5rem; box-shadow: var(--shadow-1);
}
.hero h1 {margin: 0; font-size: 2.3rem; font-weight: 600; letter-spacing: -0.02em; color: var(--on-primary-container);}
.hero p {margin: .5rem 0 0; color: #3c4a63; font-size: 1.05rem; max-width: 62ch;}

/* KPI cards */
.kpi-row {display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 1rem; margin-bottom: .6rem;}
.kpi {
    background: var(--surface); border-radius: 20px; padding: 1.2rem 1.3rem; box-shadow: var(--shadow-1);
    transition: box-shadow .25s var(--ease), transform .25s var(--ease);
    animation: rise .5s var(--ease) both;
}
.kpi:hover {box-shadow: var(--shadow-2); transform: translateY(-2px);}
.kpi-icon {width: 42px; height: 42px; border-radius: 14px; display: grid; place-items: center; margin-bottom: .8rem;}
.kpi-icon svg {width: 24px; height: 24px; fill: currentColor;}
.kpi-blue .kpi-icon {background: var(--primary-container); color: var(--primary);}
.kpi-green .kpi-icon {background: var(--green-container); color: var(--green);}
.kpi-amber .kpi-icon {background: var(--amber-container); color: #b06000;}
.kpi-red .kpi-icon {background: var(--red-container); color: var(--red);}
.kpi-label {color: var(--text-muted); font-size: .92rem; font-weight: 500;}
.kpi-value {font-size: 2.3rem; font-weight: 600; line-height: 1.15; margin: .15rem 0;}
.kpi-note {color: var(--text-muted); font-size: .82rem;}
@keyframes rise {from {opacity: 0; transform: translateY(12px);} to {opacity: 1; transform: none;}}

/* Section cards (st.container(border=True)) */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--surface); border: none !important; border-radius: 24px;
    box-shadow: var(--shadow-1); padding: .6rem .8rem;
}
[data-testid="stDataFrame"] {border-radius: 16px; overflow: hidden;}

/* Controls */
[data-baseweb="select"] > div {border-radius: 12px !important; border-color: var(--outline) !important;}
[data-baseweb="tag"] {background: var(--primary-container) !important; color: var(--on-primary-container) !important; border-radius: 8px !important;}
.stDownloadButton button {
    background: var(--primary); color: #fff; border: none; border-radius: 999px;
    padding: .55rem 1.5rem; font-weight: 500; box-shadow: var(--shadow-1);
    transition: box-shadow .2s var(--ease), background .2s var(--ease);
}
.stDownloadButton button:hover {background: #1765cc; color: #fff; box-shadow: var(--shadow-2);}
.stDownloadButton button:disabled {background: #e8eaed; color: #9aa0a6; box-shadow: none;}
button:focus-visible, [data-baseweb="select"]:focus-within {outline: 3px solid #8ab4f8 !important; outline-offset: 2px;}
[data-testid="stCaptionContainer"] {color: var(--text-muted);}

/* Legend chips */
.chips {display: flex; flex-wrap: wrap; gap: .6rem; margin-top: .4rem;}
.chip {border-radius: 10px; padding: .45rem .9rem; font-size: .88rem;}
.chip-high {background: var(--red-container); color: #a50e0e;}
.chip-med {background: var(--amber-container); color: #7a4f00;}
.chip-low {background: var(--green-container); color: #0d652d;}

@media (prefers-reduced-motion: reduce) {
    .kpi {animation: none; transition: none;}
    .kpi:hover {transform: none;}
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    """
    <div class="hero">
      <h1>Supplier Delivery Performance Dashboard</h1>
      <p>See which suppliers deliver on time, which ship incomplete orders, and where to follow up first.
      Based on the KNIME delivery performance exports.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

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

# ---- KPIs (all purchase orders) ----
total, on_time, fill, high = calculate_kpis(orders)
st.markdown(
    '<div class="kpi-row">'
    + kpi_card("Total Orders", f"{total:,}", "All purchase orders in the export", "orders", "blue", 0)
    + kpi_card("On-Time Delivery Rate", f"{on_time:.1f}%" if on_time is not None else "N/A",
               "Delivery delay of 0 days or less", "on_time", "green", 80)
    + kpi_card("Average Fill Rate", f"{fill:.1f}%" if fill is not None else "N/A",
               "Mean order-level fill rate, equal weight per order", "fill", "amber", 160)
    + kpi_card("High-Priority Orders", f"{high:,}", "Orders classified High by KNIME", "high", "red", 240)
    + "</div>",
    unsafe_allow_html=True,
)
st.caption("KPIs cover all purchase orders. The filters below affect purchase order details and the CSV download only.")

# ---- Supplier performance ----
st.subheader("Supplier Performance")
with st.container(border=True):
    chart_col, table_col = st.columns([1, 1.3], gap="large")
    with chart_col:
        st.markdown("**Average delay by supplier (days)**")
        st.bar_chart(summary.set_index("supplier")["avg_delay_days"], color="#1a73e8")
    with table_col:
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

# ---- Purchase order details ----
st.subheader("Purchase Order Details")
with st.container(border=True):
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

    styler = filtered.style
    styled = (styler.map if hasattr(styler, "map") else styler.applymap)(priority_style, subset=["issue_priority"])
    st.dataframe(
        styled, hide_index=True, width="stretch",
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

# ---- Classification legend ----
st.subheader("Issue Classifications")
st.markdown(
    """
    <div class="chips">
      <div class="chip chip-high"><b>High</b> · more than 3 days late or fill rate below 95%</div>
      <div class="chip chip-med"><b>Medium</b> · late or incomplete without meeting High conditions</div>
      <div class="chip chip-low"><b>Low</b> · on time and complete</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption("The dashboard displays the issue priorities exported by KNIME.")
