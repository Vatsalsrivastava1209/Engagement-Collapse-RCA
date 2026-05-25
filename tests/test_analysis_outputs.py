from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def test_analysis_summary_signals_localized_drop() -> None:
    summary = json.loads(Path("reports/analysis_summary.json").read_text(encoding="utf-8"))
    assert summary["affected_drop_pct"] < -0.20
    assert summary["unaffected_drop_pct"] > -0.05
    assert summary["difference_in_differences"] < -1.0
    assert summary["bootstrap_ci_post_minus_pre"]["upper"] < 0


def test_metric_tree_has_required_rows_and_columns() -> None:
    metric_tree = pd.read_csv("data/processed/metric_tree.csv")
    assert set(metric_tree["cohort"]) == {"affected", "unaffected"}
    assert set(metric_tree["period"]) == {"pre", "post"}
    required = {
        "active_users",
        "sessions",
        "video_plays",
        "plays_per_active_user",
        "completion_rate",
        "bounce_rate",
    }
    assert required.issubset(metric_tree.columns)


def test_anomaly_detection_flags_affected_post_rollout_days() -> None:
    anomaly = pd.read_csv("data/processed/anomaly_detection.csv")
    affected_post = anomaly[
        (anomaly["cohort"] == "affected")
        & (anomaly["event_date"] >= "2025-11-17")
    ]
    assert affected_post["anomaly_flag"].astype(bool).any()


def test_report_artifacts_exist() -> None:
    expected = [
        Path("reports/executive_summary.md"),
        Path("reports/analysis_summary.json"),
        Path("reports/figures/metric_tree.png"),
        Path("reports/figures/segment_drop.png"),
        Path("reports/figures/funnel.png"),
        Path("reports/figures/anomaly_detection.png"),
    ]
    for path in expected:
        assert path.exists(), f"Missing artifact: {path}"
        assert path.stat().st_size > 0
