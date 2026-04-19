# showcase-rat-containerization — analysis journal

Append-only run log written by `jellycell run`. Each section below is
one invocation: timestamp, notebook, cell-change summary, and any new
or updated artifacts. Safe to hand-edit for commentary — the next
`jellycell run` only appends at the bottom.

Disable via `[journal] enabled = false` in `jellycell.toml`.

## 2026-04-19T07:59:12+00:00 — `notebooks/01_load_and_preprocess.py`

> **Status:** ok · 3 ran · 0 cached · 0 errored · 1018ms

**Artifacts:**
- `artifacts/panel_summary.json` (210 B) — 2024 rat-complaint panel summary
- `artifacts/monthly_means_by_group.parquet` (3.0 KB) — Mean monthly complaints — treated vs. control districts (2024)
- `artifacts/top_10_districts.parquet` (2.4 KB) — Top 10 districts by 2024 rodent complaint volume

## 2026-04-19T07:59:14+00:00 — `notebooks/02_balance_and_pretrends.py`

> **Status:** ok · 2 ran · 0 cached · 0 errored · 1250ms

**Artifacts:**
- `artifacts/balance_table.json` (834 B) — Pre-treatment SMD balance
- `artifacts/pretreatment_balance.parquet` (4.0 KB) — Pre-treatment covariate balance (treated 9 Manhattan CDs vs. control)
- `artifacts/parallel_trends.png` (65.8 KB)

## 2026-04-19T07:59:16+00:00 — `notebooks/03_main_effects.py`

> **Status:** ok · 5 ran · 0 cached · 0 errored · 1485ms

**Artifacts:**
- `artifacts/twfe_result.json` (146 B) — Two-way FE: complaint_count ~ treatment + district FE + month FE (clustered SE)
- `artifacts/staggered_did.json` (89 B) — Staggered DiD — failed
- `artifacts/synthetic_control.json` (93 B) — SCM — failed
- `artifacts/multi_estimator_results.parquet` (3.5 KB) — DiD estimators side-by-side

## 2026-04-19T07:59:27+00:00 — `notebooks/04_diagnostics.py`

> **Status:** ok · 4 ran · 0 cached · 0 errored · 10471ms

**Artifacts:**
- `artifacts/residual_diagnostics.json` (187 B) — TWFE residual normality tests
- `artifacts/diag_residuals.png` (41.8 KB)
- `artifacts/jackknife_summary.json` (101 B) — Jackknife range across treated districts
- `artifacts/jackknife_treated.parquet` (2.8 KB) — Leave-one-treated-out jackknife: TWFE ATT after dropping each treated district
- `artifacts/bootstrap_ci.json` (108 B) — Block bootstrap (B=200, resampling districts)

## 2026-04-19T07:59:29+00:00 — `notebooks/05_robustness_and_mechanism.py`

> **Status:** ok · 3 ran · 1 cached · 0 errored · 1478ms

**Artifacts:**
- `artifacts/hte_by_baseline.parquet` (3.4 KB) — Heterogeneous treatment effects — TWFE stratified by pre-treatment baseline volume
- `artifacts/placebo_test.json` (494 B) — Pre-treatment placebo (treatment moved earlier)
- `artifacts/seasonal_robust.json` (178 B) — TWFE on district-demeaned outcome

## 2026-04-19T07:59:30+00:00 — `notebooks/06_synthesis_and_publication.py`

> **Status:** ok · 4 ran · 0 cached · 0 errored · 1015ms

**Artifacts:**
- `artifacts/main_results_summary.parquet` (4.1 KB) — Main results: ATT estimates across three estimators
- `artifacts/diagnostic_checklist.parquet` (3.9 KB) — Diagnostic checklist — pass/fail per assumption tested
- `artifacts/headline_findings.json` (618 B) — Headline findings — full pipeline
