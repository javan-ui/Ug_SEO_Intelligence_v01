from __future__ import annotations

from typing import Any


def evidence_confidence(parsed: dict[str, Any], pages: list[dict[str, Any]], source_count: int) -> float:
    organic = len(parsed.get("organic", []))
    fetched = len([page for page in pages if not page.get("fetch_failed")])
    score = min(100.0, organic * 6 + fetched * 3 + min(20, source_count * 5))
    return round(score, 2)