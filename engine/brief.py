"""Template-based bilingual (English + Hindi) pre-festival brief. No LLM dependency.

Only numbers that exist in the facts table are used (checked by verification.py).
Wording avoids any health-effect claim: the brief reports against CPCB Class B limits only.
"""
from __future__ import annotations

from datetime import date

from .loader import YEARS

MONTHS_EN = ["January", "February", "March", "April", "May", "June", "July", "August",
             "September", "October", "November", "December"]
MONTHS_HI = ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त",
             "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"]

TREND_HI = {"worsening": "बिगड़ता रुझान", "improving": "सुधरता रुझान", "stable": "स्थिर रुझान",
            "insufficient data": "रुझान के लिए अपर्याप्त डेटा"}
TREND_EN = {"worsening": "worsening trend", "improving": "improving trend", "stable": "stable trend",
            "insufficient data": "insufficient data for a trend"}
FEST_HI = {"Ganesh": "गणेश", "Durga": "दुर्गा"}
PHASE_HI = {"pre": "पूर्व", "during": "दौरान", "after": "पश्चात"}


def _g(x) -> str:
    return f"{x:g}" if isinstance(x, float) else str(x)


def action_lists(ranked: list[dict]) -> dict:
    """Deterministic action categories (implementation choice)."""
    aeration = sorted(
        [e for e in ranked if e["summary"]["Dissolved oxygen"]["breaches"]],
        key=lambda e: (-e["summary"]["Dissolved oxygen"]["breaches"] / max(e["summary"]["Dissolved oxygen"]["sampled"], 1),
                       e["summary"]["Dissolved oxygen"]["worst_value"]),
    )[:3]
    cleaning = sorted(
        [e for e in ranked if e["summary"]["BOD"]["breaches"]],
        key=lambda e: (-e["summary"]["BOD"]["breaches"] / max(e["summary"]["BOD"]["sampled"], 1),
                       -(e["summary"]["BOD"]["worst_value"] or 0)),
    )[:3]
    testing = sorted(ranked, key=lambda e: e["testing_priority"]["rank"])[:3]
    return {"aeration": aeration, "cleaning": cleaning, "testing": testing}


def limitations(ranked: list[dict], headline: dict) -> tuple[list[str], list[str]]:
    en, hi = [], []
    en.append("Units are not printed in the MPPCB reports; standard units (mg/l) are assumed.")
    hi.append("MPPCB रिपोर्ट में इकाइयाँ छपी नहीं हैं; मानक इकाइयाँ (mg/l) मानी गई हैं।")
    en.append(f"{headline['readings_bdl']} readings are BDL/ND (below detection limit): treated as very low, not zero, "
              f"not missing. {headline['readings_missing']} readings are missing or not sampled: never treated as clean.")
    hi.append(f"{headline['readings_bdl']} रीडिंग BDL/ND (पहचान सीमा से नीचे) हैं: बहुत कम मानी गईं, शून्य नहीं, "
              f"अनुपलब्ध नहीं। {headline['readings_missing']} रीडिंग अनुपलब्ध/सैंपल नहीं ली गईं: इन्हें कभी साफ़ नहीं माना गया।")
    for e in ranked:
        no_table = sorted({(g["year"], g["festival"]) for g in e["coverage"]["gaps"] if g["status"] == "no_table"})
        for (y, f) in no_table:
            en.append(f"{e['short_name']}: no {f} {y} table in the report; {f} {y} is not covered.")
            hi.append(f"{e['short_name']}: रिपोर्ट में {FEST_HI[f]} {y} की तालिका नहीं है; {FEST_HI[f]} {y} शामिल नहीं है।")
        if e["site_ambiguous"]:
            en.append(f"{e['short_name']}: site-name confidence is medium. Ganesh tables and Durga tables print "
                      f"different names for this site; these may be two places.")
            hi.append(f"{e['short_name']}: स्थल-नाम की पुष्टि मध्यम है। गणेश तालिकाओं और दुर्गा तालिकाओं में अलग-अलग नाम छपे हैं; "
                      f"ये दो अलग स्थान हो सकते हैं।")
    en.append("Only pH, DO and BOD have CPCB Class B limits. COD, solids, turbidity, conductivity and metals are shown "
              "for information only. Suspended solids were not tested in every year.")
    hi.append("केवल pH, DO और BOD की CPCB क्लास B सीमाएँ हैं। COD, ठोस, टर्बिडिटी, चालकता और धातुएँ केवल जानकारी के लिए हैं। "
              "निलंबित ठोस हर वर्ष नहीं जाँचे गए।")
    en.append("Readings are one sample per phase from past festivals. They describe past conditions, not live water quality.")
    hi.append("रीडिंग पिछले त्योहारों में प्रति चरण एक नमूने की हैं। ये पिछली स्थिति बताती हैं, आज की जल-गुणवत्ता नहीं।")
    return en, hi


def generate_brief_en(ranked: list[dict], headline: dict, thresholds: dict, build_date: date) -> str:
    acts = action_lists(ranked)
    lim_en, _ = limitations(ranked, headline)
    y0, y1 = YEARS[0], YEARS[-1]
    do_min, bod_max = _g(thresholds["Dissolved oxygen"]["min"]), _g(thresholds["BOD"]["max"])
    L = []
    L.append("VISARJAN GHAT WATCH - PRE-FESTIVAL WATER-QUALITY BRIEF")
    L.append(f"Date: {build_date.day} {MONTHS_EN[build_date.month - 1]} {build_date.year}")
    L.append("For: Bhopal Municipal Corporation, Durga visarjan planning")
    L.append(f"Data: MPPCB Ganesh and Durga immersion reports {y0}-{y1}, {len(ranked)} Bhopal ghats, "
             f"{headline['total_rows']} readings")
    L.append(f"Reference: CPCB Class B (outdoor bathing) limits - DO at least {do_min} mg/l, "
             f"BOD at most {bod_max} mg/l, pH {_g(thresholds['pH']['min'])}-{_g(thresholds['pH']['max'])}")
    L.append("")
    L.append("1. GHATS RANKED BY CONCERN (historical readings against Class B limits)")
    for e in ranked:
        L.append(f"  {e['rank']}. {e['short_name']} ({e['water_body']}) - {e['tier']['label_en']}; "
                 f"{e['evidence']['label_en'].lower()}; {TREND_EN[e['year_trend']]}")
        L.append(f"     {e['reason_en'].split(': ', 1)[1]}")
        if e["coverage"]["gaps"]:
            L.append(f"     Data gaps: {len(e['coverage']['gaps'])} of {e['coverage']['expected']} year-festival-phase "
                     f"combinations have no DO/BOD/pH reading.")
    L.append("")
    L.append("2. SUGGESTED ACTION CATEGORIES")
    L.append("  Testing priorities (where new samples add most information):")
    for e in acts["testing"]:
        tp = e["testing_priority"]
        why = []
        if tp["missing_combos"]:
            why.append(f"{tp['missing_combos']} missing year-festival-phase combinations")
        if tp["missing_readings"]:
            why.append(f"{tp['missing_readings']} missing DO/BOD/pH readings")
        if not why:
            why.append(f"severity score {_g(e['severity'])}, confirm before the event")
        L.append(f"    - {e['short_name']}: " + "; ".join(why))
    L.append("  Aeration priorities (lowest dissolved oxygen on record):")
    for e in acts["aeration"]:
        d = e["summary"]["Dissolved oxygen"]
        wr = d["worst_reading"]
        L.append(f"    - {e['short_name']}: DO below {do_min} mg/l in {d['breaches']} of {d['sampled']} readings; "
                 f"lowest {_g(d['worst_value'])} mg/l ({wr['festival']} {wr['year']}, {wr['phase']}, report page {wr['source_page']})")
    L.append("  Cleaning priorities (highest organic load, BOD):")
    for e in acts["cleaning"]:
        b = e["summary"]["BOD"]
        wr = b["worst_reading"]
        L.append(f"    - {e['short_name']}: BOD above {bod_max} mg/l in {b['breaches']} of {b['sampled']} readings; "
                 f"highest {_g(b['worst_value'])} mg/l ({wr['festival']} {wr['year']}, {wr['phase']}, report page {wr['source_page']})")
    L.append("")
    L.append("3. DATA LIMITATIONS")
    for s in lim_en:
        L.append(f"  - {s}")
    L.append("")
    L.append("4. NOTE")
    L.append("  This brief compares past MPPCB readings with CPCB Class B limits only. It does not describe what the water "
             "will do to people, and it does not describe current conditions. It supports the officer's decision; it does not "
             "replace it. Every number above is traceable to a report page in the evidence view.")
    return "\n".join(L)


def generate_brief_hi(ranked: list[dict], headline: dict, thresholds: dict, build_date: date) -> str:
    acts = action_lists(ranked)
    _, lim_hi = limitations(ranked, headline)
    y0, y1 = YEARS[0], YEARS[-1]
    do_min, bod_max = _g(thresholds["Dissolved oxygen"]["min"]), _g(thresholds["BOD"]["max"])
    L = []
    L.append("विसर्जन घाट वॉच - त्योहार-पूर्व जल-गुणवत्ता ब्रीफ")
    L.append(f"दिनांक: {build_date.day} {MONTHS_HI[build_date.month - 1]} {build_date.year}")
    L.append("हेतु: भोपाल नगर निगम, दुर्गा विसर्जन योजना")
    L.append(f"डेटा: MPPCB गणेश एवं दुर्गा विसर्जन रिपोर्ट {y0}-{y1}, भोपाल के {len(ranked)} घाट, "
             f"{headline['total_rows']} रीडिंग")
    L.append(f"संदर्भ: CPCB क्लास B (बाहरी स्नान) सीमाएँ - DO कम से कम {do_min} mg/l, "
             f"BOD अधिकतम {bod_max} mg/l, pH {_g(thresholds['pH']['min'])}-{_g(thresholds['pH']['max'])}")
    L.append("")
    L.append("1. चिंता के क्रम में घाट (पिछली रीडिंग, क्लास B सीमाओं के विरुद्ध)")
    for e in ranked:
        L.append(f"  {e['rank']}. {e['short_name']} ({e['water_body']}) - {e['tier']['label_hi']}; "
                 f"{e['evidence']['label_hi']}; {TREND_HI[e['year_trend']]}")
        L.append(f"     {e['reason_hi'].split(': ', 1)[1]}")
        if e["coverage"]["gaps"]:
            L.append(f"     डेटा अंतराल: {e['coverage']['expected']} में से {len(e['coverage']['gaps'])} वर्ष-त्योहार-चरण "
                     f"संयोजनों में कोई DO/BOD/pH रीडिंग नहीं।")
    L.append("")
    L.append("2. सुझाई गई कार्रवाई श्रेणियाँ")
    L.append("  जाँच प्राथमिकताएँ (जहाँ नए नमूने सबसे अधिक जानकारी देंगे):")
    for e in acts["testing"]:
        tp = e["testing_priority"]
        why = []
        if tp["missing_combos"]:
            why.append(f"{tp['missing_combos']} वर्ष-त्योहार-चरण संयोजन अनुपलब्ध")
        if tp["missing_readings"]:
            why.append(f"{tp['missing_readings']} DO/BOD/pH रीडिंग अनुपलब्ध")
        if not why:
            why.append(f"गंभीरता स्कोर {_g(e['severity'])}, आयोजन से पहले पुष्टि करें")
        L.append(f"    - {e['short_name']}: " + "; ".join(why))
    L.append("  वातन (एरेशन) प्राथमिकताएँ (रिकॉर्ड में सबसे कम घुलित ऑक्सीजन):")
    for e in acts["aeration"]:
        d = e["summary"]["Dissolved oxygen"]
        wr = d["worst_reading"]
        L.append(f"    - {e['short_name']}: {d['sampled']} में से {d['breaches']} रीडिंग में DO {do_min} mg/l से कम; "
                 f"न्यूनतम {_g(d['worst_value'])} mg/l ({FEST_HI[wr['festival']]} {wr['year']}, {PHASE_HI[wr['phase']]}, रिपोर्ट पृष्ठ {wr['source_page']})")
    L.append("  सफ़ाई प्राथमिकताएँ (सबसे अधिक जैविक भार, BOD):")
    for e in acts["cleaning"]:
        b = e["summary"]["BOD"]
        wr = b["worst_reading"]
        L.append(f"    - {e['short_name']}: {b['sampled']} में से {b['breaches']} रीडिंग में BOD {bod_max} mg/l से अधिक; "
                 f"अधिकतम {_g(b['worst_value'])} mg/l ({FEST_HI[wr['festival']]} {wr['year']}, {PHASE_HI[wr['phase']]}, रिपोर्ट पृष्ठ {wr['source_page']})")
    L.append("")
    L.append("3. डेटा की सीमाएँ")
    for s in lim_hi:
        L.append(f"  - {s}")
    L.append("")
    L.append("4. टिप्पणी")
    L.append("  यह ब्रीफ केवल MPPCB की पिछली रीडिंग की तुलना CPCB क्लास B सीमाओं से करता है। यह नहीं बताता कि पानी का लोगों पर "
             "क्या असर होगा, और न ही वर्तमान स्थिति बताता है। यह अधिकारी के निर्णय में सहायक है, उसका विकल्प नहीं। ऊपर की हर संख्या "
             "साक्ष्य दृश्य में रिपोर्ट के पृष्ठ से जुड़ी है।")
    return "\n".join(L)
