"""Streamlit dashboard for the recommendation rollout RCA case study."""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st


st.set_page_config(page_title="Engagement Collapse RCA", page_icon="RCA", layout="wide")


SUMMARY_PATH = Path("reports/analysis_summary.json")
PROCESSED_DIR = Path("data/processed")
FIGURES_DIR = Path("reports/figures")


@st.cache_data
def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@st.cache_data
def load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / name)


st.title("Recommendation Rollout RCA")
st.caption("A SQL-first product analytics case study for diagnosing an engagement collapse")

if not SUMMARY_PATH.exists():
    st.warning("Run `python scripts/run_analysis.py` first to generate reports and dashboard inputs.")
    st.stop()

summary = load_json(SUMMARY_PATH)
metric_tree = load_csv("metric_tree.csv")
segment = load_csv("segment_drilldown.csv")
funnel = load_csv("funnel_analysis.csv")
anomaly = load_csv("anomaly_detection.csv")
impact = load_csv("impact_sizing.csv")

st.info(summary["causal_language"])

overview_tab, metric_tab, segment_tab, funnel_tab, anomaly_tab, raw_tab = st.tabs(
    ["Executive Summary", "Metric Tree", "Segment Drilldown", "Funnel", "Anomaly Detection", "Raw Data Sample"]
)

with overview_tab:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Affected Drop", f"{summary['affected_drop_pct']:.1%}")
    col2.metric("Unaffected Change", f"{summary['unaffected_drop_pct']:.1%}")
    col3.metric("Lost Plays", f"{summary['lost_video_plays']:.0f}")
    col4.metric("Lost Watch Hours", f"{summary['lost_watch_hours']:.1f}")

    st.subheader("Recommendation")
    st.write(summary["recommendation"])

    image = FIGURES_DIR / "metric_tree.png"
    if image.exists():
        st.image(str(image), use_container_width=True)

with metric_tab:
    st.subheader("Metric Tree")
    st.dataframe(metric_tree, hide_index=True, use_container_width=True)
    image = FIGURES_DIR / "metric_tree.png"
    if image.exists():
        st.image(str(image), use_container_width=True)

with segment_tab:
    st.subheader("Region, Model, Device Drilldown")
    st.dataframe(segment, hide_index=True, use_container_width=True)
    image = FIGURES_DIR / "segment_drop.png"
    if image.exists():
        st.image(str(image), use_container_width=True)

with funnel_tab:
    st.subheader("Session Funnel")
    st.dataframe(funnel, hide_index=True, use_container_width=True)
    image = FIGURES_DIR / "funnel.png"
    if image.exists():
        st.image(str(image), use_container_width=True)

with anomaly_tab:
    st.subheader("Anomaly Detection")
    st.dataframe(anomaly, hide_index=True, use_container_width=True)
    image = FIGURES_DIR / "anomaly_detection.png"
    if image.exists():
        st.image(str(image), use_container_width=True)

with raw_tab:
    st.subheader("Impact Sizing")
    st.dataframe(impact, hide_index=True, use_container_width=True)
    events_path = PROCESSED_DIR / "events.parquet"
    if events_path.exists():
        st.subheader("Sample Events")
        sample = duckdb.query(f"SELECT * FROM '{events_path.as_posix()}' LIMIT 100").fetchdf()
        st.dataframe(sample, hide_index=True, use_container_width=True)
