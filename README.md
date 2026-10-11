# Visarjan Ghat Watch (NeerNiti)

Pre-festival water-quality risk briefing for the **Bhopal Municipal Corporation** officer planning Durga visarjan at the 7 Bhopal ghats.

- **Track**: Bhopal Impact Lab 2026, Track 2 - Visarjan Ghat Watch
- **Target user**: BMC officer deciding where to prioritise testing, aeration and cleaning before immersion
- **Data**: MPPCB Ganesh and Durga immersion reports 2023-2025 (1,524 readings, 7 ghats, 13 parameters), CPCB Class B limits

The tool ranks ghats by how often and how far past readings fell outside CPCB Class B (outdoor bathing) limits, shows the evidence behind every number down to the report page, lists what the data does *not* cover, and produces a bilingual (English / Hindi) brief that is machine-checked: every number must exist in a facts table and no health-effect wording is allowed.

## Run it (5 steps)

```bash
# 1. Python 3.10+ is the only requirement for the build (pytest for tests)
pip install -r requirements.txt

# 2. Build: cleans data, applies rules, ranks, writes the brief, verifies it
python build.py                       # or: python build.py --date 2026-10-11

# 3. Run the tests (headline counts, boundary rules, tamper test, health-claim blocker)
python -m pytest -q

# 4. Serve the static site (the browser needs HTTP to fetch the JSON)
python -m http.server 8000 --directory site

# 5. Open http://localhost:8000
```

`build.py` writes `output/` (JSON + `brief_en.txt` / `brief_hi.txt`) and copies the same files into `site/data/`. There is no runtime backend.

## What the dashboard shows

| Tab | Content |
|---|---|
| Dashboard | Summary cards, ghat cards ranked by severity or by testing priority, each with risk tier, evidence strength, one-line reason, DO/BOD mini phase charts, data-gap and site-ambiguity warnings. Click a card for the evidence drawer. |
| Evidence | Full readings table per ghat (filter by parameter / year / festival, sort), colour-coded breach / within limit / BDL / missing / no limit, with report page links. "What we don't know" panel: coverage matrix and parameter gaps. |
| Brief | English / Hindi toggle, copy-to-clipboard (WhatsApp-ready text), print / PDF via browser print, verification badge. |

## How the ranking works

All weights are implementation choices, documented in `implementation_plan.md` and in the Method note on the dashboard.

- **Rules**: DO breach if < 5 mg/l, BOD breach if > 3 mg/l, pH breach if outside 6.5-8.5 (boundary values are not breaches). Other parameters are display only. BDL/ND readings are not evaluated and not counted as compliant. Missing readings count in no direction.
- **Severity (0-100)** = 0.35 DO + 0.35 BOD + 0.15 pH + 0.15 worst-value penalty, each parameter = weighted breach rate x (1 + worst-value factor), Durga readings weighted 2x.
- **Tiers**: critical >= 75, high >= 50, moderate >= 25, else lower concern (based on available data).
- **Evidence strength** (separate axis): strong >= 12 readings over >= 4 year-festival-phase combinations; moderate >= 6 readings over >= 2; else limited.
- **Testing priority** (second ranking): 4 x missing combinations + missing DO/BOD/pH readings + severity / 25.

## Verification

`engine/verification.py` extracts every number from the generated briefs and card reasons and checks it against `output/facts_table.json`. It also scans for banned health-effect phrases in English and Hindi. The build fails if either check fails. `tests/test_verification.py` contains a tamper test (changing one number makes verification fail) and health-claim tests.

## What works / what does not

Works: full build, 45 automated tests, dashboard, evidence drawer and tab, bilingual brief with copy and print, bundled Noto Sans Devanagari font, print stylesheet.

Not done: a server-side `brief.pdf` (use the browser print dialog), the optional WhatsApp image card and spoken Hindi summary, and the statewide `mp_immersion_sites_2023_2025.csv` (not spot-checked by the data authors, so not used).

Known data caveats: units are assumed (reports print none); Rani Kamlapati / Kamla Park may be two sites; Bairagarh and Malikhedi have no Durga 2025 table; suspended solids were not tested in every year.

## Layout

```
build.py            master build script
engine/             loader, rules, metrics, ranking, facts, verification, brief
tests/              pytest suite
data/               copies of the Track 2 CSVs
output/             build artifacts (JSON + brief text)
site/               static dashboard (index.html, css/, js/, fonts/, data/)
```

## Sources and licence

Data: MPPCB idol immersion reports 2023, 2024, 2025 and CPCB water quality criteria, as packaged in `bhopal-impact-lab-2026-problem-statements/`. Font: Noto Sans Devanagari (SIL Open Font License). Code: MIT.
