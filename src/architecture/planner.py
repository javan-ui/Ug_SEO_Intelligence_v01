from __future__ import annotations

from typing import Any

from src.utils.text import slugify, top_terms


def _priority(record: dict[str, Any]) -> str:
    opportunity = float(record.get("opportunity", 0))
    commercial = float(record.get("commercial_value", 0))
    if opportunity >= 72 and commercial >= 65:
        return "P0"
    if opportunity >= 55:
        return "P1"
    if opportunity >= 38:
        return "P2"
    return "P3"


def build_recommendations(
    clusters: list[dict[str, Any]],
    records_by_keyword: dict[str, dict[str, Any]],
    serp_by_keyword: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    for cluster in clusters:
        primary = cluster["primary_keyword"]
        record = records_by_keyword.get(primary, {})
        priority = _priority(record)
        related = [keyword for keyword in cluster["keywords"] if keyword != primary]
        slug = slugify(primary)
        recommendations.append(
            {
                "page_type": "commercial_landing_page" if record.get("commercial_value", 0) >= 60 else "supporting_resource",
                "primary_keyword": primary,
                "secondary_keywords": related[:12],
                "intent": record.get("intents", ["MIXED"]),
                "opportunity_score": record.get("opportunity", 0),
                "recommended_url": f"/{slug}/",
                "recommended_title": f"{primary.title()} | Uganda",
                "recommended_h1": primary.title(),
                "supporting_topics": top_terms([primary, *related], 10),
                "internal_link_targets": [],
                "reason_for_creation": "; ".join(record.get("reasons", [])[:4]) or "cluster has observed search evidence",
                "priority": priority,
                "content_brief": {
                    "primary_keyword": primary,
                    "secondary_keywords": related[:12],
                    "search_intent": record.get("intents", ["MIXED"]),
                    "target_audience": "Ugandan businesses seeking stronger online visibility",
                    "recommended_page_purpose": "Answer the observed search intent with Uganda-specific service evidence.",
                    "suggested_title": f"{primary.title()} | Uganda",
                    "suggested_h1": primary.title(),
                    "suggested_h2_topics": top_terms([primary, *related], 8),
                    "questions_to_answer": ["What does this service include?", "What does it cost or depend on?", "Why choose a Uganda-focused provider?"],
                    "competitor_content_gaps": ["Use actual fetched-page weaknesses from the report; do not assume a gap caused a ranking."],
                    "uganda_specific_details": ["Uganda pricing/context where appropriate", "Local delivery and support expectations", "Relevant city or sector examples"],
                    "trust_signals": ["Business identity", "Contact details", "Portfolio or case evidence", "Clear service scope"],
                    "recommended_internal_links": [],
                    "recommended_cta_type": "request a consultation or quote",
                },
            }
        )
    recommendations.sort(key=lambda item: ({"P0": 0, "P1": 1, "P2": 2, "P3": 3}[item["priority"]], -float(item["opportunity_score"])))
    for index, recommendation in enumerate(recommendations):
        recommendation["internal_link_targets"] = [
            other["recommended_url"]
            for other in recommendations[max(0, index - 2) : index]
            if other["recommended_url"] != recommendation["recommended_url"]
        ]
        recommendation["content_brief"]["recommended_internal_links"] = recommendation["internal_link_targets"]
    return recommendations


def architecture_tree(recommendations: list[dict[str, Any]]) -> dict[str, Any]:
    pages = [
        {
            "path": recommendation["recommended_url"],
            "page_type": recommendation["page_type"],
            "primary_keyword": recommendation["primary_keyword"],
            "priority": recommendation["priority"],
        }
        for recommendation in recommendations
    ]
    return {"root": "/", "pages": pages, "execution_order": ["P0", "P1", "P2", "P3"]}