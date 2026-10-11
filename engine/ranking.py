"""Severity score, risk tier and (separate) evidence strength per ghat.

All weights and tier boundaries are implementation choices, documented in
implementation_plan.md. The ranking is deterministic.
"""
from __future__ import annotations

from .loader import ASSESSED_PARAMETERS, SHORT_NAMES

WEIGHTS = {"Dissolved oxygen": 0.35, "BOD": 0.35, "pH": 0.15, "worst_value_penalty": 0.15}

TIERS = [  # (min_score, key, label_en, label_hi, colour)
    (75, "critical", "Critical concern", "गंभीर चिंता", "red"),
    (50, "high", "High concern", "उच्च चिंता", "orange"),
    (25, "moderate", "Moderate concern", "मध्यम चिंता", "yellow"),
    (0, "lower", "Lower concern (based on available data)", "कम चिंता (उपलब्ध डेटा के आधार पर)", "green"),
]


def param_severity(pm: dict) -> float:
    """breach_rate x (1 + worst_value_factor), normalised to 0..1 (Durga weighted 2x)."""
    rate = pm["weighted_breach_rate"]
    if rate is None:
        return 0.0
    return rate * (1.0 + pm["worst_exceedance"]) / 2.0


def severity_score(metrics: dict) -> dict:
    pm = metrics["parameters"]
    parts = {p: param_severity(pm[p]) for p in ASSESSED_PARAMETERS}
    penalty = sum(pm[p]["worst_exceedance"] for p in ASSESSED_PARAMETERS) / len(ASSESSED_PARAMETERS)
    score = 100 * (
        WEIGHTS["Dissolved oxygen"] * parts["Dissolved oxygen"]
        + WEIGHTS["BOD"] * parts["BOD"]
        + WEIGHTS["pH"] * parts["pH"]
        + WEIGHTS["worst_value_penalty"] * penalty
    )
    return {"score": round(score, 1),
            "components": {**{k: round(v, 3) for k, v in parts.items()},
                           "worst_value_penalty": round(penalty, 3)}}


def tier_for(score: float) -> dict:
    for lo, key, en, hi, colour in TIERS:
        if score >= lo:
            return {"key": key, "label_en": en, "label_hi": hi, "colour": colour}
    return {"key": "lower", "label_en": TIERS[-1][2], "label_hi": TIERS[-1][3], "colour": "green"}


def evidence_strength(metrics: dict) -> dict:
    n = metrics["assessed_sampled"]
    combos = metrics["coverage"]["covered"]
    if n >= 12 and combos >= 4:
        key, en, hi = "strong", "Strong evidence", "मज़बूत साक्ष्य"
    elif n >= 6 and combos >= 2:
        key, en, hi = "moderate", "Moderate evidence", "मध्यम साक्ष्य"
    else:
        key, en, hi = "limited", "Limited evidence", "सीमित साक्ष्य"
    return {"key": key, "label_en": en, "label_hi": hi, "readings": n, "combos": combos,
            "expected_combos": metrics["coverage"]["expected"]}


def testing_priority(metrics: dict, severity: float) -> dict:
    """Second ranking: where is new testing most valuable?  (implementation choice)
    score = 4 x missing year-festival-phase combos + missing assessed readings + severity/25
    """
    missing_combos = len(metrics["coverage"]["gaps"])
    missing_readings = sum(metrics["parameters"][p]["missing"] for p in ASSESSED_PARAMETERS)
    score = 4 * missing_combos + missing_readings + severity / 25
    return {"score": round(score, 1), "missing_combos": missing_combos, "missing_readings": missing_readings}


def reason_sentence(metrics: dict, lang: str = "en") -> str:
    pm = metrics["parameters"]
    do, bod, ph = pm["Dissolved oxygen"], pm["BOD"], pm["pH"]
    short = SHORT_NAMES.get(metrics["site"], metrics["site"])
    parts_en, parts_hi = [], []
    if do["sampled"]:
        parts_en.append(f"DO below 5 mg/l in {do['breaches']} of {do['sampled']} readings (lowest {do['worst_value']:g})")
        parts_hi.append(f"{do['sampled']} में से {do['breaches']} रीडिंग में DO 5 mg/l से कम (न्यूनतम {do['worst_value']:g})")
    if bod["sampled"]:
        parts_en.append(f"BOD above 3 mg/l in {bod['breaches']} of {bod['sampled']} (highest {bod['worst_value']:g})")
        parts_hi.append(f"{bod['sampled']} में से {bod['breaches']} रीडिंग में BOD 3 mg/l से अधिक (अधिकतम {bod['worst_value']:g})")
    if ph["breaches"]:
        parts_en.append(f"pH outside 6.5-8.5 in {ph['breaches']} of {ph['sampled']}")
        parts_hi.append(f"{ph['sampled']} में से {ph['breaches']} रीडिंग में pH 6.5-8.5 से बाहर")
    if lang == "hi":
        return (f"{short}: " + "; ".join(parts_hi) + "।") if parts_hi else f"{short}: कोई मूल्यांकित रीडिंग उपलब्ध नहीं।"
    return (f"{short}: " + "; ".join(parts_en) + ".") if parts_en else f"{short}: no assessed readings available."


def rank_ghats(all_metrics: dict, meta: dict) -> list[dict]:
    ranked = []
    for site, m in all_metrics.items():
        sev = severity_score(m)
        ev = evidence_strength(m)
        entry = {
            "site": site,
            "short_name": SHORT_NAMES.get(site, site),
            "water_body": meta[site]["water_body"],
            "water_bodies": meta[site]["water_bodies"],
            "site_ambiguous": meta[site]["site_ambiguous"],
            "site_match_confidence": meta[site]["site_match_confidence"],
            "names_as_printed": meta[site]["names_as_printed"],
            "severity": sev["score"],
            "severity_components": sev["components"],
            "tier": tier_for(sev["score"]),
            "evidence": ev,
            "testing_priority": testing_priority(m, sev["score"]),
            "year_trend": m["year_trend"],
            "reason_en": reason_sentence(m, "en"),
            "reason_hi": reason_sentence(m, "hi"),
            "summary": {
                p: {k: m["parameters"][p][k]
                    for k in ("sampled", "breaches", "breach_rate", "worst_value", "bdl", "missing",
                              "worst_reading", "by_festival", "by_year", "by_phase")}
                for p in ASSESSED_PARAMETERS
            },
            "coverage": {"covered": m["coverage"]["covered"], "expected": m["coverage"]["expected"],
                         "gaps": m["coverage"]["gaps"], "combos": m["coverage"]["combos"]},
            "parameter_gaps": m["parameter_gaps"],
            "phase_series": m["phase_series"],
            "festivals_present": m["festivals_present"],
            "years_present": m["years_present"],
        }
        ranked.append(entry)
    ranked.sort(key=lambda e: (-e["severity"], e["site"]))
    for i, e in enumerate(ranked, 1):
        e["rank"] = i
    by_testing = sorted(ranked, key=lambda e: (-e["testing_priority"]["score"], e["site"]))
    for i, e in enumerate(by_testing, 1):
        e["testing_priority"]["rank"] = i
    return ranked
