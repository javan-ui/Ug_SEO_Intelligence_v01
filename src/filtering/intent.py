from __future__ import annotations

from src.utils.text import tokenize

TRANSACTIONAL = {"hire", "buy", "create", "build", "get", "services", "developer", "designer", "agency", "company"}
COMMERCIAL = {"best", "affordable", "cheap", "professional", "custom", "cost", "price", "prices", "how much"}
INFORMATIONAL = {"how", "why", "what", "guide", "learn", "create", "build", "advertise", "rank"}
LOCAL = {"uganda", "kampala", "wakiso", "entebbe", "jinja", "mbarara", "mbale", "gulu", "masaka", "mukono"}


def classify_intent(keyword: str) -> dict[str, object]:
    lower = keyword.casefold()
    tokens = tokenize(keyword)
    intents: list[str] = []
    if tokens & TRANSACTIONAL:
        intents.append("TRANSACTIONAL")
    if tokens & COMMERCIAL or "cost" in lower or "price" in lower:
        intents.append("COMMERCIAL_INVESTIGATION")
    if tokens & INFORMATIONAL or lower.startswith(("how ", "why ", "what ")):
        intents.append("INFORMATIONAL")
    if tokens & LOCAL:
        intents.append("LOCAL")
    if not intents:
        intents.append("MIXED")
    commercial = min(100.0, len(tokens & (TRANSACTIONAL | COMMERCIAL)) * 18.0)
    if "website" in tokens or "web" in tokens:
        commercial += 15.0
    if "services" in tokens or "company" in tokens or "agency" in tokens:
        commercial += 15.0
    informational = min(100.0, len(tokens & INFORMATIONAL) * 20.0)
    return {
        "intents": sorted(set(intents)),
        "commercial_intent": round(commercial, 2),
        "informational_intent": round(informational, 2),
    }