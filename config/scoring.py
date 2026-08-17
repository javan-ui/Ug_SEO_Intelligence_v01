"""Documented, bounded weights for the internal scoring model."""

OPPORTUNITY_WEIGHTS = {
    "demand_signal": 0.25,
    "rankability": 0.30,
    "commercial_value": 0.25,
    "uganda_relevance": 0.20,
}

PHASE_BUDGETS = {
    "discovery": 300,
    "candidate_expansion": 500,
    "serp_validation": 1300,
    "competitor_investigation": 250,
    "reserve": 150,
}

assert abs(sum(OPPORTUNITY_WEIGHTS.values()) - 1.0) < 0.001