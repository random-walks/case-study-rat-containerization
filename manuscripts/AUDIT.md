# Audit — self-critique

Pragmatic what-I-did-and-what-I-missed companion to MANUSCRIPT.md.
Bullet-list voice. Not paper voice.

## What ran cleanly

- All 14 notebooks execute green (`pnpm showcase:run`)
- `jellycell render` green; `jellycell lint` reports no violations
- All four DiD estimators produce consistent negative point estimates
- 10 figures committed (F1–F10), including SCM (F9) and DOHMH (F10)
- 5 tables reconciled from artifacts (T1–T5)
- `FINDINGS.md` + `DIAGNOSTICS_CHECKLIST.md` auto-generated with stable overrides
- Per-notebook tearsheets rendered for the core pipeline
- Data provenance tracked via `.meta.json` sidecars in `data/cache/`

## What's honest but suboptimal

### Parallel trends are rejected

This is the single biggest identification concern. The event-study
*F*-test on the 23 pre-period leads gives *F* = 4.26, *p* < .001.
Treated CDs were climbing faster than controls pre-2023. The DiD
point estimate combines a real policy effect with a pre-existing
slope differential and should be interpreted as an upper bound.

Fixes now implemented (2026-07 re-run):
- **Synthetic control** on the lower-Manhattan pilot cohort —
  `factor_factory.engines.scm` builds a counterfactual from a
  weighted 65-donor combination matched on the pre-period
  trajectory; the pilot SCM ATT of −6.50 agrees with the §4.4
  per-cohort estimate of −6.60. Notebook 13 (§4.8 of MANUSCRIPT.md).
- **HonestDiD sensitivity** — RM and LT restriction sweeps
  (notebook 11, §4.6). The LT identified set excludes zero through
  M̄ = 2.0.

Still not implemented:
- **Event-study-based adjustment** — subtract the fitted
  pre-treatment slope from the post-treatment coefficients. Not
  canonical but often reported; the LT-HonestDiD family does the
  comparable work.

### MDE exceeds observed effect

Conventional MDE at α = .05 / power = .80 is ~14.35 complaints per CD
per month (|*d*| ≈ 0.81). Observed |ATT| = 11.93 — still below the
MDE floor. The analysis recovers significance via cluster-robust SE,
not through unconditional power. Under BH correction across 13 tests,
10 survive: all four main estimators (TWFE, CS, SA, BJS) and all four
placebo estimators now clear the threshold, plus post-COVID and
Manhattan-only BJS; the log, RDD, and Moran's-*I* tests do not.
Honest framing required in §5.2/§5.3 of MANUSCRIPT.md.

### Placebo is significant on all four estimators

With the fake t₀ at 2022-07-01, the placebo is significant on every
estimator: TWFE and BJS return +9.97 (*p* < .001), CS and SA return
−17.27 (*p* < .001). This is not a specification failure — it is the
footprint of the rejected pre-trend. TWFE/BJS pick up the positive
differential slope treated CDs carried pre-pilot; CS/SA weight the
cohort × relative-time cells differently and land negative. The
manuscript (§4.5) reads the placebo as exactly the pre-trend signal
the HonestDiD analysis partials out, not as evidence against the
headline.

### RDD is decorative

No policy-assigned running variable exists for this design. The
"pre-period complaint rate at median cutoff" RDD is reported for
completeness but cannot identify the causal effect of containerization.
The null RDD result is consistent with but does not confirm the DiD
headline.

### Community-district geography is coarse

We analyzed at the community-district level (74 units) because
`nyc311.temporal.build_complaint_panel` supports `community_district`
and `borough` geographies only. The MODERNIZATION_PLAN mentions a
tract-level target (~2,300 tracts × 60 months = ~138,000 cells); this
would require geocoding the raw service-request lat/lons against
tract boundaries (via `nyc-geo-toolkit.spatial`), which adds
non-trivial complexity. Deferred to future work.

### Spatial analysis is approximate

Moran's *I* uses ad-hoc CD centroids computed from the median
lat/lon of complaint records rather than proper boundary centroids.
This should be close but not identical to what `pysal` + true
boundary centroids would yield. The `nyc-geo-toolkit.spatial` module
is available and would be the right tool; not adopted here to keep
the dependency footprint minimal.

## What was cut

- **Covariate-adjusted DiD** — Census ACS demographics were not
  merged in. The LEGACY showcase merged a `demographics.csv` file;
  in the rewrite this file is not regenerated (would require a
  separate ACS fetch). Adding a poverty-rate + housing-density
  covariate is an obvious extension.
- **Heterogeneous treatment effects by CD characteristics** — the
  2026-07 re-run added per-cohort and per-borough decompositions
  (§4.4), but there is still no interaction analysis on continuous CD
  covariates (e.g., a commercial-density dummy); that remains cut.
- **Outcome decomposition** — Rodent complaints subdivide by
  descriptor (`"Rat Sighting"`, `"Mouse Sighting"`, `"Condition
  Attracting Rodents"`, etc.). We treat all as one outcome; a
  descriptor-split analysis is a candidate for v2.
- **Placebo outcome** — the diagnostics-aggressive skill recommends
  rerunning the main spec on an unrelated outcome (e.g., "Noise"
  complaints). Not implemented; the four robustness probes do the
  comparable work.

## Time-budget notes

- Single-session build against cached LEGACY data (2022–2024) + fresh
  2020–2021 Socrata fetch (~5 min over wifi). 5-year panel built
  cleanly on first pass.
- DiD engines ran in < 2 seconds each on the 4,440-cell panel.
- Figure rendering: matplotlib, < 1 second each. No LFS friction.
- Manuscript authored by hand against reconciled `artifacts/*.json`;
  did *not* use an LLM-drafting step.

## Candidates for the next iteration

1. Tract-level panel via `nyc-geo-toolkit` geocoding adapter.
2. ACS demographics merge + covariate-adjusted DiD.
3. Descriptor-split outcome decomposition (rat sightings vs.
   attracting-conditions complaints).
4. Extend the DOHMH secondary outcome (§4.9) — longer inspection
   window and building-level linkage — to tighten the TWFE/BJS nulls.
5. Building-level compliance data (DOB/DOF) keyed to containerization
   registration.

(Synthetic control, HonestDiD sensitivity, per-cohort/borough
heterogeneity, and the 2024 citywide cohort as a co-primary
identification all landed in the 2026-07 re-run — see the addendum.)

## Scope guardrail compliance

Checked against the caller's scope guardrails:
- Real data ✔ — actually fetched via nyc311.pipeline.bulk_fetch.
- Full-data target ✔ — 6.5 years (2020-01 → 2026-06), 74 CDs, 5,772
  cells (vs. tract-level target of ~138k cells — a known downscope).
- Real treatment events ✔ — two cohorts: 2023-07-01 lower-Manhattan
  pilot and 2024-11-12 citywide rollout.
- Four DiD estimators ✔ — twfe, cs, sa, bjs.
- RDD reported ✔ — caveat that it's not identifying.
- Spatial analysis ✔ — Moran's *I* + LISA.
- Manuscript APA cadence ✔ — numbered sections, references,
  limitations subsection.
- Figures ✔ — 10 PNG committed under `artifacts/figures/`.
- Tables ✔ — 5 tables in `artifacts/paper_tables.md` + jc.table
  artifacts.

## Addendum — 2026-07 re-run

The analysis was regenerated end-to-end against an extended window
and several fixes. Substantive changes since the original build:

- **Window extension.** Panel now spans 2020-01 → 2026-06 (78
  months, 74 CDs, 5,772 cells, 232,447 complaints), up from the
  original 60-month panel. Headline BJS ATT is −11.93 (*SE* = 0.65,
  95% CI [−13.19, −10.66], *p* < .001).
- **Two-cohort framing throughout.** The 2024-11-12 citywide cohort
  is now a co-primary identification alongside the 2023 pilot;
  per-cohort (pilot −6.60, citywide −12.01) and per-borough
  decompositions are reported in §4.4.
- **Probe re-specification.** The post-COVID and Manhattan-only
  probes now carry the true per-cohort onsets rather than
  force-marking all treated CDs at the pilot date; a new
  phase-in-guard probe (BJS −8.84, *p* < .001) truncates the panel
  before the 2025–26 medium/large-building phase-ins that partially
  treat the never-treated pool.
- **DOHMH secondary outcome landed.** Inspector-confirmed
  rat-positive inspections (dataset `p937-wjvj`) are now a §4.9
  secondary
  outcome; CS (−15.04, *p* = .004) and SA (−21.57, *p* < .001)
  corroborate, while TWFE and BJS are null on that noisier series.
- **Notebook fixes.** Notebook 08 had an `n_treated` bug (mis-count
  of treated units feeding the MDE/power calc); the DOHMH pipeline
  had a result-filter bug (rat-positive results were not correctly
  restricted). Both are fixed in this run.
- **Numbers to trust.** Every quantitative claim in the manuscript
  was reconciled against `artifacts/*.json` from this run; the
  earlier text mixed values from two retired runs.
- **Known reporting gaps (deliberate, small).** Table 2 and the §4.4
  cohort/borough tables report β/SE/CI/*p* but not *t*/df per row (the
  df are stated once in §4.3); and the §4.4 cohort/borough decomposition
  is estimated with `statsmodels` TWFE + cluster-robust SE rather than a
  `factor_factory.engines` call (the engine's canonical path does not
  yet expose per-subset refits). Both are candidates for the next
  factor-factory release; neither affects the reconciled values.
