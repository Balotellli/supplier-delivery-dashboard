# Supplier Delivery Performance Dashboard

**Supplier performance analysis using KNIME Analytics Platform and an AI-assisted Streamlit application.**

This project demonstrates how purchasing and logistics data can be transformed into actionable supplier performance indicators. KNIME is used to calculate delivery metrics, classify problematic orders, and aggregate supplier results. A Python/Streamlit dashboard, developed with assistance from Codex, makes the KNIME outputs easy to explore.

> **Data notice:** The project uses **synthetic, fictional purchase-order data** generated for learning and demonstration. All findings describe this simulated dataset, not actual supplier performance. The priority rules are illustrative business criteria, not an official industry standard or a predictive risk model.

## Project objective

In manufacturing, late or incomplete deliveries can disrupt production planning. The project aims to answer four practical questions:

- How often do suppliers deliver on time?
- How much of the ordered quantity is actually delivered?
- Which suppliers account for the most significant delivery issues?
- Which individual purchase orders require follow-up?

## Application features

The Streamlit dashboard displays:

- **Four KPIs:** total purchase orders, on-time delivery rate, average order fill rate, and high-priority orders.
- **Supplier performance table:** order count, average delivery delay, average fill rate, and number of high-priority orders for each supplier.
- **Order-level analysis:** a searchable table with filters for supplier and issue priority (`High`, `Medium`, `Low`).
- **CSV export:** download the filtered purchase-order records for further analysis.

The dashboard reads the **two CSV files exported by KNIME**. It does not generate sample data or reclassify orders in the application.

## Technology stack

| Tool | Role |
| --- | --- |
| **KNIME Analytics Platform** | Visual ETL workflow, calculations, rule-based classification, and aggregation |
| **Python / pandas / NumPy** | Loading and validating the exported data, calculating dashboard KPIs |
| **Streamlit** | Interactive web interface, filters, tables, and CSV downloads |
| **Codex (AI-assisted coding)** | Assistance with developing and refining the Streamlit application |
| **GitHub / Streamlit Community Cloud** | Source-code hosting and optional public deployment |

## Dataset and processing workflow

The synthetic dataset represents **180 purchase orders across six fictional suppliers**, covering six component categories. Original fields include order ID and date, supplier, part category, ordered and delivered quantities, planned and actual delivery lead times, and unit cost in euros.

The KNIME workflow processes the data in the following sequence:

```text
CSV Reader  (original supplier delivery records)
    |
Math Formula  (delivery_delay_days)
    |
Math Formula  (fill_rate_percent)
    |
Rule Engine  (issue_priority)
    |
Rule Engine  (high_priority_flag)
    |
    +--> CSV Writer --> supplier_orders_scored.csv  (180 orders)
    |
GroupBy  (aggregate by supplier)
    |
Column Renamer
    |
CSV Writer --> supplier_summary.csv  (6 suppliers)
```

### Key calculations

**Delivery delay (days)**

```text
delivery_delay_days = actual_lead_days - planned_lead_days
```

Positive values indicate late deliveries; zero indicates on-time delivery; negative values indicate early delivery.

**Order fill rate (%)**

```text
fill_rate_percent = (delivered_qty / ordered_qty) * 100
```

**Issue-priority classification**

| Priority | Rule |
| --- | --- |
| **High** | More than 3 days late **or** fill rate below 95% |
| **Medium** | Late or incomplete, without meeting the High-priority criteria |
| **Low** | All other orders |

A separate `high_priority_flag` column contains `1` for High-priority orders and `0` otherwise, allowing KNIME to count them through a `Sum` aggregation. The supplier-level table uses `GroupBy` to count orders and calculate mean delivery delays and fill rates.

## Results

The following figures were **verified against the two exported CSV files**:

| Overall indicator | Result |
| --- | ---: |
| Purchase orders analyzed | **180** |
| Suppliers analyzed | **6** |
| On-time or early deliveries | **152** |
| On-time delivery rate | **84.4%** |
| Average order fill rate | **98.9%** |
| High-priority orders | **28** |
| Medium-priority orders | **7** |
| Low-priority orders | **145** |

*On-time rate is the share of orders with `delivery_delay_days <= 0`. Average fill rate is the arithmetic mean of individual order fill rates, not a quantity-weighted fill rate.*

### Supplier comparison

| Supplier | Orders | Average delay (days) | Average fill rate | High-priority orders |
| --- | ---: | ---: | ---: | ---: |
| Apex Components | 39 | 0.21 | 97.39% | 9 |
| Delta Materials | 18 | 0.78 | 96.41% | 5 |
| Meridian Supply | 26 | 0.19 | 98.97% | 3 |
| Nordic Industrial | 27 | 0.26 | 100.00% | 2 |
| PrecisionLink | 29 | 0.69 | 99.81% | 4 |
| Vector Parts | 41 | 0.59 | 99.81% | 5 |

### Key observations

- **Delta Materials** has the longest average delay (**0.78 days**) and the lowest average fill rate (**96.41%**). It also has the highest *proportion* of high-priority orders: **5 of 18 (27.8%)**.
- **Apex Components** has the largest *number* of high-priority orders (**9**), illustrating why absolute counts and percentages should both be considered.
- **Nordic Industrial** has a **100% mean fill rate** and only **2 high-priority orders** in the simulated data.
- **Vector Parts** handles the largest number of orders (**41**).

These findings support descriptive supplier-performance screening. They are **not forecasts of future supplier behavior**.

## Repository files

```text
supplier-delivery-dashboard/
├── app.py                       # Streamlit application
├── requirements.txt             # Python dependencies
├── supplier_orders_scored.csv   # KNIME export: 180 classified orders
├── supplier_summary.csv         # KNIME export: 6 supplier summaries
└── README.md                    # Project documentation
```

**Important:** If the application is currently named `app(1).py` on your computer, rename it to **`app.py`** before uploading it to GitHub. The Streamlit deployment instructions below assume the name `app.py`.

## Run locally

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

Then start the application:

```bash
streamlit run app.py
```

All four application files (`app.py`, `requirements.txt`, `supplier_orders_scored.csv`, and `supplier_summary.csv`) should be in the same directory.

## Deploy with Streamlit Community Cloud

1. Upload the project files to a GitHub repository.
2. In [Streamlit Community Cloud](https://share.streamlit.io/), create a new app from the repository.
3. Choose the repository, the `main` branch (or your actual branch), and **`app.py`** as the main file path.
4. Deploy and share the generated public URL.

The dashboard uses local CSV exports, so it **does not require a KNIME server or database connection** to run.

## Limitations and next improvements

- The original orders and supplier identities are synthetic, so the results cannot validate real-world supplier reliability.
- The project classifies **completed deliveries** using fixed thresholds; it does not use machine learning to predict delays.
- The dashboard shows a snapshot of exported CSV files rather than a live supplier-management feed.
- The supplied repository files contain **KNIME's processed outputs**, not the original KNIME workflow or raw source dataset. To make the full process reproducible, the `.knwf` workflow export and original `supplier_deliveries.csv` should also be published.
- Potential next steps include supplier-level on-time rates, monitoring changes over time, input-data refresh automation, and testing on real anonymized procurement data.

## What this project demonstrates

This project combines **low-code data engineering in KNIME**, operational KPI design, rule-based analysis, and **AI-assisted application development** into a practical end-to-end analytics prototype. The emphasis is on making procurement data understandable and supporting transparent, repeatable supplier reviews.
