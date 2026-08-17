from __future__ import annotations

from config.seeds import LOCATIONS
from src.utils.text import normalize_keyword


def normalize_records(records: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for record in records:
        keyword = normalize_keyword(record.get("keyword", ""))
        if not keyword:
            continue
        record = {**record, "keyword": keyword}
        if keyword not in merged:
            merged[keyword] = record
        else:
            existing = merged[keyword]
            existing["source_seed"] = f"{existing.get('source_seed', '')}; {record.get('source_seed', '')}".strip("; ")
            existing["discovery_method"] = f"{existing.get('discovery_method', '')}; {record.get('discovery_method', '')}".strip("; ")
    return list(merged.values())


def plausible_location_expansions(keyword: str) -> list[str]:
    lower = keyword.casefold()
    if any(token in lower for token in ("website", "web design", "seo", "online store", "hosting")) and any(
        token in lower for token in ("uganda", "kampala")
    ):
        return [normalize_keyword(f"{keyword} {location}") for location in LOCATIONS if location.casefold() not in lower][:3]
    return []