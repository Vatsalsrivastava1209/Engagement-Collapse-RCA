"""Validate the synthetic engagement event contract."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = {
    "event_id",
    "user_id",
    "session_id",
    "event_type",
    "timestamp",
    "region",
    "device",
    "app_version",
    "model_version",
    "content_id",
    "content_category",
    "watch_seconds",
}
VALID_EVENTS = {"app_open", "home_impression", "video_play", "video_complete", "video_stop", "app_close"}
AFFECTED_REGIONS = {"IN-North", "IN-South"}
ROLLOUT_DATE = pd.Timestamp("2025-11-17", tz="UTC")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate engagement event data.")
    parser.add_argument("--input", default="data/raw/events.jsonl", help="Input JSONL file.")
    return parser.parse_args()


def fail(message: str) -> None:
    raise ValueError(message)


def load_events(path: Path) -> pd.DataFrame:
    if not path.exists():
        fail(f"Missing input file: {path}")
    if path.stat().st_size == 0:
        fail(f"Input file is empty: {path}")
    data = pd.read_json(path, lines=True)
    if data.empty:
        fail("Expected at least one event row.")
    return data


def validate_schema(data: pd.DataFrame) -> None:
    missing = sorted(REQUIRED_COLUMNS - set(data.columns))
    if missing:
        fail(f"Missing required columns: {missing}")
    if data["event_id"].duplicated().any():
        fail("event_id values must be unique.")
    if not data["event_type"].isin(VALID_EVENTS).all():
        invalid = sorted(set(data.loc[~data["event_type"].isin(VALID_EVENTS), "event_type"]))
        fail(f"Invalid event_type values: {invalid}")
    if data["watch_seconds"].isna().any() or (data["watch_seconds"] < 0).any():
        fail("watch_seconds must be non-null and non-negative.")


def validate_rollout(data: pd.DataFrame) -> None:
    timestamps = pd.to_datetime(data["timestamp"], utc=True, errors="coerce")
    if timestamps.isna().any():
        fail("All timestamps must parse as UTC datetimes.")
    data = data.assign(parsed_timestamp=timestamps)
    post = data["parsed_timestamp"] >= ROLLOUT_DATE
    affected = data["region"].isin(AFFECTED_REGIONS)
    invalid_v42 = data[(data["model_version"] == "v4.2") & ~(post & affected)]
    if not invalid_v42.empty:
        fail("model_version v4.2 may only appear after rollout in affected regions.")
    missing_v42 = data[post & affected & (data["model_version"] != "v4.2")]
    if not missing_v42.empty:
        fail("Affected post-rollout events must use model_version v4.2.")
    unaffected_v42 = data[(~affected) & (data["model_version"] == "v4.2")]
    if not unaffected_v42.empty:
        fail("Unaffected regions must remain on model_version v4.1.")


def validate_session_order(data: pd.DataFrame) -> None:
    order = {
        "app_open": 1,
        "home_impression": 2,
        "video_play": 3,
        "video_complete": 4,
        "video_stop": 4,
        "app_close": 5,
    }
    data = data.assign(
        parsed_timestamp=pd.to_datetime(data["timestamp"], utc=True),
        event_order=data["event_type"].map(order),
    ).sort_values(["session_id", "parsed_timestamp", "event_order"])
    first_events = data.groupby("session_id")["event_type"].first()
    if (first_events != "app_open").any():
        fail("Every session must start with app_open.")
    has_impression = data.groupby("session_id")["event_type"].apply(lambda values: "home_impression" in set(values))
    if (~has_impression).any():
        fail("Every session must include home_impression.")

    session_events = data.groupby("session_id")["event_type"].agg(list)
    for session_id, events in session_events.items():
        if "video_complete" in events and "video_stop" in events:
            fail(f"Session {session_id} has both video_complete and video_stop.")
        if ("video_complete" in events or "video_stop" in events) and "video_play" not in events:
            fail(f"Session {session_id} has a terminal video event without video_play.")


def validate(path: Path) -> pd.DataFrame:
    data = load_events(path)
    validate_schema(data)
    validate_rollout(data)
    validate_session_order(data)
    return data


def main() -> int:
    args = parse_args()
    data = validate(Path(args.input))
    print(
        "Validation passed: "
        f"{len(data):,} events, {data['user_id'].nunique():,} users, "
        f"{data['session_id'].nunique():,} sessions."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(f"Validation failed: {exc}")
        raise SystemExit(1)
