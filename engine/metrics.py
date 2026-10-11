"""Per-ghat metrics computed from evaluated readings."""
from __future__ import annotations

from collections import defaultdict

from .loader import ASSESSED_PARAMETERS, PHASES, FESTIVALS, YEARS, PARAMETERS
from .rules import BREACH, OK, BDL, MISSING

FESTIVAL_WEIGHT = {"Durga": 2.0, "Ganesh": 1.0}  # planned event is Durga -> weighted 2x
EXPECTED_COMBOS = [(y, f, p) for y in YEARS for f in FESTIVALS for p in PHASES]


def _worse(parameter: str, a, b: float) -> float:
    if a is None:
        return b
    if parameter == "Dissolved oxygen":
        return min(a, b)
    if parameter == "BOD":
        return max(a, b)
    # pH: the value farthest from 7.5 (centre of 6.5-8.5)
    return b if abs(b - 7.5) > abs(a - 7.5) else a


def _split(numeric: list[dict], key: str, values) -> dict:
    out = {}
    for v in values:
        n = [r for r in numeric if r[key] == v]
        b = [r for r in n if r["outcome"] == BREACH]
        out[str(v)] = {"sampled": len(n), "breaches": len(b),
                       "breach_rate": (len(b) / len(n)) if n else None}
    return out


def param_metrics(rows: list[dict], parameter: str) -> dict:
    rs = [r for r in rows if r["parameter"] == parameter]
    numeric = [r for r in rs if r["outcome"] in (BREACH, OK)]
    breaches = [r for r in numeric if r["outcome"] == BREACH]
    w_sampled = sum(FESTIVAL_WEIGHT[r["festival"]] for r in numeric)
    w_breach = sum(FESTIVAL_WEIGHT[r["festival"]] for r in breaches)
    worst = None
    worst_reading = None
    for r in numeric:
        nw = _worse(parameter, worst, r["value"])
        if worst_reading is None or nw != worst:
            worst, worst_reading = nw, r
    return {
        "parameter": parameter,
        "sampled": len(numeric),
        "breaches": len(breaches),
        "breach_rate": (len(breaches) / len(numeric)) if numeric else None,
        "weighted_breach_rate": (w_breach / w_sampled) if w_sampled else None,
        "bdl": sum(1 for r in rs if r["outcome"] == BDL),
        "missing": sum(1 for r in rs if r["outcome"] == MISSING),
        "worst_value": worst,
        "worst_exceedance": max((r["exceedance"] for r in breaches), default=0.0),
        "worst_reading": (
            {k: worst_reading[k] for k in ("year", "festival", "phase", "value", "unit", "source_page")}
            if worst_reading else None
        ),
        "by_festival": _split(numeric, "festival", FESTIVALS),
        "by_year": _split(numeric, "year", YEARS),
        "by_phase": _split(numeric, "phase", PHASES),
    }


def year_trend(pm: dict) -> str:
    """Implementation choice: compare combined DO+BOD breach rate, first vs last year with data."""
    rates = []
    for y in YEARS:
        s = b = 0
        for p in ("Dissolved oxygen", "BOD"):
            yb = pm[p]["by_year"][str(y)]
            s += yb["sampled"]
            b += yb["breaches"]
        if s:
            rates.append((y, b / s))
    if len(rates) < 2:
        return "insufficient data"
    delta = rates[-1][1] - rates[0][1]
    if delta > 0.15:
        return "worsening"
    if delta < -0.15:
        return "improving"
    return "stable"


def coverage_matrix(rows: list[dict]) -> dict:
    """Which (year, festival, phase) combos have at least one numeric DO/BOD/pH reading."""
    present = defaultdict(int)
    for r in rows:
        if r["parameter"] in ASSESSED_PARAMETERS and r["outcome"] in (BREACH, OK):
            present[(r["year"], r["festival"], r["phase"])] += 1
    tabled = {(r["year"], r["festival"], r["phase"]) for r in rows}
    matrix = []
    for (y, f, p) in EXPECTED_COMBOS:
        n = present.get((y, f, p), 0)
        matrix.append({
            "year": y, "festival": f, "phase": p,
            "assessed_readings": n,
            "status": "covered" if n else ("tabled_but_missing" if (y, f, p) in tabled else "no_table"),
        })
    return {
        "combos": matrix,
        "covered": sum(1 for m in matrix if m["status"] == "covered"),
        "expected": len(matrix),
        "gaps": [m for m in matrix if m["status"] != "covered"],
    }


def parameter_gaps(rows: list[dict]) -> list[dict]:
    """Parameters never numerically reported, or with missing readings, at this ghat."""
    out = []
    for p in PARAMETERS:
        rs = [r for r in rows if r["parameter"] == p]
        numeric = sum(1 for r in rs if r["state"] == "numeric")
        bdl = sum(1 for r in rs if r["state"] == "bdl")
        missing = sum(1 for r in rs if r["state"] == "missing")
        if not rs or missing or not numeric:
            if not rs:
                note = "not in any report table"
            elif not numeric and bdl == len(rs):
                note = "no numeric readings (all BDL)"
            else:
                note = f"{missing} missing / not sampled"
            out.append({"parameter": p, "rows": len(rs), "numeric": numeric, "bdl": bdl,
                        "missing": missing, "note": note})
    return out


def phase_series(rows: list[dict]) -> dict:
    """Values of DO/BOD/pH per (year, festival) across pre/during/after, for sparklines."""
    series = {}
    for p in ASSESSED_PARAMETERS:
        series[p] = []
        for y in YEARS:
            for f in FESTIVALS:
                pts = []
                for ph in PHASES:
                    hit = next((r for r in rows if r["parameter"] == p and r["year"] == y
                                and r["festival"] == f and r["phase"] == ph), None)
                    pts.append({"phase": ph,
                                "value": hit["value"] if hit else None,
                                "outcome": hit["outcome"] if hit else "no_table"})
                if any(pt["outcome"] != "no_table" for pt in pts):
                    series[p].append({"year": y, "festival": f, "points": pts})
    return series


def ghat_metrics(site: str, rows: list[dict]) -> dict:
    srows = [r for r in rows if r["site"] == site]
    pm = {p: param_metrics(srows, p) for p in ASSESSED_PARAMETERS}
    cov = coverage_matrix(srows)
    return {
        "site": site,
        "rows": len(srows),
        "assessed_sampled": sum(pm[p]["sampled"] for p in ASSESSED_PARAMETERS),
        "assessed_breaches": sum(pm[p]["breaches"] for p in ASSESSED_PARAMETERS),
        "parameters": pm,
        "year_trend": year_trend(pm),
        "coverage": cov,
        "parameter_gaps": parameter_gaps(srows),
        "phase_series": phase_series(srows),
        "festivals_present": sorted({r["festival"] for r in srows}),
        "years_present": sorted({r["year"] for r in srows}),
    }


def headline_metrics(rows: list[dict]) -> dict:
    out = {"total_rows": len(rows)}
    for p in ASSESSED_PARAMETERS:
        m = param_metrics(rows, p)
        out[p] = {"sampled": m["sampled"], "breaches": m["breaches"], "bdl": m["bdl"], "missing": m["missing"]}
    out["readings_numeric"] = sum(1 for r in rows if r["state"] == "numeric")
    out["readings_bdl"] = sum(1 for r in rows if r["state"] == "bdl")
    out["readings_missing"] = sum(1 for r in rows if r["state"] == "missing")
    return out
