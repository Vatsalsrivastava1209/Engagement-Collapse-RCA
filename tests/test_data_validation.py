from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from scripts.validate_data import validate, validate_rollout


def test_generated_data_validates(tmp_path: Path) -> None:
    output = tmp_path / "events.jsonl"
    subprocess.run(
        [
            sys.executable,
            "scripts/generate_synthetic_data.py",
            "--output",
            str(output),
            "--users",
            "120",
            "--days",
            "14",
        ],
        check=True,
    )
    data = validate(output)
    assert not data.empty
    assert data["event_id"].is_unique
    assert {"v4.1", "v4.2"}.issubset(set(data["model_version"]))


def test_v42_before_rollout_fails() -> None:
    data = pd.DataFrame(
        [
            {
                "event_id": "e1",
                "user_id": 1,
                "session_id": "s1",
                "event_type": "app_open",
                "timestamp": "2025-11-16T00:00:00Z",
                "region": "IN-North",
                "device": "android",
                "app_version": "1.10.0",
                "model_version": "v4.2",
                "content_id": None,
                "content_category": None,
                "watch_seconds": 0,
            }
        ]
    )
    with pytest.raises(ValueError, match="v4.2 may only appear"):
        validate_rollout(data)


def test_event_ids_are_unique_in_committed_data() -> None:
    path = Path("data/raw/events.jsonl")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    event_ids = [row["event_id"] for row in rows]
    assert len(event_ids) == len(set(event_ids))
