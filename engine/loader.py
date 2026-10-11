"""Data loading + cleaning.

Each CSV row becomes a `Reading` with an explicit `state`:
  numeric  -> a number was printed in the report
  bdl      -> BDL / ND: below detection limit (very low, NOT zero, NOT missing)
  missing  -> not sampled / blank / '_' / '-' / '*' / '**'  (never treated as clean)
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
GHATS_CSV = DATA_DIR / "bhopal_ghats_2023_2025.csv"
CPCB_CSV = DATA_DIR / "cpcb_water_quality_criteria.csv"

MISSING_MARKERS = {"", "_", "-", "*", "**", "not sampled", "ns", "n.s.", "na", "n/a"}
BDL_MARKERS = {"bdl", "nd", "n.d.", "b.d.l."}

PARAMETERS = [
    "pH", "Dissolved oxygen", "BOD", "COD", "Total solids", "Dissolved solids",
    "Suspended solids", "Turbidity", "Conductivity", "Chromium", "Lead", "Zinc", "Copper",
]
ASSESSED_PARAMETERS = ["Dissolved oxygen", "BOD", "pH"]
PHASES = ["pre", "during", "after"]
FESTIVALS = ["Ganesh", "Durga"]
YEARS = [2023, 2024, 2025]

# Short display names used in the UI / brief
SHORT_NAMES = {
    "Bairagarh (Sant Hirdaram) kund": "Bairagarh",
    "Khatlapura ghat": "Khatlapura",
    "Prempura ghat": "Prempura",
    "Rani Kamlapati ghat / Kamla Park kund": "Rani Kamlapati / Kamla Park",
    "Hathaikheda dam / kund": "Hathaikheda",
    "Malikhedi kund": "Malikhedi",
    "Shahpura lake ghat": "Shahpura",
}


@dataclass
class Reading:
    year: int
    festival: str
    site: str
    water_body: str
    phase: str
    parameter: str
    value: Optional[float]
    unit: str
    flag: str
    value_as_printed: str
    parameter_as_printed: str
    site_as_printed: str
    site_match_confidence: str
    source_page: Optional[int]
    state: str  # numeric | bdl | missing

    def to_dict(self) -> dict:
        return asdict(self)


def classify(value: str, flag: str, value_as_printed: str) -> tuple[Optional[float], str]:
    """Return (float_or_None, state)."""
    v = (value or "").strip()
    f = (flag or "").strip().lower()
    p = (value_as_printed or "").strip().lower()
    if v:
        try:
            return float(v), "numeric"
        except ValueError:
            pass
    if f in BDL_MARKERS or p in BDL_MARKERS:
        return None, "bdl"
    # anything else without a number is missing (blank, _, -, *, **, not sampled)
    return None, "missing"


def load_readings(path: Path = GHATS_CSV) -> list[Reading]:
    readings: list[Reading] = []
    with open(path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            value, state = classify(row.get("value", ""), row.get("flag", ""), row.get("value_as_printed", ""))
            sp = (row.get("source_page") or "").strip()
            readings.append(
                Reading(
                    year=int(row["year"]),
                    festival=row["festival"].strip(),
                    site=row["site"].strip(),
                    water_body=row.get("water_body", "").strip(),
                    phase=row["phase"].strip().lower(),
                    parameter=row["parameter"].strip(),
                    value=value,
                    unit=(row.get("unit_assumed") or "").strip(),
                    flag=(row.get("flag") or "").strip(),
                    value_as_printed=(row.get("value_as_printed") or "").strip(),
                    parameter_as_printed=(row.get("parameter_as_printed") or "").strip(),
                    site_as_printed=(row.get("site_as_printed") or "").strip(),
                    site_match_confidence=(row.get("site_match_confidence") or "").strip(),
                    source_page=int(sp) if sp.isdigit() else None,
                    state=state,
                )
            )
    return readings


def load_class_b_thresholds(path: Path = CPCB_CSV) -> dict:
    """Extract CPCB Class B (outdoor bathing) limits for pH, DO and BOD."""
    name_map = {"BOD (5 days 20C)": "BOD", "Dissolved oxygen": "Dissolved oxygen", "pH": "pH"}
    out: dict = {}
    with open(path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row["class"].strip() != "B":
                continue
            p = name_map.get(row["parameter"].strip())
            if not p:
                continue
            lt = row["limit_type"].strip()
            lim = row["limit"].strip()
            if lt == "range":
                lo, hi = (float(x) for x in lim.split("-"))
                out[p] = {"type": "range", "min": lo, "max": hi, "unit": row["unit"].strip()}
            elif lt == "min":
                out[p] = {"type": "min", "min": float(lim), "unit": row["unit"].strip()}
            elif lt == "max":
                out[p] = {"type": "max", "max": float(lim), "unit": row["unit"].strip()}
    missing = [p for p in ASSESSED_PARAMETERS if p not in out]
    if missing:
        raise ValueError(f"CPCB Class B thresholds missing for: {missing}")
    return out


def sites(readings: list[Reading]) -> list[str]:
    seen: dict[str, None] = {}
    for r in readings:
        seen.setdefault(r.site, None)
    return list(seen)


def site_meta(readings: list[Reading]) -> dict[str, dict]:
    """Water body, confidence and as-printed names per site."""
    meta: dict[str, dict] = {}
    for r in readings:
        m = meta.setdefault(
            r.site,
            {"site": r.site, "short_name": SHORT_NAMES.get(r.site, r.site), "water_bodies": [],
             "site_match_confidence": r.site_match_confidence, "names_as_printed": []},
        )
        if r.water_body and r.water_body not in m["water_bodies"]:
            m["water_bodies"].append(r.water_body)
        if r.site_as_printed and r.site_as_printed not in m["names_as_printed"]:
            m["names_as_printed"].append(r.site_as_printed)
        if r.site_match_confidence == "medium":
            m["site_match_confidence"] = "medium"
    for m in meta.values():
        m["water_body"] = min(m["water_bodies"], key=len)
        m["site_ambiguous"] = m["site_match_confidence"] != "high"
    return meta
