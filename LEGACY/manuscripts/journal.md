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

## 2026-04-19T15:42:17+00:00 — `notebooks/07_rdd_and_spatial.py`

> **Status:** error · 2 ran · 0 cached · 1 errored · 2698ms

**Artifacts:**
- `artifacts/rdd_geometry.json` (111 B) — RDD geometry setup
- `artifacts/rdd_sensitivity.parquet` (5.9 KB) — RDD sensitivity: treatment effect × bandwidth × polynomial order
- `artifacts/rdd_summary.json` (95 B) — Local-polynomial RDD setup summary

**Errors:**
- `07_rdd_and_spatial:3 (mccrary_density)` — ValueError: For each axis slice, the sum of the observed frequencies must agree with the sum of the expected frequencies to a relative tolerance of 1.4901161193847656e-08, but the percent differences are:
1.2820100535795798

## 2026-04-19T15:42:19+00:00 — `notebooks/08_extended_robustness.py`

> **Status:** ok · 6 ran · 0 cached · 0 errored · 1904ms

**Artifacts:**
- `artifacts/mde_default.json` (152 B) — MDE at default settings: 20.75 complaints (compare to observed ATT)
- `artifacts/mde_sweep.parquet` (3.5 KB) — Minimum Detectable Effect — sensitivity to ICC and covariate R²
- `artifacts/multi_year_pretrends.json` (238 B) — Multi-year parallel-trends test (2022-May 2024 pre-window)
- `artifacts/multi_year_trends.png` (88.4 KB)
- `artifacts/reporting_bias_em.json` (282 B) — Latent reporting-bias EM (multi-year + demographic covariates)
- `artifacts/bh_correction.parquet` (3.3 KB) — Benjamini-Hochberg multiple-comparison correction across all hypothesis tests
- `artifacts/bh_summary.json` (135 B) — BH correction: 2 → 1 significant tests after FDR control

## 2026-04-19T15:42:34+00:00 — `notebooks/07_rdd_and_spatial.py`

> **Status:** error · 0 ran · 2 cached · 1 errored · 1433ms

**Errors:**
- `07_rdd_and_spatial:3 (mccrary_density)` — NameError: name 'expected_window' is not defined

## 2026-04-19T15:42:43+00:00 — `notebooks/07_rdd_and_spatial.py`

> **Status:** ok · 3 ran · 2 cached · 0 errored · 2975ms

**Artifacts:**
- `artifacts/mccrary_density.json` (262 B) — McCrary-style density continuity test (chi-square variant)
- `artifacts/rdd_scatter.png` (53.4 KB)
- `artifacts/spatial_lag_did.json` (255 B) — Spatial-lag DiD: TWFE + spatial autoregressive residuals

## 2026-04-19T16:12:24+00:00 — `notebooks/07_rdd_and_spatial.py`

> **Status:** ok · 5 ran · 0 cached · 0 errored · 3379ms

**Artifacts:**
- `artifacts/rdd_geometry.json` (111 B) — RDD geometry setup — centroids + treatment-zone center
- `artifacts/rdrobust_setup.json` (128 B) — rdrobust setup summary
- `artifacts/rdrobust_sweep.parquet` (8.5 KB) — rdrobust: kernel × polynomial-order sweep, MSE-optimal bandwidth, robust bias-corrected inference
- `artifacts/density_continuity.json` (604 B) — Density continuity test summary
- `artifacts/density_continuity.parquet` (4.4 KB) — Manual chi-square density continuity at the cutoff (rddensity substitute pending UPSTREAM_ISSUES.md #008)
- `artifacts/rdrobust_plot.png` (64.1 KB)
- `artifacts/spatial_lag_did.json` (312 B) — Spatial-lag DiD: TWFE + spatial autoregressive residuals (3 km neighborhoods)

## 2026-04-19T16:38:26+00:00 — `notebooks/07_rdd_and_spatial.py`

> **Status:** ok · 5 ran · 0 cached · 0 errored · 3883ms

**Artifacts:**
- `artifacts/rdd_geometry.json` (111 B) — RDD geometry setup — centroids + treatment-zone center
- `artifacts/rdrobust_setup.json` (128 B) — rdrobust setup summary
- `artifacts/rdrobust_sweep.parquet` (8.5 KB) — rdrobust: kernel × polynomial-order sweep, MSE-optimal bandwidth, robust bias-corrected inference
- `artifacts/density_continuity.json` (598 B) — Density continuity test summary
- `artifacts/density_continuity.parquet` (4.4 KB) — Manual chi-square density continuity at the cutoff (rddensity substitute pending UPSTREAM_ISSUES.md #008)
- `artifacts/rdrobust_plot.png` (64.1 KB)
- `artifacts/spatial_lag_did.json` (312 B) — Spatial-lag DiD: TWFE + spatial autoregressive residuals (3 km neighborhoods)

## 2026-04-19T16:39:01+00:00 — `notebooks/07_rdd_and_spatial.py`

> **Status:** ok · 5 ran · 0 cached · 0 errored · 3718ms

**Artifacts:**
- `artifacts/rdd_geometry.json` (111 B) — RDD geometry setup — centroids + treatment-zone center
- `artifacts/rdrobust_setup.json` (128 B) — rdrobust setup summary
- `artifacts/rdrobust_sweep.parquet` (8.5 KB) — rdrobust: kernel × polynomial-order sweep, MSE-optimal bandwidth, robust bias-corrected inference
- `artifacts/density_continuity.json` (598 B) — Density continuity test summary
- `artifacts/density_continuity.parquet` (4.4 KB) — Manual chi-square density continuity at the cutoff (rddensity unusable on pandas ≥ 2; no modern alternative as of 2026)
- `artifacts/rdrobust_plot.png` (64.1 KB)
- `artifacts/spatial_lag_did.json` (312 B) — Spatial-lag DiD: TWFE + spatial autoregressive residuals (3 km neighborhoods)

## 2026-04-19T17:38:56+00:00 — `notebooks/09_paper_figures.py`

> **Status:** ok · 10 ran · 0 cached · 0 errored · 17442ms

**Artifacts:**
- `artifacts/paper_v2/figures/F1_timeline.png` (29.6 KB) — Figure 1 — Treatment timeline
- `artifacts/paper_v2/staggered_did_v2.json` (161 B) — Callaway & Sant'Anna staggered DiD (corrected signature)
- `artifacts/paper_v2/scm_trajectory_v2.json` (1008 B) — Synthetic control trajectory (Manhattan 03 vs. weighted donor pool)
- `artifacts/paper_v2/event_study_coefs.parquet` (5.1 KB) — Event-study coefficients (TWFE with τ-dummies, ref τ=-1, clustered SE)
- `artifacts/paper_v2/cd_deltas.parquet` (5.5 KB) — Per-CD pre/post mean monthly complaint deltas (Jun 2024 cutoff)
- `artifacts/paper_v2/figures/F2_choropleth.png` (106.0 KB) — Figure 2 — Per-CD Δ mean monthly complaints, pre vs. post Jun 2024 pilot
- `artifacts/paper_v2/figures/F3_event_study.png` (37.9 KB) — Figure 3 — Event study with pre-treatment leads and post-treatment lags (TWFE, clustered SE)
- `artifacts/paper_v2/figures/F4_scm_trajectory.png` (63.5 KB) — Figure 4 — Synthetic control trajectory for Manhattan 03
- `artifacts/paper_v2/figures/F5_robustness.png` (28.7 KB) — Figure 5 — ATT point estimates across estimators and subsamples
- `artifacts/paper_v2/robustness_bar.parquet` (3.4 KB) — Robustness bar — per-estimator ATT point estimates + (where available) 95% CIs

## 2026-04-19T17:39:09+00:00 — `notebooks/10_paper_tables.py`

> **Status:** ok · 6 ran · 0 cached · 0 errored · 1774ms

**Artifacts:**
- `artifacts/T1_descriptive.parquet` (6.3 KB) — Table 1 — Pre-treatment descriptive statistics (Jan–May 2024)
- `artifacts/paper_v2/tables/T1_descriptive.parquet` (6.3 KB) — Table 1 data
- `artifacts/T2_main_results.parquet` (4.3 KB) — Table 2 — Main results: ATT per estimator with SE, p, 95% CI, N
- `artifacts/paper_v2/tables/T2_main_results.parquet` (4.3 KB) — Table 2 data
- `artifacts/T3_hte.parquet` (4.7 KB) — Table 3 — Heterogeneous treatment effects by pre-treatment volume quartile
- `artifacts/paper_v2/tables/T3_hte.parquet` (5.0 KB) — Table 3 data
- `artifacts/T4_rdd_sensitivity.parquet` (7.4 KB) — Table 4 — RDD sensitivity (rdrobust: kernel × polynomial sweep)
- `artifacts/paper_v2/tables/T4_rdd_sensitivity.parquet` (7.7 KB) — Table 4 data
- `artifacts/T5_diagnostic_checklist.parquet` (6.5 KB) — Table 5 — Diagnostic checklist: assumption × test × value × status
- `artifacts/paper_v2/tables/T5_diagnostic_checklist.parquet` (6.5 KB) — Table 5 data

## 2026-04-19T17:39:30+00:00 — `notebooks/10_paper_tables.py`

> **Status:** ok · 1 ran · 5 cached · 0 errored · 1348ms

**Artifacts:**
- `artifacts/T5_diagnostic_checklist.parquet` (6.6 KB) — Table 5 — Diagnostic checklist: assumption × test × value × status
- `artifacts/paper_v2/tables/T5_diagnostic_checklist.parquet` (6.6 KB) — Table 5 data

## 2026-04-19T17:44:42+00:00 — `notebooks/10_paper_tables.py`

> **Status:** ok · 5 ran · 1 cached · 0 errored · 2125ms

**Artifacts:**
- `artifacts/paper_v2/tables/T1_descriptive.parquet` (6.3 KB) — Table 1 — Pre-treatment descriptive statistics (Jan–May 2024)
- `artifacts/paper_v2/tables/T2_main_results.parquet` (4.3 KB) — Table 2 — Main results: ATT per estimator with SE, p, 95% CI, N
- `artifacts/paper_v2/tables/T3_hte.parquet` (4.7 KB) — Table 3 — Heterogeneous treatment effects by pre-treatment volume quartile
- `artifacts/paper_v2/tables/T4_rdd_sensitivity.parquet` (7.4 KB) — Table 4 — RDD sensitivity (rdrobust: kernel × polynomial sweep)
- `artifacts/paper_v2/tables/T5_diagnostic_checklist.parquet` (6.6 KB) — Table 5 — Diagnostic checklist: assumption × test × value × status
