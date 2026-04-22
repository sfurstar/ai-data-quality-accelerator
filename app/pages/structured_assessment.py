"""
app/pages/structured_assessment.py
Structured data assessment page — CSV upload + quality checks.
"""
from __future__ import annotations

import io
import os
import pandas as pd
import streamlit as st

from engine import Dimension
from engine.structured import completeness, validity, pii_detector, ai_readiness
from engine.scoring.scorer import build_result
from app.components.score_card import render_score_card
from app.components.findings_table import render_findings_table
from app.theme import page_header


def render():
    page_header("Structured Data Assessment", "Upload a dataset and assess it across five quality dimensions.")
    st.markdown(
        "Upload a CSV file, connect to a Snowflake table, or use the sample NYC 311 dataset."
    )

    # ── Data source selection ────────────────────────────────────────────────
    _sf_available = bool(os.environ.get("SNOWFLAKE_ACCOUNT"))
    source_options = ["Upload CSV", "Use sample dataset (NYC 311 Service Requests)"]
    if _sf_available:
        source_options.append("❄️ Snowflake table")

    source_option = st.radio(
        "Data source",
        source_options,
        horizontal=True,
    )

    df: pd.DataFrame | None = None
    source_name = ""

    if source_option == "Upload CSV":
        uploaded = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")
        if uploaded:
            df = pd.read_csv(uploaded, low_memory=False)
            source_name = uploaded.name
    elif source_option == "❄️ Snowflake table":
        df, source_name = _load_snowflake_table()
    else:
        df, source_name = _load_sample_dataset()
        if df is not None:
            st.success(f"✅ Sample dataset loaded: {source_name} ({len(df):,} rows, {len(df.columns)} columns)")

    if df is None:
        st.info("👆 Upload a CSV file, select the sample dataset, or choose a Snowflake table to begin.")
        return

    # ── Preview ──────────────────────────────────────────────────────────────
    with st.expander("Preview dataset", expanded=False):
        st.dataframe(df.head(100), use_container_width=True)
        st.caption(f"{len(df):,} rows × {len(df.columns)} columns")

    # ── Column config ────────────────────────────────────────────────────────
    with st.expander("Assessment configuration (optional)", expanded=False):
        st.markdown("**Column types** — override detection if needed")
        st.caption("The engine auto-detects types; override here for best results.")
        # Future: column type overrides, required field selection, etc.
        st.info("Auto-detection active — no overrides configured.")

    # ── Run assessment ───────────────────────────────────────────────────────
    if st.button("▶ Run Assessment", type="primary", use_container_width=True):
        _run_assessment(df, source_name)


def _run_assessment(df: pd.DataFrame, source_name: str):
    with st.spinner("Running assessment..."):
        progress = st.progress(0, text="Checking completeness...")

        comp_findings = completeness.run(df)
        progress.progress(25, text="Checking validity...")

        val_findings = validity.run(df)
        progress.progress(50, text="Scanning for PII...")

        pii_findings = pii_detector.run(df)
        progress.progress(75, text="Evaluating AI readiness...")

        air_findings = ai_readiness.run(df)
        progress.progress(100, text="Scoring...")

        findings_by_dim = {
            Dimension.COMPLETENESS: comp_findings,
            Dimension.VALIDITY: val_findings,
            Dimension.GOVERNANCE: pii_findings,
            Dimension.AI_READINESS: air_findings,
            Dimension.CONSISTENCY: [],  # TODO: consistency module
        }

        result = build_result(source_name, "structured", findings_by_dim)

    st.success("Assessment complete!")
    st.divider()

    # ── Score card ───────────────────────────────────────────────────────────
    render_score_card(result)
    st.divider()

    # ── Findings table ───────────────────────────────────────────────────────
    render_findings_table(result.all_findings)

    # ── Save to session for Report page ─────────────────────────────────────
    st.session_state["structured_result"] = result

    # ── Persist to Snowflake if configured ───────────────────────────────────
    try:
        from engine.snowflake.persist import save_result
        from engine.snowflake.connection import get_session
        get_session.cache_clear()
        sf_result = save_result(result)
        if sf_result["status"] == "saved":
            st.caption(f"✅ Results saved to Snowflake (ID: {sf_result['assessment_id'][:8]}...)")
    except Exception as e:
        st.caption(f"⚠️ Snowflake save failed: {e}")


def _load_sample_dataset() -> tuple[pd.DataFrame | None, str]:
    """
    Load a small slice of the NYC 311 sample dataset from the data/sample directory.
    Falls back to generating a minimal synthetic dataset if the file isn't present.
    """
    from pathlib import Path
    import numpy as np

    sample_path = Path(__file__).parents[2] / "data" / "sample" / "structured" / "nyc_311_sample.csv"

    if sample_path.exists():
        df = pd.read_csv(sample_path, low_memory=False)
        return df, "nyc_311_sample.csv"

    # ── Synthetic fallback ───────────────────────────────────────────────────
    st.warning("Sample CSV not found — using synthetic government data. Run `scripts/download_sample.py` to get real data.")
    rng = np.random.default_rng(42)
    n = 1000

    statuses = ["Open", "Closed", "Pending", "In Progress"]
    agencies = ["NYPD", "DOT", "DEP", "DSNY", "HPD", None]
    complaint_types = ["Noise - Residential", "HEAT/HOT WATER", "Blocked Driveway",
                       "Illegal Parking", "Street Light Condition", "Rodent"]
    boroughs = ["BROOKLYN", "MANHATTAN", "QUEENS", "BRONX", "STATEN ISLAND"]

    df = pd.DataFrame({
        "unique_key": [f"REQ-{i:06d}" for i in range(n)],
        "created_date": pd.date_range("2024-01-01", periods=n, freq="1h").astype(str),
        "closed_date": [
            str(pd.Timestamp("2024-01-01") + pd.Timedelta(hours=rng.integers(1, 500)))
            if rng.random() > 0.15 else None
            for _ in range(n)
        ],
        "agency": rng.choice(agencies, n),
        "complaint_type": rng.choice(complaint_types, n),
        "status": rng.choice(statuses, n, p=[0.1, 0.75, 0.10, 0.05]),
        "borough": rng.choice(boroughs, n),
        "zip_code": [
            str(rng.integers(10001, 11697)) if rng.random() > 0.05 else "INVALID"
            for _ in range(n)
        ],
        "latitude": rng.uniform(40.4, 40.9, n).round(6),
        "longitude": rng.uniform(-74.3, -73.7, n).round(6),
        "resolution_description": [
            "Issue resolved." if rng.random() > 0.30 else None
            for _ in range(n)
        ],
        "incident_address": [
            f"{rng.integers(1,999)} {rng.choice(['Broadway', 'Main St', 'Park Ave'])}"
            if rng.random() > 0.08 else None
            for _ in range(n)
        ],
    })

    # Inject some quality issues for demo
    # ~3% SSN-like values in a mislabeled column
    ssn_col = [""] * n
    for i in rng.choice(n, size=30, replace=False):
        ssn_col[i] = f"{rng.integers(100,999)}-{rng.integers(10,99)}-{rng.integers(1000,9999)}"
    df["reference_id"] = ssn_col
    df.loc[df["reference_id"] == "", "reference_id"] = None

    return df, "synthetic_gov_311.csv (demo)"


def _load_snowflake_table() -> tuple[pd.DataFrame | None, str]:
    """Load data from a user-selected Snowflake table."""
    try:
        from engine.snowflake.data_source import list_tables, fetch_sample, get_row_count

        with st.spinner("Loading available Snowflake tables..."):
            tables = list_tables()

        if not tables:
            st.warning("No tables found. Run `snowflake/setup.sql` to create the required objects.")
            return None, ""

        # Build display options
        options = {f"{t['schema']}.{t['name']} ({t['row_count']:,} rows)": t["full_name"]
                   for t in tables}

        selected_label = st.selectbox(
            "Select table",
            options=list(options.keys()),
            index=0,
        )
        selected_table = options[selected_label]

        col_limit, col_load = st.columns([2, 1])
        with col_limit:
            limit = st.number_input(
                "Max rows to assess",
                min_value=100,
                max_value=100000,
                value=5000,
                step=1000,
                help="Larger samples give more accurate results but take longer to load.",
            )
        with col_load:
            st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
            load_clicked = st.button("Load table", use_container_width=True)

        # Clear cached df if user switches tables
        if st.session_state.get("sf_table_name") != selected_table:
            st.session_state.pop("sf_table_df", None)
            st.session_state.pop("sf_table_name", None)

        if load_clicked:
            with st.spinner(f"Fetching {limit:,} rows from {selected_table}..."):
                df = fetch_sample(selected_table, limit=int(limit))
                actual_rows = get_row_count(selected_table)
            st.session_state["sf_table_df"] = df
            st.session_state["sf_table_name"] = selected_table
            st.success(
                f"✅ Loaded {len(df):,} rows from `{selected_table}` "
                f"(table has {actual_rows:,} total rows, {len(df.columns)} columns)"
            )

        # Return from session state if already loaded
        if "sf_table_df" in st.session_state:
            return st.session_state["sf_table_df"], st.session_state["sf_table_name"]

        return None, ""

    except Exception as e:
        st.error(f"❌ Snowflake error: {e}")
        return None, ""
