from __future__ import annotations

from config.scoring import OPPORTUNITY_WEIGHTS


def opportunity_score(
    demand_signal: float,
    rankability: float,
    commercial_value: float,
    uganda_relevance: float,
    *,
    competition: float = 0,
    irrelevant: bool = False,
    local_gap: bool = False,
) -> tuple[float, list[str]]:
    raw = (
        demand_signal * OPPORTUNITY_WEIGHTS["demand_signal"]
        + rankability * OPPORTUNITY_WEIGHTS["rankability"]
        + commercial_value * OPPORTUNITY_WEIGHTS["commercial_value"]
        + uganda_relevance * OPPORTUNITY_WEIGHTS["uganda_relevance"]
    )
    penalties = 0.0
    bonuses = 0.0
    reasons = [
        f"demand signal contributes {demand_signal:.1f} at 25%",
        f"rankability contributes {rankability:.1f} at 30%",
        f"commercial value contributes {commercial_value:.1f} at 25%",
        f"Uganda relevance contributes {uganda_relevance:.1f} at 20%",
    ]
    if competition >= 85:
        penalties += 10
        reasons.append("penalty for extreme SERP dominance")
    if irrelevant:
        penalties += 30
        reasons.append("penalty for irrelevant intent")
    if local_gap:
        bonuses += 6
        reasons.append("bonus for an observed local gap")
    result = max(0.0, min(100.0, raw - penalties + bonuses))
    return round(result, 2), reasons