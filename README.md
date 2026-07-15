# case-study-rat-containerization

A causal evaluation of NYC's staggered rat-mitigation containerization
rollout using NYC 311 Rodent-complaint data and four
difference-in-differences estimators (TWFE, Callaway-Sant'Anna,
Sun-Abraham, Borusyak-Jaravel-Spiess).

**Research question**: did mandatory bin containerization — the 2023
lower-Manhattan pilot (MN 01–09, 2023-07-01) and the 2024 citywide
rollout to 1–9-unit residential buildings (50 CDs, 2024-11-12) —
causally reduce rodent-complaint volume?

**Headline**: BJS ATT = -11.93 rodent complaints per community
district per month (*SE* = 0.65, 95% CI [-13.19, -10.66], *p* < .001,
*N* = 5,772, 74 CDs × 78 months). Both cohorts show negative effects,
with the 2024 citywide rollout (-12.01) running roughly twice the
2023 pilot (-6.60). All four estimators agree in sign; the result
survives five robustness probes — including a phase-in-guard probe
that pre-dates the 2025–26 building phase-ins (-8.84) — is reproduced
by a parallel-trends-free synthetic control on the pilot cohort
(-6.50), and is directionally corroborated by a DOHMH
inspector-confirmed secondary outcome. It rests on a parallel-trends
assumption the data reject (*F*(23, 73) = 4.26, *p* < .001), so read
the point estimate as an upper bound; HonestDiD bounds (§4.6) are the
formal defense. Full discussion: `manuscripts/MANUSCRIPT.md`.

> Standalone repo since 2026-07 — extracted with full history from
> `blaise-website` `packages/python-showcase/`. The published post at
> <https://blaiseoss.com/posts/rat-containerization> is generated from
> `manuscripts/MANUSCRIPT.md` by the blaise-dev-workspace sync
> (`scripts/sync-case-study.sh rat`); never edit the MDX directly.

## Run

From the repo root (Python 3.12 + [uv](https://docs.astral.sh/uv/)):

```bash
uv sync                    # resolve + install into .venv
for nb in notebooks/[0-9]*.py; do uv run jellycell run "$nb"; done
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
│   ├── 09_paper_figures.py             ← F1-F10 index
│   ├── 10_paper_tables.py              ← T1-T5 reconciled
│   ├── 11_honestdid_sensitivity.py     ← RM + LT bound sweeps
│   ├── 12_heterogeneous_effects.py     ← per-cohort + per-borough decomposition
│   ├── 13_synthetic_control.py         ← pilot + citywide SCM + placebo permutation
│   └── 14_dohmh_secondary_outcome.py   ← DOHMH rat-inspection secondary outcome
├── data/
│   ├── README.md
│   ├── cache/                          ← gitignored; built on first run
│   └── rat_mitigation_events_2023.json ← hand-curated two-cohort treatment spec
├── artifacts/                          ← committed JSON + PNG + CSV
├── manuscripts/
│   ├── MANUSCRIPT.md                   ← hand-authored paper
│   ├── METHODOLOGY.md                  ← hand-authored; identification + pipeline
│   ├── FINDINGS.md                     ← auto-generated, byte-stable
│   ├── DIAGNOSTICS_CHECKLIST.md        ← auto-generated
│   ├── AUDIT.md                        ← hand-authored self-critique
│   └── tearsheets/                     ← per-notebook tearsheets
└── site/                               ← gitignored HTML render
```

## Data source

NYC Open Data Socrata dataset `erm2-nwe9` (311 Service Requests from
2010 to Present), filtered to `complaint_type = "Rodent"`, spanning
2020-01-01 through 2026-06-30. 232,447 records, aggregated to 74
community districts × 78 months. The secondary outcome (notebook 14)
adds DOHMH rat-inspection results from dataset `p937-wjvj`.

## Treatment source

`data/rat_mitigation_events_2023.json` — hand-curated from NYC DSNY
press releases, tagged by cohort. Two cohorts: the nine
lower-Manhattan pilot CDs (MN 01–09) effective 2023-07-01, and the 50
citywide-rollout CDs effective 2024-11-12. Fifteen irregular CDs
carry no event date and serve as the never-treated control pool.

## Stack

- `nyc311` 1.0.3 — pipeline + panel builder + factor-factory adapter
- `factor-factory` 1.0.3 — DiD + RDD + spatial + SCM engines
- `jellycell` 1.4.0 — reproducible notebook cache + HTML catalogue
- `rdrobust` — regression-discontinuity (via factor-factory)
- `statsmodels` — TWFE diagnostics, Breusch-Pagan, Shapiro-Wilk
- `scipy` — Welch *t*, Shapiro-Wilk, multiple-comparison corrections
