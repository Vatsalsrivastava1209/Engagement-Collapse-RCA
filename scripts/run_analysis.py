"""Run the SQL-first engagement collapse RCA analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


SQL_DIR = Path("sql")
PROCESSED_DIR = Path("data/processed")
REPORTS_DIR = Path("reports")
FIGURES_DIR = REPORTS_DIR / "figures"
AFFECTED_REGIONS = {"IN-North", "IN-South"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RCA SQL analysis.")
    parser.add_argument("--input", default="data/raw/events.jsonl", help="Input JSONL file.")
    parser.add_argument("--seed", type=int, default=42, help="Bootstrap random seed.")
    return parser.parse_args()


def ensure_dirs() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def connect_events(input_path: Path) -> duckdb.DuckDBPyConnection:
    if not input_path.exists():
        raise FileNotFoundError(f"Missing raw event file: {input_path}")
    con = duckdb.connect()
    raw_path = input_path.as_posix()
    con.execute(
        f"""
        CREATE OR REPLACE TABLE events AS
        SELECT
            event_id::VARCHAR AS event_id,
            user_id::INTEGER AS user_id,
            session_id::VARCHAR AS session_id,
            event_type::VARCHAR AS event_type,
            CAST(timestamp AS TIMESTAMPTZ) AS event_ts,
            CAST(CAST(timestamp AS TIMESTAMPTZ) AS DATE) AS event_date,
            region::VARCHAR AS region,
            device::VARCHAR AS device,
            app_version::VARCHAR AS app_version,
            model_version::VARCHAR AS model_version,
            content_id::VARCHAR AS content_id,
            content_category::VARCHAR AS content_category,
            watch_seconds::INTEGER AS watch_seconds
        FROM read_json_auto('{raw_path}', format='newline_delimited');
        """
    )
    con.execute("COPY events TO 'data/processed/events.parquet' (FORMAT PARQUET);")
    return con


def run_sql(con: duckdb.DuckDBPyConnection, name: str) -> pd.DataFrame:
    sql = (SQL_DIR / name).read_text(encoding="utf-8")
    data = con.execute(sql).fetchdf()
    output = PROCESSED_DIR / f"{Path(name).stem}.csv"
    data.to_csv(output, index=False)
    return data


def bootstrap_difference(values_a: np.ndarray, values_b: np.ndarray, seed: int, iterations: int = 5000) -> dict:
    rng = np.random.default_rng(seed)
    estimates = []
    for _ in range(iterations):
        sample_a = rng.choice(values_a, size=len(values_a), replace=True)
        sample_b = rng.choice(values_b, size=len(values_b), replace=True)
        estimates.append(sample_b.mean() - sample_a.mean())
    lower, upper = np.percentile(estimates, [2.5, 97.5])
    return {"lower": float(lower), "upper": float(upper)}


def compute_user_daily(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.execute(
        """
        SELECT
            user_id,
            event_date,
            region,
            CASE WHEN region IN ('IN-North', 'IN-South') THEN 'affected' ELSE 'unaffected' END AS cohort,
            CASE WHEN event_date >= DATE '2025-11-17' THEN 'post' ELSE 'pre' END AS period,
            SUM(CASE WHEN event_type = 'video_play' THEN 1 ELSE 0 END) AS video_plays
        FROM events
        GROUP BY 1,2,3,4,5;
        """
    ).fetchdf()


def get_metric_row(metric_tree: pd.DataFrame, cohort: str, period: str) -> pd.Series:
    row = metric_tree[(metric_tree["cohort"] == cohort) & (metric_tree["period"] == period)]
    if row.empty:
        raise ValueError(f"Missing metric_tree row for {cohort}/{period}")
    return row.iloc[0]


def make_figures(metric_tree: pd.DataFrame, segment: pd.DataFrame, funnel: pd.DataFrame, anomaly: pd.DataFrame) -> None:
    sns.set_theme(style="whitegrid")

    plt.figure(figsize=(9, 5))
    plot_tree = metric_tree.copy()
    plot_tree["label"] = plot_tree["cohort"] + " / " + plot_tree["period"]
    sns.barplot(data=plot_tree, x="label", y="plays_per_active_user", hue="cohort")
    plt.title("Plays per Active User Before and After Rollout")
    plt.xlabel("")
    plt.ylabel("Plays per active user")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "metric_tree.png", dpi=160)
    plt.close()

    region_summary = (
        segment.groupby(["period", "region"], as_index=False)
        .agg(plays_per_active_user=("plays_per_active_user", "mean"), bounce_rate=("bounce_rate", "mean"))
    )
    plt.figure(figsize=(10, 5))
    sns.barplot(data=region_summary, x="region", y="plays_per_active_user", hue="period")
    plt.title("Regional Engagement Drop")
    plt.xlabel("")
    plt.ylabel("Avg plays per active user")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "segment_drop.png", dpi=160)
    plt.close()

    funnel_plot = funnel.melt(
        id_vars=["cohort", "period"],
        value_vars=["impression_rate", "play_through_rate", "completion_rate", "bounce_rate"],
        var_name="stage",
        value_name="rate",
    )
    plt.figure(figsize=(10, 5))
    sns.barplot(data=funnel_plot, x="stage", y="rate", hue="cohort")
    plt.title("Funnel Health by Cohort")
    plt.xlabel("")
    plt.ylabel("Rate")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "funnel.png", dpi=160)
    plt.close()

    plt.figure(figsize=(11, 5))
    sns.lineplot(data=anomaly, x="event_date", y="plays_per_active_user", hue="region", marker="o")
    plt.axvline(pd.Timestamp("2025-11-17"), color="red", linestyle="--", label="v4.2 affected-region rollout")
    plt.title("Daily Plays per Active User with Rollout Marker")
    plt.xlabel("")
    plt.ylabel("Plays per active user")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "anomaly_detection.png", dpi=160)
    plt.close()


def build_summary(
    *,
    metric_tree: pd.DataFrame,
    funnel: pd.DataFrame,
    impact: pd.DataFrame,
    anomaly: pd.DataFrame,
    user_daily: pd.DataFrame,
    seed: int,
) -> dict:
    affected_pre = get_metric_row(metric_tree, "affected", "pre")
    affected_post = get_metric_row(metric_tree, "affected", "post")
    unaffected_pre = get_metric_row(metric_tree, "unaffected", "pre")
    unaffected_post = get_metric_row(metric_tree, "unaffected", "post")

    affected_delta = affected_post["plays_per_active_user"] - affected_pre["plays_per_active_user"]
    unaffected_delta = unaffected_post["plays_per_active_user"] - unaffected_pre["plays_per_active_user"]
    did = affected_delta - unaffected_delta
    affected_drop_pct = affected_delta / affected_pre["plays_per_active_user"]
    unaffected_drop_pct = unaffected_delta / unaffected_pre["plays_per_active_user"]

    affected_user_pre = user_daily[(user_daily["cohort"] == "affected") & (user_daily["period"] == "pre")][
        "video_plays"
    ].to_numpy()
    affected_user_post = user_daily[(user_daily["cohort"] == "affected") & (user_daily["period"] == "post")][
        "video_plays"
    ].to_numpy()
    affected_ci = bootstrap_difference(affected_user_pre, affected_user_post, seed=seed)

    affected_impact = impact[impact["cohort"] == "affected"].iloc[0]
    affected_funnel_pre = funnel[(funnel["cohort"] == "affected") & (funnel["period"] == "pre")].iloc[0]
    affected_funnel_post = funnel[(funnel["cohort"] == "affected") & (funnel["period"] == "post")].iloc[0]
    post_anomalies = anomaly[(anomaly["cohort"] == "affected") & (anomaly["anomaly_flag"] == True)]

    return {
        "business_question": "Did the recommendation model rollout create a localized engagement collapse?",
        "rollout_date": "2025-11-17",
        "affected_regions": sorted(AFFECTED_REGIONS),
        "primary_metric": "plays_per_active_user",
        "affected_pre_plays_per_user": float(affected_pre["plays_per_active_user"]),
        "affected_post_plays_per_user": float(affected_post["plays_per_active_user"]),
        "affected_drop_pct": float(affected_drop_pct),
        "unaffected_drop_pct": float(unaffected_drop_pct),
        "difference_in_differences": float(did),
        "bootstrap_ci_post_minus_pre": affected_ci,
        "affected_bounce_pre": float(affected_funnel_pre["bounce_rate"]),
        "affected_bounce_post": float(affected_funnel_post["bounce_rate"]),
        "affected_completion_pre": float(affected_funnel_pre["completion_rate"]),
        "affected_completion_post": float(affected_funnel_post["completion_rate"]),
        "lost_video_plays": float(affected_impact["lost_video_plays"]),
        "lost_watch_hours": float(affected_impact["lost_watch_seconds"] / 3600.0),
        "post_rollout_anomaly_days": int(len(post_anomalies)),
        "recommendation": (
            "Evidence supports rolling back v4.2 in IN-North and IN-South, then auditing "
            "ranking diversity and feature drift before re-launch."
        ),
        "causal_language": (
            "This synthetic RCA supports a rollout-related degradation; it is not a randomized "
            "causal experiment."
        ),
    }


def write_report(summary: dict) -> None:
    (REPORTS_DIR / "analysis_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report = f"""# Executive Summary: Recommendation Rollout Engagement Collapse

## Business Question

Did the recommendation model rollout on `{summary['rollout_date']}` create a localized engagement collapse?

## Key Findings

- Affected regions: `{', '.join(summary['affected_regions'])}`.
- Primary metric: `{summary['primary_metric']}`.
- Affected-region engagement moved from `{summary['affected_pre_plays_per_user']:.2f}` plays/user pre-rollout to `{summary['affected_post_plays_per_user']:.2f}` post-rollout.
- Affected-region change: `{summary['affected_drop_pct']:.1%}`.
- Unaffected-region change: `{summary['unaffected_drop_pct']:.1%}`.
- Difference-in-differences estimate: `{summary['difference_in_differences']:.3f}` plays/user.
- Bootstrap 95% CI for affected post-minus-pre: `[{summary['bootstrap_ci_post_minus_pre']['lower']:.3f}, {summary['bootstrap_ci_post_minus_pre']['upper']:.3f}]`.
- Estimated affected-region loss: `{summary['lost_video_plays']:.0f}` video plays and `{summary['lost_watch_hours']:.1f}` watch hours.

## Interpretation

The evidence supports a rollout-related degradation in the affected regions. The drop is visible in the primary engagement metric, funnel health, and post-rollout anomaly flags.

## Recommendation

{summary['recommendation']}

## Limitations

This is a deterministic synthetic case study. It demonstrates product analytics methodology, not a real production incident. The analysis is observational and should not be described as proof from a randomized experiment.
"""
    (REPORTS_DIR / "executive_summary.md").write_text(report, encoding="utf-8")


def main() -> int:
    args = parse_args()
    ensure_dirs()
    con = connect_events(Path(args.input))
    outputs = {
        "data_quality_checks": run_sql(con, "data_quality_checks.sql"),
        "metric_tree": run_sql(con, "metric_tree.sql"),
        "segment_drilldown": run_sql(con, "segment_drilldown.sql"),
        "funnel_analysis": run_sql(con, "funnel_analysis.sql"),
        "anomaly_detection": run_sql(con, "anomaly_detection.sql"),
        "impact_sizing": run_sql(con, "impact_sizing.sql"),
    }
    if not outputs["data_quality_checks"]["passed"].all():
        failed = outputs["data_quality_checks"].loc[~outputs["data_quality_checks"]["passed"], "check_name"].tolist()
        raise ValueError(f"Data quality checks failed: {failed}")

    user_daily = compute_user_daily(con)
    user_daily.to_csv(PROCESSED_DIR / "user_daily_metrics.csv", index=False)
    make_figures(
        outputs["metric_tree"],
        outputs["segment_drilldown"],
        outputs["funnel_analysis"],
        outputs["anomaly_detection"],
    )
    summary = build_summary(
        metric_tree=outputs["metric_tree"],
        funnel=outputs["funnel_analysis"],
        impact=outputs["impact_sizing"],
        anomaly=outputs["anomaly_detection"],
        user_daily=user_daily,
        seed=args.seed,
    )
    write_report(summary)
    print(
        "Analysis complete: "
        f"{summary['affected_drop_pct']:.1%} affected-region change, "
        f"{summary['lost_video_plays']:.0f} estimated lost plays."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
