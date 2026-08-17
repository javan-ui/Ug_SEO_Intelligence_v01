from __future__ import annotations

from typing import Any


def rankability_score(parsed: dict[str, Any], competitors: list[dict[str, Any]], pages: list[dict[str, Any]]) -> tuple[float, list[str]]:
    if not competitors:
        return 50.0, ["SERP sample unavailable; rankability confidence is limited"]
    weak_pages = [page for page in pages if not page.get("fetch_failed") and (page.get("content_depth_score", 0) < 45 or page.get("local_relevance_score", 0) < 50)]
    directories = sum(1 for item in competitors if item.get("domain_type") == "DIRECTORY")
    local_gap = sum(1 for item in competitors if item.get("country_relevance", 0) < 50)
    score = 45.0 + min(25.0, len(weak_pages) * 5) + min(15.0, directories * 3) + min(15.0, local_gap * 2)
    score -= min(25.0, sum(1 for item in competitors if item.get("domain_type") == "GOVERNMENT") * 5)
    reasons = [
        f"{len(weak_pages)} fetched pages show an observed content/local weakness",
        f"{directories} directory-like results appear in the top sample",
        f"{local_gap} results have limited Uganda-specific evidence",
    ]
    return round(max(0.0, min(100.0, score)), 2), reasons