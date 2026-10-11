"""Numeric claim auditor + health-claim blocker.

* Every number in generated text must exist in the facts table.
* Generated text must contain none of the banned health-effect phrases
  (the brief reports against CPCB Class B limits only).
"""
from __future__ import annotations

import re

NUMBER_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(?![\w]|\.\d)")

# Phrases that would turn a limit comparison into a health-effect claim.
BANNED_PHRASES_EN = [
    "safe to bathe", "safe for bathing", "safe for immersion", "safe to immerse", "safe to drink",
    "unsafe", "is safe", "are safe", "will cause", "causes disease", "disease", "health risk",
    "health hazard", "harmful to health", "dangerous to health", "toxic", "poison", "cancer",
    "illness", "infection", "sickness", "fit for bathing", "unfit for bathing", "drinkable",
    "potable", "risk to life", "fatal", "lethal",
]
BANNED_PHRASES_HI = [
    "सुरक्षित", "असुरक्षित", "स्वास्थ्य", "बीमारी", "रोग", "ज़हरीला", "जहरीला", "विषैला", "विषाक्त",
    "कैंसर", "संक्रमण", "नहाने योग्य", "नहाने के लिए", "पीने योग्य", "जानलेवा", "घातक", "खतरनाक",
]


def extract_numbers(text: str) -> list[str]:
    return NUMBER_RE.findall(text)


def audit_numbers(text: str, allowed_values: set[float]) -> dict:
    found = extract_numbers(text)
    unverified = []
    for tok in found:
        try:
            v = float(tok)
        except ValueError:
            unverified.append(tok)
            continue
        if v not in allowed_values:
            unverified.append(tok)
    return {"numbers_found": len(found), "numbers_verified": len(found) - len(unverified),
            "unverified": sorted(set(unverified), key=lambda s: float(s))}


def find_health_claims(text: str) -> list[str]:
    low = text.lower()
    hits = [p for p in BANNED_PHRASES_EN if p in low]
    hits += [p for p in BANNED_PHRASES_HI if p in text]
    return hits


def verify_text(text: str, allowed_values: set[float], label: str = "") -> dict:
    audit = audit_numbers(text, allowed_values)
    health = find_health_claims(text)
    passed = not audit["unverified"] and not health
    badge = f"Verified: {audit['numbers_verified']} of {audit['numbers_found']} numbers, {len(health)} health claims"
    return {"label": label, "passed": passed, "badge": badge, "health_claims": health, **audit}


def verify_all(texts: dict, allowed_values: set[float]) -> dict:
    results = {k: verify_text(v, allowed_values, k) for k, v in texts.items()}
    total_found = sum(r["numbers_found"] for r in results.values())
    total_ok = sum(r["numbers_verified"] for r in results.values())
    total_health = sum(len(r["health_claims"]) for r in results.values())
    return {
        "passed": all(r["passed"] for r in results.values()),
        "badge": f"Verified: {total_ok} of {total_found} numbers, {total_health} health claims",
        "numbers_found": total_found,
        "numbers_verified": total_ok,
        "health_claims": total_health,
        "texts": results,
    }
