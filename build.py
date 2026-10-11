#!/usr/bin/env python
"""Master build script. Static architecture: this IS the backend.

Usage:  python build.py [--date YYYY-MM-DD]

Emits output/{ranking,evidence,facts_table,verification,brief}.json, brief_en.txt, brief_hi.txt
and copies them into site/data/ for the static dashboard.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from engine import loader, rules, metrics, ranking, facts, verification, brief  # noqa: E402

OUTPUT = ROOT / "output"
SITE_DATA = ROOT / "site" / "data"


def run(build_date: date, write: bool = True) -> dict:
    # 1. load + clean
    readings = loader.load_readings()
    thresholds = loader.load_class_b_thresholds()
    meta = loader.site_meta(readings)
    # 2. rules
    rows = rules.evaluate_all(readings, thresholds)
    # 3. metrics
    headline = metrics.headline_metrics(rows)
    per_ghat = {s: metrics.ghat_metrics(s, rows) for s in loader.sites(readings)}
    # 4. ranking
    ranked = ranking.rank_ghats(per_ghat, meta)
    # 5. facts
    fact_list = facts.build_facts(rows, ranked, thresholds, build_date)
    allowed = facts.fact_values(fact_list)
    # 6. brief
    brief_en = brief.generate_brief_en(ranked, headline, thresholds, build_date)
    brief_hi = brief.generate_brief_hi(ranked, headline, thresholds, build_date)
    # 7. verification of all generated text
    texts = {"brief_en": brief_en, "brief_hi": brief_hi}
    for e in ranked:
        texts[f"reason_en:{e['short_name']}"] = e["reason_en"]
        texts[f"reason_hi:{e['short_name']}"] = e["reason_hi"]
    report = verification.verify_all(texts, allowed)

    ranking_doc = {
        "generated": build_date.isoformat(),
        "data_period": f"{loader.YEARS[0]}-{loader.YEARS[-1]}",
        "thresholds": thresholds,
        "headline": headline,
        "ghats": ranked,
        "verification": {"badge": report["badge"], "passed": report["passed"]},
        "method": {
            "severity_weights": ranking.WEIGHTS,
            "festival_weight": metrics.FESTIVAL_WEIGHT,
            "tiers": [{"min": t[0], "key": t[1], "label_en": t[2]} for t in ranking.TIERS],
            "evidence_strength": "strong: >=12 readings & >=4 combos; moderate: >=6 readings & >=2 combos; else limited",
        },
    }
    evidence_doc = {
        "generated": build_date.isoformat(),
        "sites": {s: [r for r in rows if r["site"] == s] for s in loader.sites(readings)},
        "parameters": loader.PARAMETERS,
        "assessed_parameters": loader.ASSESSED_PARAMETERS,
        "coverage": {s: per_ghat[s]["coverage"] for s in per_ghat},
        "parameter_gaps": {s: per_ghat[s]["parameter_gaps"] for s in per_ghat},
    }
    brief_doc = {"generated": build_date.isoformat(), "en": brief_en, "hi": brief_hi, "verification": report}
    result = {"headline": headline, "ranked": ranked, "report": report, "facts": fact_list,
              "brief_en": brief_en, "brief_hi": brief_hi, "allowed": allowed, "rows": rows}
    if not write:
        return result

    # 8. emit
    OUTPUT.mkdir(exist_ok=True)
    SITE_DATA.mkdir(parents=True, exist_ok=True)

    def dump(name: str, obj) -> None:
        for d in (OUTPUT, SITE_DATA):
            with open(d / name, "w", encoding="utf-8") as fh:
                json.dump(obj, fh, ensure_ascii=False, indent=1)

    dump("ranking.json", ranking_doc)
    dump("evidence.json", evidence_doc)
    dump("facts_table.json", {"generated": build_date.isoformat(), "facts": fact_list})
    dump("verification.json", report)
    dump("brief.json", brief_doc)
    (OUTPUT / "brief_en.txt").write_text(brief_en, encoding="utf-8")
    (OUTPUT / "brief_hi.txt").write_text(brief_hi, encoding="utf-8")
    shutil.copy(OUTPUT / "brief_en.txt", SITE_DATA / "brief_en.txt")
    shutil.copy(OUTPUT / "brief_hi.txt", SITE_DATA / "brief_hi.txt")
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=date.today().isoformat(), help="brief date, YYYY-MM-DD")
    args = ap.parse_args()
    build_date = date.fromisoformat(args.date)
    res = run(build_date)
    h = res["headline"]
    print("== Visarjan Ghat Watch build ==")
    print(f"rows={h['total_rows']}  DO breaches={h['Dissolved oxygen']['breaches']}/{h['Dissolved oxygen']['sampled']}  "
          f"BOD breaches={h['BOD']['breaches']}/{h['BOD']['sampled']}  pH breaches={h['pH']['breaches']}/{h['pH']['sampled']}")
    print("rank  severity  tier      evidence  ghat")
    for e in res["ranked"]:
        print(f"{e['rank']:>4}  {e['severity']:>8}  {e['tier']['key']:<9} {e['evidence']['key']:<9} {e['short_name']}")
    r = res["report"]
    print(f"facts={len(res['facts'])}  {r['badge']}  -> {'PASS' if r['passed'] else 'FAIL'}")
    if not r["passed"]:
        for k, t in r["texts"].items():
            if not t["passed"]:
                print(f"  FAIL {k}: unverified={t['unverified']} health={t['health_claims']}")
        return 1
    print(f"wrote {OUTPUT} and {SITE_DATA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
