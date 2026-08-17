from __future__ import annotations

from config.seeds import LOCATIONS
from src.utils.text import tokenize

BUSINESS_TERMS = {
    "website", "web", "design", "development", "developer", "designer", "agency",
    "business", "ecommerce", "shop", "store", "seo", "google", "hosting", "domain",
    "wordpress", "online", "company", "services", "maintenance", "email",
}
IRRELEVANT_TERMS = {"html", "css", "javascript", "python", "github", "jobs", "template", "download"}


def score_relevance(keyword: str) -> dict[str, float]:
    tokens = tokenize(keyword)
    business = min(100.0, len(tokens & BUSINESS_TERMS) * 22.0)
    local = 65.0 if "uganda" in tokens else 0.0
    local += min(30.0, sum(20.0 for location in LOCATIONS if location.casefold() in keyword.casefold()))
    local = min(100.0, local)
    penalty = min(50.0, len(tokens & IRRELEVANT_TERMS) * 10.0)
    relevance = max(0.0, min(100.0, business + local * 0.25 - penalty))
    return {
        "relevance_score": round(relevance, 2),
        "local_relevance": round(local, 2),
        "business_relevance": round(max(0.0, business - penalty), 2),
    }


def should_retain(keyword: str) -> tuple[bool, str]:
    scores = score_relevance(keyword)
    if scores["business_relevance"] < 20:
        return False, "insufficient website/business relevance"
    if any(term in keyword.casefold().split() for term in ("celebrity", "football", "weather", "lyrics")):
        return False, "unrelated search topic"
    return True, ""