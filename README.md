# case-study-rat-containerization

A causal evaluation of NYC's 2023 rat-mitigation containerization pilot
using NYC 311 Rodent-complaint data and four difference-in-differences
estimators (TWFE, Callaway-Sant'Anna, Sun-Abraham,
Borusyak-Jaravel-Spiess).

**Research question**: did the mandatory bin-containerization pilot,
launched 2023-07-01 in nine lower-Manhattan community districts,
causally reduce rodent-complaint volume?

**Headline**: BJS ATT = -15.29 rodent complaints per community
district per month (*SE* = 2.35, 95% CI [-19.90, -10.69], *p* < .001,
*N* = 4,440, 74 CDs × 60 months). All four estimators agree in
sign; the result survives four robustness probes but rests on a
parallel-trends assumption that the data reject (*F*(23, 73) = 7.90,
*p* < .001). Interpret the point estimate as an upper bound on the
true policy effect. Full discussion: `manuscripts/MANUSCRIPT.md`.

> Standalone repo since 2026-07 — extracted with full history from
> `blaise-website` `packages/python-showcase/`. The published post at
> <https://blaiseoss.com/posts/rat-containerization> is generated from
> `manuscripts/MANUSCRIPT.md` by the blaise-dev-workspace sync
> (`scripts/sync-case-study.sh rat`); never edit the MDX directly.

## Run

From the repo root (Python 3.12 + [uv](https://docs.astral.sh/uv/)):

```bash
uv sync                    # resolve + install into .venv
uv run jellycell run       # all notebooks in order
uv run jellycell render    # → site/index.html
uv run jellycell lint
uv run jellycell view      # live catalogue @ :5180
```

First run fetches the Socrata CSVs into `data/cache/` (gitignored,
~10–15 min on a cold cache; needs network). Subsequent runs hit the
local cache.

## Structure

```
case-study-rat-containerization/
├── jellycell.toml
├── notebooks/
│   ├── 01_load_and_preprocess.py       ← nyc311.bulk_fetch + build Panel
│   ├── 02_balance_and_pretrends.py
│   ├── 03_main_effects.py              ← 4-estimator DiD
│   ├── 04_diagnostics.py               ← event study + residuals
│   ├── 05_robustness.py                ← 4 probes
│   ├── 06_synthesis.py                 ← emits FINDINGS + DIAGNOSTICS_CHECKLIST
│   ├── 07_rdd_and_spatial.py           ← RDD sensitivity + Moran's I + LISA
│   ├── 08_extended_robustness.py       ← MDE + BH correction + power curve
│   ├── 09_paper_figures.py             ← F1-F6 index
│   └── 10_paper_tables.py              ← T1-T5 reconciled
├── data/
│   ├── README.md
│   ├── cache/                          ← gitignored; built on first run
│   └── rat_mitigation_events_2023.json ← hand-curated treatment spec
├── artifacts/                          ← committed JSON + PNG + CSV
├── manuscripts/
│   ├── MANUSCRIPT.md                   ← hand-authored paper (~3,100 words)
│   ├── METHODOLOGY.md                  ← hand-authored; identification + pipeline
│   ├── FINDINGS.md                     ← auto-generated, byte-stable
│   ├── DIAGNOSTICS_CHECKLIST.md        ← auto-generated
│   ├── AUDIT.md                        ← hand-authored self-critique
│   └── tearsheets/                     ← 10 per-notebook tearsheets
└── site/                               ← gitignored HTML render
```

## Data source

NYC Open Data Socrata dataset `erm2-nwe9` (311 Service Requests from
2010 to Present), filtered to `complaint_type = "Rodent"`, spanning
2020-01-01 through 2024-12-31. 377,950 records, aggregated to 74
community districts × 60 months.

## Treatment source

`data/rat_mitigation_events_2023.json` — hand-curated from NYC DSNY
press releases. Nine lower-Manhattan community districts (MN 01–09)
effective 2023-07-01.

## Stack

- `nyc311` 1.0.0 — pipeline + panel builder + factor-factory adapter
- `factor-factory` 1.0.2 — DiD + RDD + spatial engines
- `jellycell` 1.3.5 — reproducible notebook cache + HTML catalogue
- `rdrobust` — regression-discontinuity (via factor-factory)
- `statsmodels` — TWFE diagnostics, Breusch-Pagan, Shapiro-Wilk
- `scipy` — Welch *t*, Shapiro-Wilk, multiple-comparison corrections
