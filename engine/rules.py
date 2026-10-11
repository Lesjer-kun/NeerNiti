"""CPCB Class B threshold checks.

Outcome per reading:
  breach        numeric value outside the Class B limit
  ok            numeric value within the limit (boundary values are NOT breaches)
  bdl           below detection limit: not evaluated, not counted as compliant
  missing       not sampled: not counted in any direction
  not_assessed  parameter has no Class B limit (display only)
"""
from __future__ import annotations

from .loader import Reading, ASSESSED_PARAMETERS

BREACH, OK, BDL, MISSING, NOT_ASSESSED = "breach", "ok", "bdl", "missing", "not_assessed"


def is_breach(parameter: str, value: float, thresholds: dict) -> bool:
    t = thresholds.get(parameter)
    if t is None:
        return False
    if t["type"] == "min":
        return value < t["min"]
    if t["type"] == "max":
        return value > t["max"]
    return value < t["min"] or value > t["max"]


def evaluate(reading: Reading, thresholds: dict) -> str:
    if reading.parameter not in ASSESSED_PARAMETERS or reading.parameter not in thresholds:
        return NOT_ASSESSED
    if reading.state == "missing":
        return MISSING
    if reading.state == "bdl":
        return BDL
    return BREACH if is_breach(reading.parameter, reading.value, thresholds) else OK


def exceedance_factor(parameter: str, value: float, thresholds: dict) -> float:
    """How far beyond the limit a value sits, scaled 0..1 (0 = at/within limit).

    Implementation choice (not source-stated):
      DO  : (5 - value) / 5             -> DO 0 gives 1.0
      BOD : (value - 3) / 27            -> BOD 30 gives 1.0
      pH  : distance outside 6.5-8.5 / 1.5
    """
    t = thresholds.get(parameter)
    if t is None:
        return 0.0
    if t["type"] == "min":
        f = (t["min"] - value) / t["min"]
    elif t["type"] == "max":
        f = (value - t["max"]) / (t["max"] * 9)
    else:
        if value < t["min"]:
            f = (t["min"] - value) / 1.5
        elif value > t["max"]:
            f = (value - t["max"]) / 1.5
        else:
            f = 0.0
    return max(0.0, min(1.0, f))


def evaluate_all(readings: list[Reading], thresholds: dict) -> list[dict]:
    """Attach `outcome` and `exceedance` to each reading dict."""
    out = []
    for r in readings:
        d = r.to_dict()
        d["outcome"] = evaluate(r, thresholds)
        d["exceedance"] = (
            exceedance_factor(r.parameter, r.value, thresholds) if d["outcome"] == BREACH else 0.0
        )
        out.append(d)
    return out
