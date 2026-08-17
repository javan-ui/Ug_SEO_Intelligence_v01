from __future__ import annotations

from typing import Any


def demand_score(parsed: dict[str, Any], discovery_count: int = 1) -> tuple[float, str, list[str]]:
    related = len(parsed.get("related_searches", []))
    paa = len(parsed.get("people_also_ask", []))
    organic = len(parsed.get("organic", []))
    score = min(100.0, related * 7 + paa * 8 + min(25, organic * 1.5) + min(25, discovery_count * 4))
    confidence_value = min(100, organic * 7 + related * 4 + paa * 5)
    confidence = "HIGH" if confidence_value >= 75 else "MEDIUM" if confidence_value >= 40 else "LOW"
    reasons = [
        f"{related} related-search signals observed",
        f"{paa} People Also Ask signals observed",
        f"candidate was discovered through {discovery_count} source path(s)",
    ]
    return round(score, 2), confidence, reasons