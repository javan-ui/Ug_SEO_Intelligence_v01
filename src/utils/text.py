from __future__ import annotations

import re
from collections import Counter


def normalize_keyword(value: str) -> str:
    value = value.casefold().strip()
    value = re.sub(r"[^\w\s&'-]", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def slugify(value: str) -> str:
    words = re.findall(r"[a-z0-9]+", value.casefold())
    return "-".join(words)


def tokenize(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.casefold()))


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / max(1, len(a | b))


def top_terms(values: list[str], limit: int = 12) -> list[str]:
    counts = Counter(token for value in values for token in tokenize(value))
    return [term for term, _ in counts.most_common(limit)]


def html_escape(value: object) -> str:
    from html import escape

    return escape(str(value), quote=True)