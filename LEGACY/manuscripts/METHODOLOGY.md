# Methodology — rat-containerization

## Research question

Did the **2024 NYC rat containerization mandate** (pilot June 2024 in
Manhattan CDs 01–09; citywide enforcement Nov 12, 2024) reduce 311
rodent complaints in treated districts relative to controls?

## Identification

The natural experiment is staggered-but-clean: nine adjacent Manhattan
community districts received the pilot mandate in June 2024 while the
remaining 59 districts continued as control through Dec 2024. The
short post-treatment window (7 months) limits dynamic-effect detection,
which we treat as a known constraint rather than ignore.

### Assumptions

1. **Parallel trends.** Treated and control districts would have moved
   in parallel absent the mandate. Tested via the placebo regression
   in `05_robustness_and_mechanism.py` (treatment shifted to Jan 2024,
   restricted to the pre-true-treatment window). PASS = ATT ≈ 0.
2. **SUTVA / no spillovers.** One district's treatment doesn't affect
   another's outcome. Spatial spillovers across CD boundaries (e.g.,
   rats relocating from treated to neighboring untreated zones) would
   bias the ATT downward. Not formally tested in this showcase — flagged
   as a limitation in the diagnostic checklist.
3. **No anticipation.** Districts didn't change behavior pre-June 2024
   in anticipation of the mandate. The November citywide enforcement
   announcement complicates this — control districts learning of
   imminent rules might shift reporting behavior.

## Estimation strategy

Three estimators side-by-side (notebook 03), explicitly chosen for
their differing assumptions:

1. **Two-way fixed effects** — district + month FE, clustered SE at
   district level. Transparent baseline; sensitive to staggered
   treatment heterogeneity.
2. **Callaway & Sant'Anna staggered DiD** — heterogeneity-robust;
   aggregates group-time ATTs via inverse-variance weighting.
3. **Synthetic control** (Manhattan CD 03 only) — donor-weighted
   counterfactual; useful when you don't trust pooled DiD.

If the three converge, that's strong evidence. If they diverge, the
direction and magnitude of divergence is itself a finding.

## Diagnostics (notebook 04)

Each report below is a JSON artifact under `artifacts/`:

- **Residual normality** — Jarque-Bera + Shapiro-Wilk on TWFE residuals
- **Q-Q plot + residuals-vs-fitted** — visual heteroskedasticity check
- **Leave-one-treated-out jackknife** — drop each treated district,
  refit; report ATT range
- **Block bootstrap CI** — resample districts with replacement (B=200
  default), refit TWFE on each replicate, percentile CI

## Robustness (notebook 05)

- **HTE by baseline volume** — stratify districts by pre-treatment
  median; refit ATT separately. Tests whether the pooled ATT masks
  divergent subgroup effects.
- **Placebo test** — pretend treatment was Jan 2024; restrict to
  pre-true-treatment data; ATT should be ≈ 0.
- **Seasonal-adjusted outcome** — refit on district-demeaned
  complaints. (Full year-over-year differencing requires multi-year
  data; this showcase uses 2024 only.)

## Data

Real Socrata pull, fetched via `nyc311.pipeline.bulk_fetch`:

- **Complaint type:** Rodent (all subtypes)
- **Window:** 2024-01-01 through 2024-12-31
- **Geography:** community district
- **Total records:** 39,725 across 5 boroughs
- **Demographics:** ACS 2022 5-year estimates for 51 community
  districts (vendored from upstream; small file, real values)

## Differences from upstream

The upstream `random-walks/nyc311` analysis (`examples/case_studies/rat_containerization/`)
reports four point estimates (DiD, SCM, RDD, power) but lacks
**covariate balance checks**, **spec-robustness comparisons**,
**leave-one-out / bootstrap diagnostics**, **HTE analysis**, and
**placebo / seasonal-robustness checks**. This showcase fills those
gaps. The exact list of additions vs. upstream is in
[`DIAGNOSTICS_CHECKLIST.md`](DIAGNOSTICS_CHECKLIST.md).

## References

- Callaway, B., & Sant'Anna, P. H. C. (2021). Difference-in-differences
  with multiple time periods. *J. Econometrics*, 225(2), 200–230.
- Abadie, A., Diamond, A., & Hainmueller, J. (2010). Synthetic control
  methods for comparative case studies. *JASA*, 105(490), 493–505.
- Goodman-Bacon, A. (2021). Difference-in-differences with variation
  in treatment timing. *J. Econometrics*, 225(2), 254–277.
- Cameron, A. C., & Miller, D. L. (2015). A practitioner's guide to
  cluster-robust inference. *J. Human Resources*, 50(2), 317–372.
