# Visarjan Ghat Watch — Implementation Plan

> **Project**: Pre-festival water-quality risk briefing tool for Bhopal Municipal Corporation
> **Target User**: BMC officer planning Durga visarjan at 7 ghats
> **Data**: 1,524 rows × 14 columns across 7 ghats, 3 years (2023–2025), 2 festivals, 3 phases

---

## Data Verification ✅

| Headline Metric | Expected | Verified |
|---|---|---|
| Total rows | 1,524 | ✅ 1,524 |
| DO readings below 5 mg/l | 42 of 116 | ✅ 42/116 |
| BOD readings above 3 mg/l | 100 of 112 | ✅ 100/112 |
| DO = 0 at Bairagarh | 4 times | ✅ 4 |
| Ghats | 7 | ✅ 7 |
| Parameters | 13 | ✅ 13 |

---

## Architecture Decision

```
Build-time pipeline (Python)          →  Static files  →  Static website (HTML/Tailwind/JS)
                                           ↓
bhopal_ghats_2023_2025.csv            ranking.json
cpcb_water_quality_criteria.csv  →    evidence.json
                                      facts_table.json
                                      brief_en.txt / brief_hi.txt
```

**No runtime backend needed.** Python builds JSON artifacts at build time; the browser reads them.

---

## Project Structure

```
NeerNiti/
├── data/                          # Symlinked/copied from source repo
│   ├── bhopal_ghats_2023_2025.csv
│   ├── cpcb_water_quality_criteria.csv
│   └── sample_bhopal_2025.csv
├── build.py                       # Master build script
├── engine/                        # Python core logic
│   ├── __init__.py
│   ├── loader.py                  # Data loading + cleaning
│   ├── rules.py                   # CPCB Class B threshold checks
│   ├── metrics.py                 # Per-ghat metrics calculation
│   ├── ranking.py                 # Severity + evidence-strength ranking
│   ├── facts.py                   # Facts table builder
│   ├── brief.py                   # Bilingual brief generator
│   └── verification.py            # Numeric claim checker + health claim blocker
├── tests/
│   ├── test_loader.py
│   ├── test_rules.py
│   ├── test_metrics.py
│   ├── test_ranking.py
│   └── test_verification.py
├── output/                        # Generated build artifacts
│   ├── ranking.json
│   ├── evidence.json
│   ├── facts_table.json
│   ├── brief_en.txt
│   ├── brief_hi.txt
│   └── brief.pdf
├── site/                          # Static frontend
│   ├── index.html
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   ├── app.js                 # Main app controller
│   │   ├── ranking-view.js        # Ranked ghat cards
│   │   ├── evidence-view.js       # Evidence drawer + readings table
│   │   ├── gaps-view.js           # "What we don't know" panel
│   │   ├── brief-view.js          # Bilingual brief display + export
│   │   └── charts.js              # Mini phase charts
│   └── fonts/
│       └── NotoSansDevanagari.woff2
├── requirements.txt
└── README.md
```

---

## Part 1: Data Ingestion + Core Logic Engine

### Module 1.1 — Data Loader (`engine/loader.py`)
- Load `bhopal_ghats_2023_2025.csv` with proper encoding
- Parse values: numeric → float, empty → `None`
- Distinguish three states: **numeric**, **BDL/ND** (flag preserved, value=None), **missing/not-sampled** (flag preserved)
- Missing markers: blank, `_`, `-`, `*`, `**`, `not sampled` → state=`missing`
- BDL/ND → state=`bdl` (very low, NOT zero, NOT missing)
- Preserve `value_as_printed`, `site_as_printed`, `parameter_as_printed`
- Load CPCB criteria CSV and extract Class B thresholds

### Module 1.2 — Rules Engine (`engine/rules.py`)
- **DO**: breach if value < 5.0 mg/l (boundary 5.0 = NOT a breach)
- **BOD**: breach if value > 3.0 mg/l (boundary 3.0 = NOT a breach)
- **pH**: breach if value < 6.5 OR value > 8.5 (boundaries 6.5 and 8.5 = NOT a breach)
- **Other parameters** (COD, metals, solids, etc.): NO threshold check, display only
- BDL/ND readings: NOT evaluated as breaches, NOT counted as compliant
- Missing readings: NOT counted in any direction

### Module 1.3 — Per-Ghat Metrics (`engine/metrics.py`)
For each ghat, calculate:
- **Sampled readings** (total numeric readings for DO, BOD, pH)
- **Breach count** per parameter
- **Breach rate** (breaches / sampled readings)
- **Worst value** per parameter
- **Year trend** (improving / stable / worsening)
- **Phase pattern** (pre/during/after coverage)
- **Durga vs Ganesh split** (Durga weighted 2× for planned Durga event)
- **Evidence coverage matrix**: which (year, festival, phase) combos exist

### Module 1.4 — Ranking (`engine/ranking.py`)

#### Severity Score (0–100)
```
severity = (
    0.35 × DO_severity +
    0.35 × BOD_severity +
    0.15 × pH_severity +
    0.15 × worst_value_penalty
)
```
Where each parameter severity = `breach_rate × (1 + worst_value_factor)`  
Durga readings weighted 2× Ganesh readings.

#### Risk Tiers
| Tier | Severity Score | Label |
|---|---|---|
| Critical | ≥ 75 | 🔴 Critical concern |
| High | 50–74 | 🟠 High concern |
| Moderate | 25–49 | 🟡 Moderate concern |
| Lower | < 25 | 🟢 Lower concern (based on available data) |

#### Evidence Strength (separate axis)
| Level | Criteria |
|---|---|
| Strong | ≥ 12 readings across ≥ 4 year-festival-phase combos |
| Moderate | 6–11 readings across ≥ 2 combos |
| Limited | < 6 readings or only 1 combo |

> [!IMPORTANT]
> A ghat with "Limited" evidence NEVER appears implicitly safe. The UI must show evidence gaps prominently.

### Module 1.5 — Facts Table (`engine/facts.py`)
- Every numeric claim that can appear in the brief or UI
- Each fact linked to source readings with `source_page` references
- Format: `{fact_id, claim_text, value, source_readings: [{year, festival, phase, source_page}]}`

### Module 1.6 — Verification (`engine/verification.py`)
- **Numeric auditor**: Extract all numbers from generated text → check each against facts table
- **Health-claim blocker**: Regex phrase list for banned terms:
  - "safe to bathe", "safe for immersion", "will cause disease", "health risk", "toxic", "dangerous to health", "cancer", "illness", etc.
- Verification badge: `"Verified: N of N numbers, 0 health claims"`

### Module 1.7 — Brief Generator (`engine/brief.py`)
- English + Hindi bilingual brief
- Structure:
  1. **Header**: Date, context, data period
  2. **Top-risk ghats** with one-line reason each
  3. **Three action categories**: Testing priorities, Aeration priorities, Cleaning priorities
  4. **Data limitations box**: Missing parameters, incomplete coverage, site ambiguity
  5. **Disclaimer**: Historical data, not live conditions; supports officer's decision, not replacement

---

## Part 2: Backend/Build Pipeline

### `build.py` — Master Build Script
Since architecture is static-site, `build.py` IS the "backend":
1. Run loader → cleaned data
2. Run rules → breach flags
3. Run metrics → per-ghat calculations
4. Run ranking → severity + evidence strength
5. Build facts table → verified claims
6. Generate brief text (English + Hindi) using template-based approach (no LLM dependency)
7. Run verification → audit all generated text
8. Emit: `ranking.json`, `evidence.json`, `facts_table.json`, brief files
9. Print verification report

---

## Part 3: Frontend Dashboard

### 3.1 — Dashboard Layout (`index.html`)
- **Header**: Project title, data period badge, verification status badge
- **Tab navigation**: Dashboard | Evidence | Brief
- **Summary cards row**: Total readings, breach rate, data gaps count, ghats analyzed

### 3.2 — Ranked Ghat Cards
Each card shows:
- Risk tier badge (color-coded)
- Ghat name + water body
- One-sentence reason
- Evidence strength indicator (separate from severity)
- Mini phase chart (sparkline: pre/during/after per year)
- Site ambiguity warning (for Rani Kamlapati)
- Click → opens evidence drawer

### 3.3 — Evidence Drawer
- **Readings table**: year, festival, phase, value, unit, flag, source_page
- Sortable/filterable by parameter, year, festival
- Color-coded: breach = red, compliant = green, BDL = blue, missing = gray
- **"What we don't know" panel**: Missing year-festival-phase combinations
- Source page links

### 3.4 — Bilingual Brief View
- Toggle English ↔ Hindi
- Copy-to-clipboard button
- Print/PDF button (browser print with @media print styles)
- Bundled Noto Sans Devanagari font

---

## Part 4: Export, Polish, Testing

### 4.1 — Export
- Print-friendly CSS with `@media print`
- PDF via browser print dialog
- Copy-ready text for WhatsApp sharing

### 4.2 — Automated Tests
- `test_loader.py`: Missing markers, BDL/ND preservation, row counts
- `test_rules.py`: Boundary tests (DO=5, BOD=3, pH=6.5/8.5)
- `test_metrics.py`: Headline counts (42/116 DO, 100/112 BOD)
- `test_ranking.py`: All 7 ghats present, severity ≠ evidence strength
- `test_verification.py`: Tamper test, health-claim blocking

### 4.3 — README.md
- Team, track, target user
- How to run in ≤ 5 steps
- What works, what doesn't
- Data sources, licence (MIT)

---

## Execution Order

| Step | What | Files Created |
|---|---|---|
| 1 | Set up project structure + copy data | folders, data/ |
| 2 | Build `engine/loader.py` | loader.py |
| 3 | Build `engine/rules.py` | rules.py |
| 4 | Build `engine/metrics.py` | metrics.py |
| 5 | Build `engine/ranking.py` | ranking.py |
| 6 | Build `engine/facts.py` + `engine/verification.py` | facts.py, verification.py |
| 7 | Build `engine/brief.py` | brief.py |
| 8 | Build `build.py` + run pipeline | build.py, output/*.json |
| 9 | Build tests + verify headline counts | tests/ |
| 10 | Build frontend HTML/CSS/JS | site/ |
| 11 | Polish, print styles, README | README.md |

> [!NOTE]
> All formulas, weights, and tier boundaries are **implementation choices** (not source-stated). They are documented here and will be tested. The ranking is deterministic and reproducible.
