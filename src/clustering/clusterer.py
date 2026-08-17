from __future__ import annotations

from collections import defaultdict
from typing import Any

from src.utils.text import jaccard, tokenize


def serp_similarity(a: dict[str, Any], b: dict[str, Any]) -> float:
    a_urls = {item.get("link") for item in a.get("organic", []) if item.get("link")}
    b_urls = {item.get("link") for item in b.get("organic", []) if item.get("link")}
    if not a_urls and not b_urls:
        return 0.0
    return len(a_urls & b_urls) / max(1, min(len(a_urls), len(b_urls)))


def cluster_keywords(records: list[dict[str, Any]], serp_by_keyword: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    clusters: list[dict[str, Any]] = []
    assigned: set[str] = set()
    next_id = 1
    ordered = sorted(records, key=lambda item: item.get("opportunity", 0), reverse=True)
    for record in ordered:
        keyword = record["keyword"]
        if keyword in assigned:
            continue
        cluster_keywords_list = [keyword]
        assigned.add(keyword)
        for candidate in ordered:
            other = candidate["keyword"]
            if other in assigned:
                continue
            lexical = jaccard(tokenize(keyword), tokenize(other))
            serp = serp_similarity(serp_by_keyword.get(keyword, {}), serp_by_keyword.get(other, {}))
            if lexical >= 0.42 or serp >= 0.6:
                cluster_keywords_list.append(other)
                assigned.add(other)
        clusters.append(
            {
                "cluster_id": next_id,
                "primary_keyword": keyword,
                "keywords": cluster_keywords_list,
                "serp_similarity_evidence": {
                    other: round(serp_similarity(serp_by_keyword.get(keyword, {}), serp_by_keyword.get(other, {})), 3)
                    for other in cluster_keywords_list
                    if other != keyword
                },
            }
        )
        next_id += 1
    return clusters


def cannibalization_warnings(clusters: list[dict[str, Any]], serp_by_keyword: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    for cluster in clusters:
        keywords = cluster.get("keywords", [])
        for index, first in enumerate(keywords):
            for second in keywords[index + 1 :]:
                similarity = serp_similarity(serp_by_keyword.get(first, {}), serp_by_keyword.get(second, {}))
                if similarity >= 0.6:
                    warnings.append(
                        {
                            "page_a": first,
                            "page_b": second,
                            "shared_serp_ratio": round(similarity, 2),
                            "evidence": f"{round(similarity * 10)} of the top 10 URLs overlap where available",
                            "recommendation": "Consider one primary page unless stronger evidence supports separate pages.",
                        }
                    )
    return warnings