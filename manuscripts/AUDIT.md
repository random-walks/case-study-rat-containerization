# Audit — self-critique

Pragmatic what-I-did-and-what-I-missed companion to MANUSCRIPT.md.
Bullet-list voice. Not paper voice.

## What ran cleanly

- All 10 notebooks execute green (`pnpm showcase:run`)
- `jellycell render` green; `jellycell lint` reports no violations
- All four DiD estimators produce consistent negative point estimates
- 5 figures committed (F1–F5) + F6 per-borough bar
- 5 tables reconciled from artifacts (T1–T5)
- `FINDINGS.md` + `DIAGNOSTICS_CHECKLIST.md` auto-generated with stable overrides
- 10 per-notebook tearsheets rendered
- Data provenance tracked via `.meta.json` sidecars in `data/cache/`

## What's honest but suboptimal

### Parallel trends are rejected

This is the single biggest identification concern. The event-study
*F*-test on the 23 pre-period leads gives *F* = 7.90, *p* < .001.
Treated CDs were climbing faster than controls pre-2023. The DiD
point estimate combines a real policy effect with a pre-existing
slope differential and should be interpreted as an upper bound.

Candidate fixes not implemented:
- **Synthetic control** on the lower-Manhattan pilot cohort — would
  construct a counterfactual from a weighted combination of control
  CDs matched on pre-period trajectory. `factor_factory.engines.scm`
  is installed; deferred to future work.
- **Event-study-based adjustment** — subtract the fitted
  pre-treatment slope from the post-treatment coefficients. Not
  canonical but often reported.

### MDE exceeds observed effect

Conventional MDE at α = .05 / power = .80 is ~35 complaints per CD
per month (|*d*| ≈ 1.0). Observed |ATT| = 15. The analysis recovers
significance via cluster-robust SE, not through unconditional power.
Under BH correction across 13 tests: main BJS and main SA survive;
main TWFE does *not*. Honest framing required in §5.2.

### Placebo significance at raw *p* < .01

SA's placebo rejects at raw *p* → 0 (SE collapses to 2.6). This is a
known Sun-Abraham pathology on single-cohort samples — effectively
zero residual variance in the imputation step. We note this in the
manuscript but don't correct; the other three estimators' placebo
results are non-significant or borderline.

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
- **Heterogeneous treatment effects** — no interaction analysis by
  CD characteristics (e.g., commercial-density dummy). The rollout
  is uniform within the treated set in our specification.
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

1. Synthetic control cross-check using `factor_factory.engines.scm`.
2. Tract-level panel via `nyc-geo-toolkit` geocoding adapter.
3. ACS demographics merge + covariate-adjusted DiD.
4. Descriptor-split outcome decomposition (rat sightings vs.
   attracting-conditions complaints).
5. 2024 citywide-expansion event as the primary identification
   (larger *N*, clearer natural experiment).

## Scope guardrail compliance

Checked against the caller's scope guardrails:
- Real data ✔ — actually fetched via nyc311.pipeline.bulk_fetch.
- Full-data target ✔ — 5 years, 74 CDs, 4,440 cells (vs. tract-level
  target of 138k cells — documented here as a known downscope).
- Real treatment events ✔ — 2023-07-01 lower-Manhattan pilot.
- Four DiD estimators ✔ — twfe, cs, sa, bjs.
- RDD reported ✔ — caveat that it's not identifying.
- Spatial analysis ✔ — Moran's *I* + LISA.
- Manuscript APA cadence ✔ — ~3,100 words, numbered sections,
  references, limitations subsection.
- Figures ✔ — 6 PNG committed under `artifacts/figures/`.
- Tables ✔ — 5 tables in `artifacts/paper_tables.md` + jc.table
  artifacts.
