from __future__ import annotations

import re
from typing import Any

from src.pages.fetcher import FetchResult, strip_html
from src.pages.parser import parse_html


def analyze_page(result: FetchResult, keyword: str) -> dict[str, Any]:
    analysis: dict[str, Any] = {
        "url": result.url,
        "keyword": keyword,
        "final_url": result.final_url,
        "fetch_failed": result.failed,
        "reason": result.reason,
        "fetch_method": result.method,
    }
    if result.failed or not result.html:
        return analysis
    parser = parse_html(result.html, result.final_url or result.url)
    body_text = strip_html(result.html)
    lower_keyword = keyword.casefold()
    first_words = body_text.casefold()[:2_000]
    title = parser.title
    h1_text = " ".join(parser.headings["h1"])
    meta_description = parser.meta.get("description", "")
    internal_links = [link for link in parser.links if parser.base_url.split("/")[2] in link["href"]]
    external_links = [link for link in parser.links if link not in internal_links]
    image_alt_coverage = (
        sum(1 for image in parser.images if image["alt"].strip()) / len(parser.images) * 100
        if parser.images
        else 100.0
    )
    analysis.update(
        {
            "title": title,
            "meta_description": meta_description,
            "h1": h1_text,
            "h2_count": len(parser.headings["h2"]),
            "h3_count": len(parser.headings["h3"]),
            "word_count": len(re.findall(r"\b\w+\b", body_text)),
            "paragraph_count": len(parser.paragraphs),
            "image_count": len(parser.images),
            "image_alt_coverage": round(image_alt_coverage, 2),
            "internal_link_count": len(internal_links),
            "external_link_count": len(external_links),
            "canonical": parser.meta.get("canonical"),
            "robots_meta": parser.meta.get("robots"),
            "schema_types": parser.schema_types,
            "language": parser.meta.get("language") or parser.meta.get("og:locale"),
            "https": (result.final_url or result.url).startswith("https://"),
            "mobile_meta": "viewport" in parser.meta,
            "open_graph": any(key.startswith("og:") for key in parser.meta),
            "twitter_card": "twitter:card" in parser.meta,
            "keyword_in_title": lower_keyword in title.casefold(),
            "keyword_in_h1": lower_keyword in h1_text.casefold(),
            "keyword_in_url": lower_keyword.replace(" ", "-") in (result.final_url or result.url).casefold(),
            "keyword_in_meta_description": lower_keyword in meta_description.casefold(),
            "keyword_in_first_200_words": lower_keyword in first_words,
            "content_depth_score": min(100.0, len(re.findall(r"\b\w+\b", body_text)) / 10),
            "topic_coverage_score": min(100.0, (len(parser.headings["h2"]) * 10) + (len(parser.headings["h3"]) * 4) + (len(parser.paragraphs) * 2)),
            "local_relevance_score": 75.0 if "uganda" in body_text.casefold() or ".ug" in (result.final_url or result.url) else 25.0,
            "commercial_alignment_score": 75.0 if any(term in body_text.casefold() for term in ("contact", "quote", "price", "services", "call")) else 35.0,
            "page_structure_score": min(100.0, (20 if title else 0) + (20 if h1_text else 0) + (len(parser.headings["h2"]) * 8) + (20 if parser.paragraphs else 0)),
            "technical_optimization_score": min(100.0, (20 if result.final_url and result.final_url.startswith("https://") else 0) + (20 if parser.meta.get("description") else 0) + (20 if "viewport" in parser.meta else 0) + (20 if parser.meta.get("canonical") else 0) + (20 if parser.meta.get("has_json_ld") else 0)),
        }
    )
    analysis["observed_weaknesses"] = observed_weaknesses(analysis)
    return analysis


def observed_weaknesses(analysis: dict[str, Any]) -> list[str]:
    weaknesses: list[str] = []
    if not analysis.get("title"):
        weaknesses.append("missing title")
    if not analysis.get("h1"):
        weaknesses.append("missing H1")
    if not analysis.get("meta_description"):
        weaknesses.append("missing meta description")
    if analysis.get("word_count", 0) < 450:
        weaknesses.append("thin page by observed word count")
    if analysis.get("local_relevance_score", 0) < 50:
        weaknesses.append("limited Uganda-specific evidence")
    if analysis.get("topic_coverage_score", 0) < 35:
        weaknesses.append("limited heading/topic coverage")
    return weaknesses