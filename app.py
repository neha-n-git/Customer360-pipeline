from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent
ANALYTICS_ROOT = PROJECT_ROOT / "data" / "analytics"


@st.cache_data
def read_csv(path):
    if not path.is_file():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except (OSError, pd.errors.EmptyDataError, pd.errors.ParserError):
        return pd.DataFrame()


@st.cache_data
def load_summary(path):
    if not path.is_file():
        return {}
    try:
        import json

        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


@st.cache_data
def read_parquet(path):
    if not path.is_file():
        return pd.DataFrame()
    try:
        return pd.read_parquet(path)
    except (OSError, ValueError, ImportError):
        return pd.DataFrame()


def available_batches():
    if not ANALYTICS_ROOT.is_dir():
        return []
    return sorted(
        (path.name for path in ANALYTICS_ROOT.iterdir() if path.is_dir()),
        reverse=True,
    )


st.set_page_config(
    page_title="Customer 360 Analytics",
    page_icon="",
    layout="wide",
)

st.title("Customer 360 Analytics")
st.caption("Verified Customer 360 analytical outputs")

batches = available_batches()
if not batches:
    st.warning("No analytics batches were found under data/analytics.")
    st.stop()

selected_batch = st.sidebar.selectbox("Analytics batch", batches)
batch_dir = ANALYTICS_ROOT / selected_batch

top_customers = read_csv(batch_dir / "top_customers_by_revenue.csv")
segmentation = read_csv(batch_dir / "customer_segmentation.csv")
high_support = read_csv(batch_dir / "high_support_customers.csv")
revenue_by_city = read_csv(batch_dir / "revenue_by_city.csv")
customer_count_by_city = read_csv(batch_dir / "customer_count_by_city.csv")
summary = load_summary(batch_dir / "execution_summary.json")

required_files = {
    "Top customers": batch_dir / "top_customers_by_revenue.csv",
    "Segmentation": batch_dir / "customer_segmentation.csv",
    "High-support customers": batch_dir / "high_support_customers.csv",
    "Revenue by city": batch_dir / "revenue_by_city.csv",
    "Customer count by city": batch_dir / "customer_count_by_city.csv",
}
missing_files = [name for name, path in required_files.items() if not path.is_file()]
if missing_files:
    st.warning("Missing analytics outputs: " + ", ".join(missing_files))

total_customers = summary.get("gold_records_read")
if total_customers is None and not customer_count_by_city.empty:
    total_customers = int(customer_count_by_city["customer_count"].sum())
total_customers = 0 if total_customers is None else int(total_customers)

total_revenue = 0.0
if not revenue_by_city.empty and "revenue" in revenue_by_city.columns:
    total_revenue = float(revenue_by_city["revenue"].sum())

high_support_count = len(high_support)

st.subheader("Overview")
metric_columns = st.columns(4)
metric_columns[0].metric("Total customers", f"{total_customers:,}")
metric_columns[1].metric("Valid lifetime revenue", f"{total_revenue:,.2f}")
metric_columns[2].metric(
    "Segments",
    len(segmentation["segment"].dropna().unique()) if not segmentation.empty else 0,
)
metric_columns[3].metric("High-support customers", f"{high_support_count:,}")

overview_tab, top_tab, segment_tab, support_tab, geography_tab, quality_tab = st.tabs(
    [
        "Overview",
        "Top 10 Customers",
        "Segmentation",
        "Support Analysis",
        "Geographical Analysis",
        "Data Quality",
    ]
)

with overview_tab:
    if not segmentation.empty:
        segment_chart = segmentation.set_index("segment")
        st.bar_chart(segment_chart["customer_count"])
    else:
        st.info("Segment distribution is unavailable for this batch.")

with top_tab:
    st.subheader("Top 10 Customers by Revenue")
    if top_customers.empty:
        st.info("No known lifetime revenue records are available.")
    else:
        st.dataframe(top_customers, use_container_width=True, hide_index=True)
        if {"name", "lifetime_value"}.issubset(top_customers.columns):
            chart_data = top_customers.set_index("name")[["lifetime_value"]]
            st.bar_chart(chart_data)

with segment_tab:
    st.subheader("Customer Segmentation")
    if segmentation.empty:
        st.info("Customer segmentation is unavailable for this batch.")
    else:
        st.dataframe(segmentation, use_container_width=True, hide_index=True)
        segment_chart = segmentation.set_index("segment")[["customer_count"]]
        st.bar_chart(segment_chart)

with support_tab:
    st.subheader("Customers with More Than 5 Support Tickets")
    if high_support.empty:
        st.info("No customers exceed five support tickets.")
    else:
        st.dataframe(
            high_support,
            use_container_width=True,
            hide_index=True,
            column_order=[
                "customer_id",
                "name",
                "support_tickets",
                "lifetime_value",
            ],
        )

with geography_tab:
    st.subheader("Revenue by City")
    if revenue_by_city.empty:
        st.info("Revenue by city is unavailable for this batch.")
    else:
        st.bar_chart(revenue_by_city.set_index("city")[["revenue"]])
        st.dataframe(revenue_by_city, use_container_width=True, hide_index=True)

    st.subheader("Customer Count by City")
    if customer_count_by_city.empty:
        st.info("Customer count by city is unavailable for this batch.")
    else:
        st.bar_chart(customer_count_by_city.set_index("city")[["customer_count"]])
        st.dataframe(
            customer_count_by_city,
            use_container_width=True,
            hide_index=True,
        )

with quality_tab:
    st.subheader("Data Quality")

    bronze_dir = PROJECT_ROOT / "data" / "bronze" / selected_batch
    silver_dir = PROJECT_ROOT / "data" / "silver" / selected_batch
    quarantine_dir = silver_dir / "quarantine"

    bronze_counts = {
        source: len(read_parquet(bronze_dir / filename))
        for source, filename in {
            "CRM": "crm_customers.parquet",
            "Orders": "orders.parquet",
            "Support": "support_tickets.parquet",
        }.items()
    }
    silver_counts = {
        source: len(read_parquet(silver_dir / filename))
        for source, filename in {
            "CRM": "crm_customers.parquet",
            "Orders": "orders.parquet",
            "Support": "support_tickets.parquet",
        }.items()
    }
    quarantine_counts = {
        source: len(read_parquet(quarantine_dir / filename))
        for source, filename in {
            "CRM": "crm_conflicts.parquet",
            "Orders": "orders.parquet",
            "Support": "support.parquet",
        }.items()
    }

    quality_issues = read_parquet(silver_dir / "quality_issues.parquet")

    st.markdown("#### Ingestion Overview")
    ingestion_columns = st.columns(4)
    ingestion_columns[0].metric("CRM ingested", bronze_counts["CRM"])
    ingestion_columns[1].metric("Orders ingested", bronze_counts["Orders"])
    ingestion_columns[2].metric("Support ingested", bronze_counts["Support"])
    ingestion_columns[3].metric("Total ingested", sum(bronze_counts.values()))

    st.markdown("#### Silver Processing")
    silver_columns = st.columns(4)
    silver_columns[0].metric("Valid CRM", silver_counts["CRM"])
    silver_columns[1].metric("Valid Orders", silver_counts["Orders"])
    silver_columns[2].metric("Valid Support", silver_counts["Support"])
    silver_columns[3].metric("Total valid Silver", sum(silver_counts.values()))

    st.markdown("#### Quarantine Overview")
    quarantine_columns = st.columns(4)
    quarantine_columns[0].metric("CRM quarantined", quarantine_counts["CRM"])
    quarantine_columns[1].metric("Orders quarantined", quarantine_counts["Orders"])
    quarantine_columns[2].metric("Support quarantined", quarantine_counts["Support"])
    quarantine_columns[3].metric(
        "Total quarantined",
        sum(quarantine_counts.values()),
    )

    if quality_issues.empty:
        st.info("Quality issue details are unavailable for this batch.")
        st.caption(
            "Issue-row counts are separate from unique rejected-record counts."
        )
    else:
        st.markdown("#### Quality Issues")
        issue_columns = st.columns(4)
        issue_columns[0].metric("Issue rows", len(quality_issues))
        issue_columns[1].metric(
            "Errors",
            int(quality_issues["severity"].eq("ERROR").sum())
            if "severity" in quality_issues.columns else 0,
        )
        issue_columns[2].metric(
            "Warnings",
            int(quality_issues["severity"].eq("WARNING").sum())
            if "severity" in quality_issues.columns else 0,
        )
        unique_issue_records = (
            quality_issues.groupby(
                ["source", "record_key"],
                dropna=False,
            ).ngroups
            if {"source", "record_key"}.issubset(quality_issues.columns)
            else 0
        )
        issue_columns[3].metric("Unique issue records", unique_issue_records)

        if "severity" in quality_issues.columns:
            severity_counts = (
                quality_issues.groupby("severity", dropna=False)
                .size().rename("issue_count").reset_index()
            )
            st.dataframe(severity_counts, use_container_width=True, hide_index=True)

        if "source" in quality_issues.columns:
            source_counts = (
                quality_issues.groupby("source", dropna=False)
                .size().rename("issue_count").reset_index()
            )
            st.dataframe(source_counts, use_container_width=True, hide_index=True)

        if "issue_type" in quality_issues.columns:
            issue_type_counts = (
                quality_issues.groupby("issue_type", dropna=False)
                .size().rename("issue_count").reset_index()
            )
            st.dataframe(issue_type_counts, use_container_width=True, hide_index=True)

        if "reason" in quality_issues.columns:
            reason_counts = (
                quality_issues["reason"].fillna("Unknown")
                .value_counts().rename("issue_count").reset_index()
            )
            reason_counts.columns = ["reason", "issue_count"]
            st.dataframe(reason_counts.head(10), use_container_width=True, hide_index=True)

        display_columns = [
            column for column in [
                "source",
                "record_key",
                "column",
                "reason",
                "severity",
                "issue_type",
            ]
            if column in quality_issues.columns
        ]
        st.dataframe(
            quality_issues[display_columns],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("#### Unmatched Records")
    unmatched_counts = {}
    for source, filename in {"Orders": "orders.parquet", "Support": "support.parquet"}.items():
        records = read_parquet(quarantine_dir / filename)
        if records.empty or "quarantine_reason" not in records.columns:
            unmatched_counts[source] = 0
            continue
        unmatched_counts[source] = int(
            records["quarantine_reason"]
            .fillna("")
            .astype(str)
            .str.contains("UNMATCHED_CUSTOMER_ID|not present in valid CRM", case=False, regex=True)
            .sum()
        )

    unmatched_columns = st.columns(2)
    unmatched_columns[0].metric("Unmatched Orders", unmatched_counts["Orders"])
    unmatched_columns[1].metric("Unmatched Support", unmatched_counts["Support"])
