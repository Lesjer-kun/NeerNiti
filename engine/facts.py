"""Facts table: every numeric claim that may appear in the brief or UI.

Each fact: {fact_id, claim_text, value, source_readings: [{year, festival, phase, source_page}]}
The verification step checks every number in generated text against this table.
"""
from __future__ import annotations

from datetime import date

from .loader import ASSESSED_PARAMETERS, YEARS, PARAMETERS
from .rules import BREACH, OK

PARAM_SHORT = {"Dissolved oxygen": "DO", "BOD": "BOD", "pH": "pH"}


def _src(rows: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for r in rows:
        key = (r["year"], r["festival"], r["phase"], r["source_page"], r["site"])
        if key in seen:
            continue
        seen.add(key)
        out.append({"site": r["site"], "year": r["year"], "festival": r["festival"],
                    "phase": r["phase"], "source_page": r["source_page"]})
    return out


def build_facts(rows: list[dict], ranked: list[dict], thresholds: dict, build_date: date) -> list[dict]:
    facts: list[dict] = []

    def add(fact_id, claim, value, src=None):
        facts.append({"fact_id": fact_id, "claim_text": claim, "value": value,
                      "source_readings": src or []})

    # --- build context -----------------------------------------------------
    add("build_date_day", "Day of month this brief was generated", build_date.day)
    add("build_date_year", "Year this brief was generated", build_date.year)
    add("build_date_month", "Month number this brief was generated", build_date.month)

    # --- thresholds (CPCB Class B) -----------------------------------------
    add("threshold_do_min", "CPCB Class B: dissolved oxygen minimum (mg/l)", thresholds["Dissolved oxygen"]["min"])
    add("threshold_bod_max", "CPCB Class B: BOD maximum (mg/l)", thresholds["BOD"]["max"])
    add("threshold_ph_min", "CPCB Class B: pH minimum", thresholds["pH"]["min"])
    add("threshold_ph_max", "CPCB Class B: pH maximum", thresholds["pH"]["max"])

    # --- dataset headline --------------------------------------------------
    add("total_rows", "Total readings in the Bhopal dataset", len(rows))
    for y in YEARS:
        add(f"year_{y}", f"Report year {y} is in the dataset", y)
    add("ghat_count", "Number of Bhopal ghats analysed", len(ranked))
    add("parameter_count", "Number of parameters in the reports", len(PARAMETERS))
    add("readings_bdl", "Readings printed as BDL / ND (below detection limit)",
        sum(1 for r in rows if r["state"] == "bdl"))
    add("readings_missing", "Readings missing / not sampled",
        sum(1 for r in rows if r["state"] == "missing"))
    add("festival_count", "Number of festivals covered (Ganesh, Durga)", 2)
    add("phase_count", "Number of sampling phases (pre, during, after)", 3)
    for p in ASSESSED_PARAMETERS:
        prs = [r for r in rows if r["parameter"] == p and r["outcome"] in (BREACH, OK)]
        br = [r for r in prs if r["outcome"] == BREACH]
        s = PARAM_SHORT[p]
        add(f"{s.lower()}_sampled_all", f"{s} numeric readings across all ghats", len(prs), _src(prs))
        add(f"{s.lower()}_breaches_all", f"{s} readings outside the Class B limit across all ghats", len(br), _src(br))
    do_zero = [r for r in rows if r["parameter"] == "Dissolved oxygen" and r["value"] == 0.0]
    add("do_zero_count", "Readings where dissolved oxygen was printed as 0", len(do_zero), _src(do_zero))

    # --- per ghat ----------------------------------------------------------
    for e in ranked:
        site = e["site"]
        sid = e["short_name"].lower().replace(" / ", "_").replace(" ", "_")
        srows = [r for r in rows if r["site"] == site]
        add(f"{sid}_rank", f"{e['short_name']}: severity rank", e["rank"])
        add(f"{sid}_severity", f"{e['short_name']}: severity score (0-100)", e["severity"], _src(srows))
        add(f"{sid}_testing_rank", f"{e['short_name']}: testing-priority rank", e["testing_priority"]["rank"])
        add(f"{sid}_evidence_readings", f"{e['short_name']}: numeric DO/BOD/pH readings", e["evidence"]["readings"], _src(srows))
        add(f"{sid}_combos_covered", f"{e['short_name']}: year-festival-phase combinations with data",
            e["coverage"]["covered"])
        add(f"{sid}_combos_expected", f"{e['short_name']}: expected year-festival-phase combinations",
            e["coverage"]["expected"])
        add(f"{sid}_combos_missing", f"{e['short_name']}: missing year-festival-phase combinations",
            len(e["coverage"]["gaps"]))
        add(f"{sid}_missing_readings", f"{e['short_name']}: missing DO/BOD/pH readings",
            e["testing_priority"]["missing_readings"])
        for p in ASSESSED_PARAMETERS:
            s = PARAM_SHORT[p]
            sm = e["summary"][p]
            prs = [r for r in srows if r["parameter"] == p and r["outcome"] in (BREACH, OK)]
            br = [r for r in prs if r["outcome"] == BREACH]
            add(f"{sid}_{s.lower()}_sampled", f"{e['short_name']}: {s} numeric readings", sm["sampled"], _src(prs))
            add(f"{sid}_{s.lower()}_breaches", f"{e['short_name']}: {s} readings outside Class B limit", sm["breaches"], _src(br))
            if sm["worst_value"] is not None:
                wr = sm["worst_reading"]
                add(f"{sid}_{s.lower()}_worst", f"{e['short_name']}: worst {s} value", sm["worst_value"],
                    [{"site": site, "year": wr["year"], "festival": wr["festival"], "phase": wr["phase"],
                      "source_page": wr["source_page"]}])
                add(f"{sid}_{s.lower()}_worst_page", f"{e['short_name']}: report page of worst {s} value",
                    wr["source_page"])
            for fest, fb in sm["by_festival"].items():
                add(f"{sid}_{s.lower()}_{fest.lower()}_sampled", f"{e['short_name']}: {s} readings during {fest}", fb["sampled"])
                add(f"{sid}_{s.lower()}_{fest.lower()}_breaches", f"{e['short_name']}: {s} breaches during {fest}", fb["breaches"])
            for y, yb in sm["by_year"].items():
                add(f"{sid}_{s.lower()}_{y}_sampled", f"{e['short_name']}: {s} readings in {y}", yb["sampled"])
                add(f"{sid}_{s.lower()}_{y}_breaches", f"{e['short_name']}: {s} breaches in {y}", yb["breaches"])
    return facts


def fact_values(facts: list[dict]) -> set[float]:
    return {float(f["value"]) for f in facts if isinstance(f["value"], (int, float)) and f["value"] is not None}
