from __future__ import annotations

from typing import Any

from src.utils.urls import domain_from_url


def parse_serp(response: dict[str, Any]) -> dict[str, Any]:
    organic: list[dict[str, Any]] = []
    for index, result in enumerate(response.get("organic", []) or [], 1):
        if not isinstance(result, dict):
            continue
        link = str(result.get("link", ""))
        organic.append(
            {
                "position": result.get("position", index),
                "title": result.get("title", ""),
                "link": link,
                "snippet": result.get("snippet", ""),
                "domain": domain_from_url(link) if link else "",
                "display_domain": result.get("displayedLink") or result.get("displayLink") or domain_from_url(link),
                "sitelinks": result.get("sitelinks", []),
                "attributes": result.get("attributes", {}),
                "date": result.get("date"),
            }
        )
    paa = []
    for item in response.get("peopleAlsoAsk", []) or []:
        if isinstance(item, dict):
            paa.append({"question": item.get("question", ""), "answer": item.get("snippet") or item.get("answer", "")})
    related = []
    for item in response.get("relatedSearches", []) or []:
        if isinstance(item, dict):
            related.append(item.get("query", ""))
        elif item:
            related.append(str(item))
    return {
        "organic": organic,
        "knowledge_graph": response.get("knowledgeGraph"),
        "answer_box": response.get("answerBox"),
        "people_also_ask": [item for item in paa if item["question"]],
        "related_searches": [item for item in related if item],
        "places": response.get("places", []),
        "features": detect_features(response),
    }


def detect_features(response: dict[str, Any]) -> dict[str, bool]:
    organic = response.get("organic", []) or []
    return {
        "has_answer_box": bool(response.get("answerBox")),
        "has_knowledge_graph": bool(response.get("knowledgeGraph")),
        "has_people_also_ask": bool(response.get("peopleAlsoAsk")),
        "has_local_pack_or_places": bool(response.get("places")),
        "has_video_results": bool(response.get("videos")),
        "has_news_results": bool(response.get("news")),
        "has_shopping_results": bool(response.get("shopping")),
        "has_sitelinks": any(isinstance(item, dict) and item.get("sitelinks") for item in organic),
    }