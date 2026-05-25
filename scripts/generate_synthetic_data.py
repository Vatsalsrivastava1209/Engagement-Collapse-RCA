"""Generate deterministic synthetic clickstream data for the RCA case study."""

from __future__ import annotations

import argparse
import json
import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


REGIONS = ["IN-North", "IN-South", "IN-East", "IN-West", "EU-West", "US-East", "APAC"]
AFFECTED_REGIONS = {"IN-North", "IN-South"}
DEVICES = ["android", "ios", "smart_tv", "web"]
APP_VERSIONS = ["1.9.0", "1.9.1", "1.10.0"]
CONTENT_CATEGORIES = ["sports", "movies", "news", "comedy", "music", "education"]
EVENT_TYPES = ["app_open", "home_impression", "video_play", "video_complete", "video_stop", "app_close"]
ROLLOUT_DATE = datetime(2025, 11, 17, tzinfo=timezone.utc).date()


@dataclass(frozen=True)
class UserProfile:
    user_id: int
    region: str
    device: str
    app_version: str
    base_active_probability: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic engagement logs.")
    parser.add_argument("--output", default="data/raw/events.jsonl", help="JSONL output path.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--users", type=int, default=1800, help="Number of synthetic users.")
    parser.add_argument("--days", type=int, default=14, help="Number of days to generate.")
    return parser.parse_args()


def iso_timestamp(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def make_event(
    *,
    user: UserProfile,
    session_id: str,
    event_type: str,
    ts: datetime,
    model_version: str,
    content_id: str | None = None,
    content_category: str | None = None,
    watch_seconds: int = 0,
) -> dict:
    event_key = f"{session_id}:{event_type}:{iso_timestamp(ts)}:{content_id or 'none'}:{watch_seconds}"
    return {
        "event_id": str(uuid.uuid5(uuid.NAMESPACE_URL, event_key)),
        "user_id": user.user_id,
        "session_id": session_id,
        "event_type": event_type,
        "timestamp": iso_timestamp(ts),
        "region": user.region,
        "device": user.device,
        "app_version": user.app_version,
        "model_version": model_version,
        "content_id": content_id,
        "content_category": content_category,
        "watch_seconds": watch_seconds,
    }


def build_users(count: int) -> list[UserProfile]:
    users: list[UserProfile] = []
    region_weights = [0.18, 0.17, 0.12, 0.12, 0.13, 0.13, 0.15]
    device_weights = [0.48, 0.30, 0.12, 0.10]
    version_weights = [0.18, 0.34, 0.48]
    for user_id in range(1, count + 1):
        users.append(
            UserProfile(
                user_id=user_id,
                region=random.choices(REGIONS, weights=region_weights, k=1)[0],
                device=random.choices(DEVICES, weights=device_weights, k=1)[0],
                app_version=random.choices(APP_VERSIONS, weights=version_weights, k=1)[0],
                base_active_probability=random.uniform(0.58, 0.82),
            )
        )
    return users


def session_profile(user: UserProfile, day: datetime) -> tuple[str, float, float, tuple[int, int]]:
    post_rollout = day.date() >= ROLLOUT_DATE
    affected = user.region in AFFECTED_REGIONS
    if post_rollout and affected:
        return "v4.2", 0.31, 0.38, (20, 110)
    return "v4.1", 0.08, 0.64, (60, 260)


def generate_session(user: UserProfile, day: datetime, session_number: int) -> list[dict]:
    start = day + timedelta(
        hours=random.choices([8, 12, 18, 21], weights=[0.18, 0.20, 0.42, 0.20], k=1)[0],
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    session_id = f"{user.user_id}-{day.date()}-{session_number}"
    model_version, bounce_probability, completion_probability, watch_range = session_profile(user, day)
    category_pool = CONTENT_CATEGORIES
    if model_version == "v4.2":
        category_pool = ["news", "education", "movies"]
    content_category = random.choice(category_pool)
    content_id = f"{content_category[:3].upper()}-{random.randint(1000, 1099)}"

    events = [
        make_event(user=user, session_id=session_id, event_type="app_open", ts=start, model_version=model_version),
        make_event(
            user=user,
            session_id=session_id,
            event_type="home_impression",
            ts=start + timedelta(seconds=2),
            model_version=model_version,
            content_id=content_id,
            content_category=content_category,
        ),
    ]

    if random.random() < bounce_probability:
        events.append(
            make_event(
                user=user,
                session_id=session_id,
                event_type="app_close",
                ts=start + timedelta(seconds=random.randint(8, 35)),
                model_version=model_version,
            )
        )
        return events

    play_ts = start + timedelta(seconds=random.randint(4, 16))
    watch_seconds = random.randint(*watch_range)
    events.append(
        make_event(
            user=user,
            session_id=session_id,
            event_type="video_play",
            ts=play_ts,
            model_version=model_version,
            content_id=content_id,
            content_category=content_category,
            watch_seconds=watch_seconds,
        )
    )
    completion_event = "video_complete" if random.random() < completion_probability else "video_stop"
    events.append(
        make_event(
            user=user,
            session_id=session_id,
            event_type=completion_event,
            ts=play_ts + timedelta(seconds=watch_seconds),
            model_version=model_version,
            content_id=content_id,
            content_category=content_category,
            watch_seconds=watch_seconds if completion_event == "video_complete" else 0,
        )
    )
    events.append(
        make_event(
            user=user,
            session_id=session_id,
            event_type="app_close",
            ts=play_ts + timedelta(seconds=watch_seconds + random.randint(3, 30)),
            model_version=model_version,
        )
    )
    return events


def generate_events(users: list[UserProfile], days: int) -> list[dict]:
    start_date = datetime(2025, 11, 10, tzinfo=timezone.utc)
    events: list[dict] = []
    for offset in range(days):
        day = start_date + timedelta(days=offset)
        weekday_lift = 0.05 if day.weekday() in {5, 6} else 0.0
        for user in users:
            if random.random() > min(0.92, user.base_active_probability + weekday_lift):
                continue
            session_count = 1 + int(random.random() < 0.22)
            for session_number in range(1, session_count + 1):
                events.extend(generate_session(user, day, session_number))
    return events


def main() -> int:
    args = parse_args()
    random.seed(args.seed)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    users = build_users(args.users)
    events = generate_events(users, args.days)

    with output.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, sort_keys=True) + "\n")

    print(f"Generated {len(events):,} events for {args.users:,} users at {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
