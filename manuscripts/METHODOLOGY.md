# Methodology

Hand-authored companion to `MANUSCRIPT.md`. Covers identification,
data pipeline, and specification choices at the level of detail that
would otherwise clutter the paper body.

## 1. Data pipeline

### 1.1 Source

NYC Open Data Socrata dataset `erm2-nwe9` (311 Service Requests from
2010 to Present), filtered to `complaint_type = "Rodent"`. All
records are retrieved via the `nyc311` v1.0 `bulk_fetch` helper,
which splits downloads by borough to keep per-file sizes below 300
MB. Each borough-year CSV pairs with a `.meta.json` sidecar
recording row count, SHA-256 checksum, fetch timestamp, and filter
parameters.

### 1.2 Panel construction

`nyc311.temporal.build_complaint_panel` aggregates records to the
community-district × month level with balanced filling: any
(CD, month) cell without a complaint is filled with zero rather than
dropped. Over the 2020-01 through 2026-06 window this produces a
rectangular 74 × 78 panel with 5,772 cells (232,447 Rodent
complaints), which the
`factor_factory.tidy.Panel.to_factor_factory_panel`
adapter casts into the canonical `factor_factory.tidy.Panel`
contract for consumption by the DiD engines.

### 1.3 Treatment specification

Treatment is a two-cohort staggered-DiD design. The pilot cohort —
the nine lower-Manhattan community districts MN 01–09 — flips from 0
to 1 on 2023-07-01; the citywide cohort — the 50 remaining real CDs
across the other boroughs — flips on 2024-11-12. Each unit remains
treated for the duration of its post-period, and 15 irregular CDs
(airports, parks, cemeteries, and Unspecified geocoding-failure rows)
carry no event date and serve as the never-treated control pool. The
treatment event file is `data/rat_mitigation_events_2023.json`,
hand-curated from DSNY press releases dated 2023-06-15, 2024-02-20,
and 2024-06-12, with each event tagged by cohort.

## 2. Identification

### 2.1 DiD specification

    Y_it = α_i + γ_t + β · (TREATED_i × Post_t) + ε_it

- α_i: CD fixed effects (74 dummies)
- γ_t: period fixed effects (78 dummies)
- TREATED_i × Post_t: the interaction whose coefficient β is the ATT
- SE: cluster-robust at `unit_id` (community district)

The equation above is the pooled TWFE for exposition; the
heterogeneity-robust estimators (CS, SA, BJS) replace the single
interaction with cohort × relative-time structure that respects the
staggered onsets described in §1.3.

### 2.2 Why four estimators

TWFE is known to produce biased point estimates in staggered-adoption
settings when treatment effects are heterogeneous across cohorts or
time (Goodman-Bacon, 2021; de Chaisemartin & D'Haultfœuille, 2020;
Baker, Larcker, & Wang, 2022). Our design has two cohorts with
visibly different per-CD effects (the 2024 citywide rollout runs
roughly twice the 2023 pilot), so TWFE is *not* rescued from the
"forbidden comparison" contamination — which is precisely why we
report the three heterogeneity-robust estimators (CS, SA, BJS)
alongside it.

Expected behavior under two-cohort staggered adoption with
heterogeneous ATT:
- TWFE and BJS no longer coincide mechanically; their spread is a
  read on cohort heterogeneity rather than a bug.
- CS and SA weight cohort × relative-time cells differently, so their
  point estimates diverge from each other and from BJS by an amount
  that indexes heterogeneity.
- Sign agreement across the four is the robustness bar; magnitude
  agreement is not expected under heterogeneity (Roth et al., 2023).

### 2.3 Cluster-robust inference

All four estimators use cluster-robust standard errors at the
community-district level. This allows within-CD serial correlation
across months without bias in the SE, but assumes independence
across CDs. Spatial proximity could plausibly violate this
assumption (adjacent CDs might share shocks); however, Moran's *I*
on the per-CD change is near zero (§4.7 of MANUSCRIPT.md), which
makes the single-level cluster adequate.

### 2.4 Parallel-trends check

The event study in §4.3 of MANUSCRIPT.md rejects flat pre-period
leads at *F*(23, 73) = 4.26, *p* < .001. This is the identification
concern; the magnitude of the treatment effect should be interpreted
as an upper bound (see §5.3 limitation 1 of MANUSCRIPT.md).

## 3. Robustness strategy

Five probes, each changing a single specification choice. The
post-COVID and Manhattan-only probes were re-specified for the
two-cohort design: the earlier single-cohort code force-marked all
59 treated CDs at the 2023 pilot date, mis-timing the 50 citywide
CDs by ~16 months; both now carry the true per-cohort onsets
(MN 01–09 at 2023-07-01, the citywide 50 at 2024-11-12).

| Probe | Changes | Rationale |
| :--- | :--- | :--- |
| Placebo t₀ | 2023-07-01 → 2022-07-01; drop post-pilot data | Check for anticipation or pre-existing trend. |
| Log outcome | Y → log(1 + Y) | Address right-skewed count variance; multiplicative specification. |
| Post-COVID | Drop 2020-01 → 2021-12; keep true per-cohort onsets | Check whether COVID lockdown effects drive the headline. |
| MN-only controls | Restrict panel to Manhattan; two-cohort onsets within borough | Eliminate borough-level confounding at cost of a thin post-2024-11 control pool. |
| Phase-in guard | Truncate panel before 2025-06-01 | Pre-date the 2025–26 medium/large-building phase-ins that partially treat the never-treated pool. |

Each probe produces its own four-estimator result set in
`artifacts/placebo_did.json`, `log_outcome_did.json`,
`post_covid_did.json`, `manhattan_only_did.json`,
`phase_in_guard_did.json`.

## 4. Auxiliary analyses

### 4.1 Cross-sectional RDD

Sharp design with running variable = pre-period mean complaint rate,
cutoff = median rate. Not an identifying strategy; reported as
sensitivity. See `artifacts/rdd_density_sensitivity.json` for
conventional, bias-corrected, and robust estimates at three
bandwidths (h/2, h, 2h).

### 4.2 Moran's I + LISA

Computed on the per-CD post-minus-pre complaint change using an
inverse-distance weight matrix with 10 km cutoff. Community-district
centroids derived from the median latitude / longitude of service
requests attributed to each CD in the raw data. Permutation *p*-value
from 999 random permutations. LISA cluster labels ("HH", "LL", "HL",
"LH", "ns") follow the Anselin (1995) convention (Local indicators
of spatial association—LISA, *Geographical Analysis*, 27(2),
93–115).

## 5. Reporting conventions

All reported *p*-values are two-sided. Significance thresholds are
reported as raw *p* < .05 alongside Benjamini-Hochberg-corrected
*p*_BH < .05 across the 13 reported tests. Confidence intervals are
95% normal-theory from the engine's reported point estimate and
standard error.

Effect sizes for the DiD ATT are reported in natural units
(complaints per CD per month); a Cohen's *d*-style dimensionless
version can be recovered by dividing the ATT by the within-residual
SD (~17.7 complaints, see `artifacts/mde_analysis.json`).

## 6. Reproducibility

The full pipeline runs in <5 minutes on cache-hit; first run with
live Socrata fetch takes ~10–15 minutes. All artifacts are
deterministic (`np.random.seed(42)` fixed in every notebook that
uses RNG), and the committed `manuscripts/FINDINGS.md` +
`manuscripts/DIAGNOSTICS_CHECKLIST.md` regenerate byte-identically
under the stable-overrides pattern (see
`.claude/skills/committed-tearsheets.md`).
