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
dropped. This produces a rectangular 74 × 60 panel with 4,440 cells,
which the `factor_factory.tidy.Panel.to_factor_factory_panel`
adapter casts into the canonical `factor_factory.tidy.Panel`
contract for consumption by the DiD engines.

### 1.3 Treatment specification

Treatment is a single-cohort staggered-DiD design: all nine treated
community districts (MN 01–09) flip from 0 to 1 on 2023-07-01 and
remain treated for the duration of the post-period. The treatment
event file is `data/rat_mitigation_events_2023.json`, hand-curated
from DSNY press releases dated 2023-06-15, 2024-02-20, and 2024-06-12.

## 2. Identification

### 2.1 DiD specification

    Y_it = α_i + γ_t + β · (TREATED_i × Post_t) + ε_it

- α_i: CD fixed effects (74 dummies)
- γ_t: period fixed effects (60 dummies)
- TREATED_i × Post_t: the interaction whose coefficient β is the ATT
- SE: cluster-robust at `unit_id` (community district)

### 2.2 Why four estimators

TWFE is known to produce biased point estimates in staggered-adoption
settings when treatment effects are heterogeneous across cohorts or
time (Goodman-Bacon, 2021; de Chaisemartin & D'Haultfœuille, 2020).
Our design has a single cohort, which rescues TWFE from the
"contamination" problem in most settings — but we report all four
heterogeneity-robust estimators (CS, SA, BJS) regardless, so readers
can form their own interpretation.

Expected behavior under single-cohort adoption with homogeneous
ATT:
- TWFE ≈ BJS (both use full panel; BJS has tighter SE via imputation).
- CS and SA use different weighting schemes but recover the same point
  estimate in the one-cohort case.
- Sign disagreement across the four would indicate model
  misspecification or violations of common-trend assumptions.

### 2.3 Cluster-robust inference

All four estimators use cluster-robust standard errors at the
community-district level. This allows within-CD serial correlation
across months without bias in the SE, but assumes independence
across CDs. Spatial proximity could plausibly violate this
assumption (adjacent CDs might share shocks); however, Moran's *I*
on the residuals is near zero (§4.5 of MANUSCRIPT.md), which makes
the single-level cluster adequate.

### 2.4 Parallel-trends check

The event study in §4.3 of MANUSCRIPT.md rejects flat pre-period
leads at *F*(23, 73) = 7.90, *p* < .001. This is the identification
concern; the magnitude of the treatment effect should be interpreted
as an upper bound (see §5.3 limitation 1).

## 3. Robustness strategy

Four probes, each changing a single specification choice:

| Probe | Changes | Rationale |
| :--- | :--- | :--- |
| Placebo t₀ | 2023-07-01 → 2022-07-01; drop post-pilot data | Check for anticipation or pre-existing trend. |
| Log outcome | Y → log(1 + Y) | Address right-skewed count variance; multiplicative specification. |
| Post-COVID | Drop 2020-01 → 2021-12 | Check whether COVID lockdown effects drive the headline. |
| MN-only controls | Control pool → 6 non-pilot MN CDs | Eliminate borough-level confounding at cost of N. |

Each probe produces its own four-estimator result set in
`artifacts/placebo_did.json`, `log_outcome_did.json`,
`post_covid_did.json`, `manhattan_only_did.json`.

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
"LH", "ns") follow the Anselin (1995) convention.

## 5. Reporting conventions

All reported *p*-values are two-sided. Significance thresholds are
reported as raw *p* < .05 alongside Benjamini-Hochberg-corrected
*p*_BH < .05 across the 13 reported tests. Confidence intervals are
95% normal-theory from the engine's reported point estimate and
standard error.

Effect sizes for the DiD ATT are reported in natural units
(complaints per CD per month); a Cohen's *d*-style dimensionless
version can be recovered by dividing the ATT by the within-residual
SD (~35 complaints, see `artifacts/mde_analysis.json`).

## 6. Reproducibility

The full pipeline runs in <5 minutes on cache-hit; first run with
live Socrata fetch takes ~10–15 minutes. All artifacts are
deterministic (`np.random.seed(42)` fixed in every notebook that
uses RNG), and the committed `manuscripts/FINDINGS.md` +
`manuscripts/DIAGNOSTICS_CHECKLIST.md` regenerate byte-identically
under the stable-overrides pattern (see
`.claude/skills/committed-tearsheets.md`).
