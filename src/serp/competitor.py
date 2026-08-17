from __future__ import annotations

from typing import Any

from src.utils.urls import domain_from_url


LOCAL_TLDS = (".ug", ".co.ug", ".org.ug", ".ac.ug", ".go.ug")
DIRECTORY_WORDS = ("directory", "yellowpages", "listing", "tripadvisor", "yelp")
GOVERNMENT_WORDS = (".go.ug", "government", "ministry")
EDUCATION_WORDS = (".ac.ug", "university", "school", "college")


def identify_competitors(keyword: str, parsed: dict[str, Any]) -> list[dict[str, Any]]:
    competitors: list[dict[str, Any]] = []
    for result in parsed.get("organic", []):
        domain = result.get("domain") or domain_from_url(result.get("link", ""))
        lower = f"{domain} {result.get('title', '')} {result.get('snippet', '')}".casefold()
        if any(word in lower for word in GOVERNMENT_WORDS):
            domain_type = "GOVERNMENT"
        elif any(word in lower for word in EDUCATION_WORDS):
            domain_type = "EDUCATIONAL"
        elif any(word in lower for word in DIRECTORY_WORDS):
            domain_type = "DIRECTORY"
        elif any(term in lower for term in ("news", "daily", "monitor")):
            domain_type = "NEWS"
        elif any(term in lower for term in ("facebook", "instagram", "linkedin", "youtube")):
            domain_type = "SOCIAL"
        elif any(term in lower for term in ("agency", "design", "web", "digital", "seo", "studio")):
            domain_type = "LOCAL_AGENCY" if domain.endswith(LOCAL_TLDS) or "uganda" in lower else "INTERNATIONAL_COMPANY"
        else:
            domain_type = "LOCAL_BUSINESS" if domain.endswith(LOCAL_TLDS) else "OTHER"
        country_relevance = 85.0 if domain.endswith(LOCAL_TLDS) else 65.0 if "uganda" in lower else 25.0
        competitors.append(
            {
                "keyword": keyword,
                "position": result.get("position"),
                "url": result.get("link"),
                "domain": domain,
                "title": result.get("title"),
                "snippet": result.get("snippet"),
                "domain_type": domain_type,
                "country_relevance": country_relevance,
                "business_type": domain_type,
                "page_type": "service_page" if "service" in lower or "design" in lower else "general_page",
                "confidence": 65.0 if domain_type != "OTHER" else 40.0,
            }
        )
    return competitors