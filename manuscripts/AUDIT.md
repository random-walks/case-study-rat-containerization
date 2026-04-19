# Audit — rat-containerization showcase (v2)

A statistical / methodological audit of this showcase as it stands
after the canonical-tooling pass (commit topic: rdrobust + tearsheets +
upstream issues). Not a substitute for peer review — a self-audit so
you and I can decide what to upgrade next when we sit down and design
the "proper paper" version of this analysis.

---

## What changed v1 → v2

| Area | v1 | v2 |
|---|---|---|
| RDD engine | `nyc311.stats.regression_discontinuity` (homegrown) | `rdrobust 1.3.0` (Calonico-Cattaneo-Farrell-Titiunik, NSF-funded — SES-1357561, -1459931, -1947805, -2019432). MSE-optimal bandwidth, robust bias-corrected CIs, sweep over kernel × polynomial. |
| McCrary density | hand-rolled chi-square | hand-rolled chi-square *across multiple windows* + flag for [`UPSTREAM_ISSUES.md` #008](../../UPSTREAM_ISSUES.md) (rddensity 2.4.6 broken on pandas 2.x — needs upstream PR before we can swap in canonical) |
| Tearsheets | none | per-notebook tearsheet under `manuscripts/tearsheets/<stem>.md`, regenerable via `jellycell export tearsheet` |
| Manuscripts | METHODOLOGY + DIAGNOSTICS_CHECKLIST + MANUSCRIPT | + this AUDIT.md (self-audit + roadmap) |
| Issues tracking | implicit "future work" bullets in MANUSCRIPT | explicit, structured [`UPSTREAM_ISSUES.md`](../../UPSTREAM_ISSUES.md) at the showcase-package root |

## What's strong

The showcase now cleanly demonstrates the seven canonical diagnostics
that should accompany any DiD-based policy claim:

1. **Pre-treatment balance (SMD)** — notebook 02
2. **Multi-estimator agreement (TWFE + C&S + SCM)** — notebook 03
3. **Residual normality + Q-Q + jackknife + bootstrap CI** — notebook 04
4. **HTE by baseline + within-2024 placebo + seasonal-demeaned** — notebook 05
5. **Local-poly RDD with bandwidth + kernel sweep + density continuity** — notebook 07
6. **Spatial-lag DiD (rho > 0.5, p < 0.001) — substantive flip vs. naive TWFE** — notebook 07
7. **MDE + multi-year parallel trends + reporting-bias EM + BH correction** — notebook 08

Per-notebook tearsheets live in `manuscripts/tearsheets/` and are
regenerable. Diagnostic checklist + methodology + working-paper
manuscript live in `manuscripts/`. Headline JSON artifacts roll up
into `06_synthesis_and_publication.py`.

## What's still gappy

### Statistical

- **Record-level RDD.** Currently runs at CD level (N=59) using
  centroid distance to treatment-zone center. The peninsula geometry
  fails the density-continuity test (artifacts/density_continuity.json,
  p=0.0003 at 15 km). A record-level RDD using individual-complaint
  lat/lon (N≈40,000) with a real boundary distance metric would have
  more power and a more defensible running variable. Blocked on
  [`UPSTREAM_ISSUES.md` #006](../../UPSTREAM_ISSUES.md) — `nyc311.temporal`
  needs to surface a `record_view` companion to the aggregated panel.
- **C&S event-study leads.** `nyc311.stats.staggered_did` returns the
  aggregated ATT. For the multi-year panel we should fit a full
  event-study with pre-treatment leads and visualize the coefficient
  trajectory with pointwise + uniform CIs.
- **Synthetic-control inference.** Current SCM gives a point estimate
  and donor weights. Standard practice (Abadie-Diamond-Hainmueller
  2010) adds a placebo permutation test across the donor pool —
  cross-validation by treating each donor as the treated unit and
  comparing pseudo-ATTs to the real ATT. Not yet implemented.
- **Multiple-testing universe is small.** BH correction in notebook 08
  pools 7 tests; some published applied work pools 30+ (every HTE
  subgroup, every bandwidth × polynomial RDD). Worth expanding the
  family if we want fully family-wise-corrected reporting.
- **Reporting-bias instrument.** EM collapses to uniform ρ — needs an
  external instrument (media coverage, DOH inspection counts, news
  search volume). Notebook 08 documents the constraint; future
  iteration should actually wire in one of those instruments.

### Tooling

- **rddensity pandas 2.x compat** — see `UPSTREAM_ISSUES.md` #008.
  Once upstream lands the patch, swap the manual chi-square in
  notebook 07 for `rddensity(running_var, c=0)`.
- **rdlocrand for randomization inference at small N.** With only 9
  treated CDs, randomization-inference p-values via local-polynomial
  RD designs would be a credibility upgrade. Same `rdpackages` family
  as rdrobust + rddensity.

## What I'd want for a "proper paper" version

When you and I sit down to design the publication-quality version of
this analysis, the additions I'd push for:

### Figures (currently missing)

- **F1 — Treatment timeline.** A simple 2-row Gantt-ish chart showing
  pilot zone (Manhattan 01–09, June 2024) and citywide enforcement
  (all CDs, Nov 12, 2024) with the data window overlaid.
- **F2 — Choropleth of Δ ATT by CD.** Map of NYC CDs colored by
  pre/post change in mean monthly complaints, treated zone outlined.
  We have the geography (boundaries from `nyc311.geographies`); we
  just need to compute the per-CD ΔY and plot.
- **F3 — Event study.** Coefficient plot with pre-treatment leads
  (months -12 to -1) and post-treatment lags (months +1 to +7),
  pointwise + uniform CI bands. Standard in DiD papers.
- **F4 — SCM trajectory.** Two-line plot: actual Manhattan 03
  trajectory vs. weighted synthetic counterfactual, treatment date
  marked. Also standard.
- **F5 — Robustness plot.** Bar chart of estimated ATT from each of:
  TWFE, C&S, Sun-Abraham, SCM, RDD (CD-level), spatial-lag DiD,
  jackknife (low / median / high). Reviewers love these.

### Tables (currently scattered or missing)

- **T1 — Descriptive statistics.** Pre-treatment means, SDs,
  treated-vs-control split, by covariate. The balance table from
  notebook 02 nearly is this — needs slight polish.
- **T2 — Main results.** ATT from each estimator with SE, p, 95% CI,
  N. Notebook 06 already produces a parquet; needs prose framing.
- **T3 — Heterogeneous effects.** ATT × subgroup (baseline volume
  quartile, borough) with SE. Notebook 05 already has the data.
- **T4 — RDD sensitivity.** ATT × bandwidth × polynomial × kernel.
  Notebook 07's `rdrobust_sweep` artifact already produces this.
- **T5 — Diagnostic checklist.** Pass/fail per assumption tested.
  Notebook 06 already produces this — render it as a proper paper-grade
  table.

### Narrative tighten

- **Abstract.** One paragraph stating: research question → design
  (staggered DiD + 6 diagnostics) → finding (sign + significance after
  multi-method consensus) → headline limitation (underpowered, see
  MDE).
- **Mechanism section.** The reporting-awareness vs. real-rat-decline
  question deserves its own subsection in the manuscript with the
  HTE results, the multi-year pre-trend finding, and the
  spatial-spillover finding stitched together. Currently scattered
  across DIAGNOSTICS_CHECKLIST and MANUSCRIPT.
- **Discussion of the RDD's failed density continuity.** Say it
  explicitly: the RDD identifying assumption fails for our running
  variable due to peninsula geometry. The CD-level RDD provides
  *consistency-check* evidence at best; the DiD evidence is the
  primary identification.

## Status of each diagnostic (live)

Numbers update with each rerun; latest values are in the linked JSON.

| # | Test | Notebook | Latest result |
|---|---|---|---|
| 1 | Pre-treatment SMD | 02 | [`balance_table.json`](../artifacts/balance_table.json) |
| 2 | Parallel-trends visual | 02 | [`parallel_trends.png`](../artifacts/parallel_trends.png) |
| 3 | Multi-estimator agreement | 03 | [`multi_estimator_results.parquet`](../artifacts/multi_estimator_results.parquet) |
| 4 | Residual normality (JB, SW) | 04 | [`residual_diagnostics.json`](../artifacts/residual_diagnostics.json) |
| 5 | Q-Q + residuals-vs-fitted | 04 | [`diag_residuals.png`](../artifacts/diag_residuals.png) |
| 6 | Leave-one-treated-out jackknife | 04 | [`jackknife_summary.json`](../artifacts/jackknife_summary.json) |
| 7 | Block bootstrap CI | 04 | [`bootstrap_ci.json`](../artifacts/bootstrap_ci.json) |
| 8 | HTE by baseline | 05 | [`hte_by_baseline.parquet`](../artifacts/hte_by_baseline.parquet) |
| 9 | Within-2024 placebo | 05 | [`placebo_test.json`](../artifacts/placebo_test.json) |
| 10 | Seasonal-demeaned robustness | 05 | [`seasonal_robust.json`](../artifacts/seasonal_robust.json) |
| 11 | rdrobust local-poly sweep | 07 | [`rdrobust_sweep.parquet`](../artifacts/rdrobust_sweep.parquet) |
| 12 | Density continuity (manual chi-square) | 07 | [`density_continuity.json`](../artifacts/density_continuity.json) — FAIL (peninsula) |
| 13 | Spatial-lag DiD | 07 | [`spatial_lag_did.json`](../artifacts/spatial_lag_did.json) — ρ=0.52, p<0.001 |
| 14 | MDE power sweep | 08 | [`mde_default.json`](../artifacts/mde_default.json) — MDE ~21 vs |ATT| ~7 |
| 15 | Multi-year parallel trends | 08 | [`multi_year_pretrends.json`](../artifacts/multi_year_pretrends.json) — FAIL (p≈0.05) |
| 16 | Latent reporting-bias EM | 08 | [`reporting_bias_em.json`](../artifacts/reporting_bias_em.json) — uniform ρ (underdetermined) |
| 17 | BH correction | 08 | [`bh_summary.json`](../artifacts/bh_summary.json) |
