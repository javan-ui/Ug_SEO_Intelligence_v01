from __future__ import annotations

from typing import Any


def competition_score(parsed: dict[str, Any], competitors: list[dict[str, Any]], pages: list[dict[str, Any]]) -> tuple[float, list[str]]:
    if not competitors:
        return 20.0, ["no organic competitor sample available"]
    strong = sum(1 for item in competitors if item.get("domain_type") in {"INTERNATIONAL_COMPANY", "GOVERNMENT"} or item.get("country_relevance", 0) >= 80)
    local = sum(1 for item in competitors if item.get("domain_type") in {"LOCAL_AGENCY", "LOCAL_BUSINESS"})
    page_strength = sum(float(page.get("content_depth_score", 0)) for page in pages if not page.get("fetch_failed"))
    page_count = max(1, len([page for page in pages if not page.get("fetch_failed")]))
    feature_pressure = sum(10 for value in parsed.get("features", {}).values() if value)
    score = min(100.0, (strong / len(competitors)) * 45 + (local / len(competitors)) * 20 + (page_strength / page_count) * 0.2 + feature_pressure * 0.5)
    reasons = [
        f"{strong}/{len(competitors)} results appear strong or institutionally established",
        f"{local}/{len(competitors)} results appear locally relevant business pages",
        f"{len(pages)} competitor page fetches available",
    ]
    return round(score, 2), reasons