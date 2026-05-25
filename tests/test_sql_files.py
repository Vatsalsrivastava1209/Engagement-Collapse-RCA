from __future__ import annotations

from pathlib import Path


def test_sql_files_are_not_empty() -> None:
    sql_files = sorted(Path("sql").glob("*.sql"))
    assert sql_files
    for path in sql_files:
        text = path.read_text(encoding="utf-8").strip()
        assert len(text) > 100, f"{path} should contain a real query"
        assert "SELECT" in text.upper()
