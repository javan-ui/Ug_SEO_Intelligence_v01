from __future__ import annotations

from typing import Any

from src.discovery.normalizer import normalize_records
from src.filtering.intent import classify_intent
from src.filtering.relevance import score_relevance, should_retain


def build_candidate_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Normalize, score, and split candidates without deleting filtered evidence."""
    retained: list[dict[str, Any]] = []
    filtered: list[dict[str, Any]] = []
    for record in normalize_records(records):
        keyword = record["keyword"]
        enriched = {**record, **score_relevance(keyword), **classify_intent(keyword)}
        keep, reason = should_retain(keyword)
        enriched["retained"] = keep
        if keep:
            retained.append(enriched)
        else:
            filtered.append({**enriched, "filtered_reason": reason})
    return retained, filtered