from __future__ import annotations

from typing import Any

from src.serper.client import SerperClient
from src.serp.parser import parse_serp
from src.utils.storage_types import now_iso


def expand_seeds(seeds: list[dict[str, str]], client: SerperClient, logger: Any, max_seeds: int | None = None) -> list[dict[str, str]]:
    records = list(seeds if max_seeds is None else seeds[:max_seeds])
    initial_seeds = list(records)
    for index, seed in enumerate(initial_seeds, 1):
        logger.info("[DISCOVERY] Seed %s/%s: %s", index, len(records), seed["keyword"])
        result = client.search(seed["keyword"], num=10)
        if result.response is None:
            continue
        parsed = parse_serp(result.response)
        discovered: list[dict[str, str]] = []
        for organic in parsed.get("organic", []):
            text = f"{organic.get('title', '')} {organic.get('snippet', '')}".strip()
            if text:
                discovered.append(
                    {
                        "keyword": text,
                        "source_seed": seed["keyword"],
                        "discovery_method": "organic_title_or_snippet",
                        "discovery_query": seed["keyword"],
                        "first_seen": now_iso(),
                    }
                )
        for question in parsed.get("people_also_ask", []):
            if question.get("question"):
                discovered.append(
                    {
                        "keyword": question["question"],
                        "source_seed": seed["keyword"],
                        "discovery_method": "people_also_ask",
                        "discovery_query": seed["keyword"],
                        "first_seen": now_iso(),
                    }
                )
        for related in parsed.get("related_searches", []):
            discovered.append(
                {
                    "keyword": related,
                    "source_seed": seed["keyword"],
                    "discovery_method": "related_search",
                    "discovery_query": seed["keyword"],
                    "first_seen": now_iso(),
                }
            )
        records.extend(discovered)
    return records