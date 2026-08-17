from __future__ import annotations

from typing import Any


def serp_evidence_score(parsed: dict[str, Any]) -> dict[str, Any]:
    organic = parsed.get("organic", [])
    features = parsed.get("features", {})
    related = parsed.get("related_searches", [])
    paa = parsed.get("people_also_ask", [])
    demand = min(100.0, len(related) * 7.0 + len(paa) * 8.0 + min(25.0, len(organic) * 1.5))
    pressure = sum(10 for value in features.values() if value)
    confidence = min(100.0, len(organic) * 7.0 + len(related) * 4.0 + len(paa) * 5.0)
    return {
        "demand_signal": round(demand, 2),
        "demand_confidence": "HIGH" if confidence >= 75 else "MEDIUM" if confidence >= 40 else "LOW",
        "serp_feature_pressure": min(100.0, pressure),
        "evidence_confidence": round(confidence, 2),
    }