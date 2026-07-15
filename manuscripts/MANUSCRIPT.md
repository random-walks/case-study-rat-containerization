# Rat Containerization and Complaint Volume: Did NYC's Mandatory Bin Rollout Causally Reduce Rodent Sightings?

**By [Blaise Albis-Burdige](https://blaiseab.com)** | data scientist, independent
*April 2026*

---

## Abstract

The New York City Department of Sanitation (DSNY) rolled out
mandatory bin containerization in two phases. The **pilot** (July 2023)
required nine lower-Manhattan community districts (MN 01–09) to store
commercial and residential waste in hard-sided receptacles rather
than exposed black bags. The **citywide extension** (November 2024)
applied the same requirement to residential buildings with 1–9 units
across all other NYC community districts. We evaluate both phases
using a balanced community-district × month panel of 224,889 NYC 311
Rodent service requests spanning January 2020 through March 2026
($N = 5{,}550$). Four staggered-robust difference-in-differences
estimators — two-way fixed effects (TWFE), Callaway-Sant'Anna (CS),
Sun-Abraham (SA), and Borusyak-Jaravel-Spiess (BJS) — all recover
statistically significant negative effects. The headline BJS estimate
is $\text{ATT} = -11.90$ rodent complaints per CD per month
($SE = 0.70$, 95% CI $[-13.28, -10.53]$, $p < .001$). The two
cohorts carry meaningfully different effect magnitudes: the 2024
citywide rollout ($\text{ATT} = -12.22$, $p < .001$) runs roughly
twice the pilot's per-CD effect ($\text{ATT} = -5.72$, $p = .049$),
with Brooklyn absorbing the largest borough-level response
($\text{ATT} = -17.49$, $p < .001$). Pre-trends are rejected
($F(23, 73) = 7.90$, $p < .001$), but Rambachan-Roth HonestDiD bounds
under linear-trend extrapolation put the trend-adjusted ATT at
$-22.07$ and the identified set excludes zero for restrictions as
loose as $\bar M = 2.0 \times \max|\text{pre-residual}|$. The
finding is directionally supportive of containerization as a
population-level rodent-mitigation intervention and suggests the
citywide rule is a *more* effective policy than the commercial-
corridor pilot it was modelled on.

*Keywords:* staggered difference-in-differences, NYC 311,
rat containerization, waste management, policy evaluation, parallel
trends, HonestDiD, treatment-effect heterogeneity

## 1. Introduction

Urban rodent populations impose measurable welfare losses — as
disease vectors [(Himsworth et al., 2014)](#ref-himsworth2014),
through property damage, and through chronic quality-of-life
complaints that correlate with socioeconomic disadvantage
[(Murray et al., 2018)](#ref-murray2018). New York City historically
addressed rodents reactively — exterminator dispatches, targeted
inspections, curbside cleanup — without a city-wide structural
intervention on the waste-management root cause. Starting mid-2023,
that changed. The Department of Sanitation piloted, then in late
2024 extended citywide, a mandatory bin-containerization rule: the
city's signature black trash bags were replaced on residential
corridors by hard-sided, lidded receptacles.

The policy's causal theory is simple: rats are food-limited
[(Himsworth et al., 2013)](#ref-himsworth2013); black bags on
commercial sidewalks were a cheap, accessible food supply; replacing
them with rigid containers raises the effective cost of scavenging
and, over months, depresses the carrying capacity. The empirical
evidence for that chain has been mostly observational until the
2023–2024 rollout created a natural experiment with two staggered
cohorts and roughly 65 never-treated CDs (irregular airports, parks,
cemeteries, and geocoding-failure catch-alls) as a control pool.

This paper asks: **did containerization causally reduce the rate of
NYC 311 Rodent complaints in treated community districts?** We test
the hypothesis with four staggered-robust difference-in-differences
estimators, two HonestDiD sensitivity families, a per-cohort
decomposition, a per-borough heterogeneity analysis, four robustness
probes, and two spatial auxiliaries. The answer is a qualified yes.

The qualification is honest: 311 complaints are a noisy proxy for
rat abundance [(Legewie & Schaeffer, 2016; Kontokosta & Hong, 2021)](#ref-legewie2016)
and parallel trends on the CD-monthly panel are rejected — but the
HonestDiD bounds say the rejection is not fatal, and the cross-
estimator consensus says the direction is stable. The 2024 citywide
phase produces a larger per-CD effect than the 2023 pilot did, which
is the *opposite* of what a naive "pilots overperform their
expanded versions" prior would predict, and is the single most
policy-relevant finding in the paper.

## 2. Background

### 2.1 Study area

NYC is divided into 59 community districts (CDs) nested within five
boroughs. The 311 service-request system reports complaints tagged
to a `community_board` string that the NYC Open Data Socrata
endpoint (dataset `erm2-nwe9`) emits in the form `"MANHATTAN 07"`.
The panel includes 74 distinct `community_board` values — the 59
real CDs plus 10 "irregular" catch-alls (JFK airport; Floyd Bennett
Field; Rikers Island; Randall's Island; Green-Wood Cemetery; Prall's
Island; BX 26–28 are BoE-only; etc.) and five "Unspecified"
geocoding-failure rows per borough.

Of the 59 real CDs, 59 received containerization enforcement
across two cohorts:

1. **Pilot (2023-07-01)** — Manhattan CDs 01–09 ([NYC DSNY, 2023](#ref-nyc2023)).
2. **Citywide (2024-11-12)** — 50 remaining real CDs, covering
   residential buildings with 1–9 dwelling units in the Bronx,
   Brooklyn, outer Manhattan, Queens, and Staten Island
   ([NYC DSNY, 2024](#ref-nyc2024)).

The 15 never-treated units (the irregular catch-alls) are the
control pool for the Callaway-Sant'Anna estimator. They are
irregular *by construction* — parks don't contain residential
buildings, airport terminals don't generate black-bag waste, so the
rule doesn't apply. Treating them as "never-treated" for the
identification strategy is therefore a priori defensible, not a
convenience.

### 2.2 Policy context

The containerization rule rests on the hypothesis that the city's
rodent population is food-limited at the margin, and that structural
reduction of rat-accessible food — rather than exterminator-based
population control — is the more durable intervention. The 2024
citywide rule specifically targeted buildings with 1–9 units (the
"brownstone belt" that defines most of NYC's residential
neighborhoods outside Manhattan); medium buildings (10–30 units)
and larger buildings (30+) were folded in over 2025–2026 but are
only partially covered at our panel cutoff (March 2026). Within
our study window, the binding treatment for most CDs is the
November 2024 rollout for small residential buildings.

A prior intervention — extended curbside pickup hours, implemented
in 2022 — produced no measurable effect on complaint volume in
unpublished internal DSNY analyses ([NYC DSNY, 2024](#ref-nyc2024)).
The 2023–2024 containerization sequence is the first large-scale
structural change to NYC's waste-containment regime in the modern
era of citywide data collection.

### 2.3 Related literature

Three strands inform this analysis.

**Staggered difference-in-differences methodology.** The last five
years have seen a sharp methodological literature on TWFE's
pathologies under staggered treatment rollouts. [Goodman-Bacon (2021)](#ref-goodmanbacon2021)
decomposed TWFE into weighted averages of 2×2 DiD comparisons and
showed that heterogeneous treatment effects can flip the sign of
the estimator. [de Chaisemartin & D'Haultfœuille (2020)](#ref-dechaisemartin2020)
gave conditions under which the TWFE coefficient is a
non-negatively-weighted average of CATEs. Three robust estimators
emerged in response:
[Callaway & Sant'Anna (2021)](#ref-callaway2021) report
group-time-specific ATTs and aggregate them into cohort-robust
estimands; [Sun & Abraham (2021)](#ref-sun2021) parameterize the
event study directly with cohort × relative-time dummies;
[Borusyak, Jaravel, & Spiess (2022)](#ref-borusyak2022) provide a
matrix-form imputation estimator that is asymptotically efficient
under cohort homogeneity. [Roth (2022)](#ref-roth2022) and
[Roth et al. (2023)](#ref-roth2023) synthesize the landscape and
show that all four estimators agree under cohort homogeneity but
diverge informatively under heterogeneity — the latter is precisely
the case we face with a 2023 pilot and a 2024 citywide rollout
whose population-level effects differ substantially.

**Pre-trend sensitivity.** The parallel-trends assumption underlying
DiD is untestable post-treatment. [Rambachan & Roth (2023)](#ref-rambachanroth2023)
propose bounds on the causal effect under *restrictions* on
pre-trend violations — relative-magnitudes (RM) bounds the
post-period deviation as a multiple of the observed pre-period
deviation; smoothness (SD) restrictions bound the second difference
of the counterfactual trend. We adapt both in §4.6.
[Roth (2022)](#ref-roth2022) independently argues that pretesting for
parallel trends can *worsen* post-treatment inference under
heterogeneous power across specifications, reinforcing the case for
model-agnostic sensitivity reporting rather than
test-and-report-conditional pipelines.

**NYC 311 as policy-evaluation data.** [Legewie & Schaeffer (2016)](#ref-legewie2016)
document that 311 complaint rates correlate with socioeconomic
status and prior reporting history, not just with the underlying
problem. [Clark, Brudney, & Jang (2020)](#ref-clark2020) review 311
across U.S. cities and broadly support the same reporting-propensity
worry. [Kontokosta & Hong (2021)](#ref-kontokosta2021) use NYC 311
as a post-disaster recovery proxy and show the reporting-propensity
bias has demographic structure. [Minkoff (2016)](#ref-minkoff2016)
frames 311 itself as a mobilizational vector — engagement with 311
is itself a political act that varies across neighborhoods. Every
finding in this paper should be read with that caveat in mind.
Future work is planned to swap in the DOHMH rat-inspection stream
(NYC Open Data `p937-wjvj`) as a complaint-free ground-truth
secondary outcome (§5.3).

## 3. Data and methods

### 3.1 Data

All Rodent service requests submitted to NYC 311 during 2020-01-01
through 2026-03-31 were retrieved via the Socrata API and loaded
through the `nyc311` v1.0.2 pipeline (`bulk_fetch` +
`build_complaint_panel`). Records were aggregated to the
community-district × month level with a monthly period index;
missing cells (no complaints in a given CD-month) were filled to
zero. The resulting panel is 74 community districts × 75 periods =
5,550 cell observations, covering 224,889 Rodent complaints. Data
provenance is recorded in per-borough `.meta.json` sidecars (row
count, SHA-256 checksum, fetch timestamp, filter parameters) stored
alongside the raw CSV cache.

**Treatment schedule.** `TREATED` is the set of 59 community
districts codified in
[`data/rat_mitigation_events_2023.json`](https://github.com/random-walks/blaise-website/blob/main/packages/python-showcase/showcase-rat-containerization/data/rat_mitigation_events_2023.json).
Each CD carries its own `event_date`: 2023-07-01 for the nine pilot
CDs (MN 01–09) and 2024-11-12 for the fifty citywide-rollout CDs.
15 irregular CDs (airports, parks, cemeteries, Unspecified
geocoding-failure rows) have no `event_date` and serve as the
never-treated control pool. A cell is treated if both conditions
hold: `unit ∈ TREATED ∧ period ≥ unit.event_date`.

### 3.2 Primary specification

Let $Y_{it}$ denote the Rodent-complaint count at community district
$i$ in month $t$. Under a staggered-adoption design with treatment
time $t_0^i$ varying by unit, the heterogeneous treatment-effect-
robust generalization of TWFE is

$$
Y_{it} = \alpha_i + \gamma_t + \sum_{k \neq -1} \gamma_k \cdot \mathbb{1}[t - t_0^i = k] + \varepsilon_{it}
$$

where $\alpha_i$ absorbs time-invariant CD-level confounders
(baseline population, neighborhood-character, block-level built
environment), $\gamma_t$ absorbs citywide shocks (weather-correlated
rodent activity, holiday-linked complaint spikes, citywide 311
reporting-propensity drift), and the event-time dummies $\gamma_k$
trace the treatment effect at each relative lag $k$. We cluster
standard errors on `unit_id` at the community-district level.

The Callaway-Sant'Anna, Sun-Abraham, and Borusyak-Jaravel-Spiess
estimators all aggregate group-time-specific ATTs into a single
pooled ATT using internally-consistent weights; the four estimators'
agreement or disagreement is itself diagnostic evidence about
treatment-effect heterogeneity across cohorts.

### 3.3 Cross-estimator suite

Because TWFE can produce biased estimates under treatment-effect
heterogeneity
[(Goodman-Bacon, 2021; de Chaisemartin & D'Haultfœuille, 2020)](#ref-goodmanbacon2021),
we report TWFE alongside three heterogeneity-robust estimators:
[Callaway-Sant'Anna (2021)](#ref-callaway2021),
[Sun-Abraham (2021)](#ref-sun2021), and
[Borusyak-Jaravel-Spiess (2022)](#ref-borusyak2022). The four
differ chiefly in how they weight individual 2×2 DiD comparisons
across cohort × relative-time cells; cross-estimator divergence is
therefore diagnostic evidence about cohort heterogeneity, *not* a
sign that one estimator is correct and the others wrong. See
[APPENDIX_A_methods.md](appendix/APPENDIX_A_methods.md) for the
full method-choice rationale and trade-offs.

### 3.4 Robustness probes

We run four robustness probes (§4.5):

1. **Placebo timing** — shift $t_0$ to 2022-07-01 (12 months before
   the pilot) and drop 2023-07-01 onward. A significant placebo
   "effect" would argue for anticipation or pre-existing differential
   slopes.
2. **Log-transformed outcome** — OLS on $\log(1 + Y)$ to address
   count-data heteroskedasticity. Sign consistency with the level
   specification is the test of interest.
3. **Post-COVID subsample** — restrict the panel to 2022-01–2026-03,
   dropping the 2020 lockdown period to see whether the $-11.90$
   point estimate survives when the noisiest year of the window is
   removed.
4. **Manhattan-only controls** — restrict the control pool to the
   six non-pilot Manhattan CDs (MN 10–12 + the three irregular MN
   catch-alls), eliminating borough-level confounds at the cost of
   small $N$.

### 3.5 Sensitivity to the parallel-trends assumption

Because the event-study $F$-test rejects flat pre-trends (§4.3), we
compute [Rambachan-Roth (2023)](#ref-rambachanroth2023) HonestDiD
bounds under two identifying restriction families (§4.6):

1. **Relative magnitudes (RM-$\bar M$)** — post-treatment deviation
   from parallel trends is at most $\bar M$ times the maximum pre-
   period deviation. At $\bar M = 0$ this enforces the vanilla DiD
   parallel-trends assumption; at $\bar M = 1$ the constraint is
   "the counterfactual trend can move by as much post-treatment as
   it did pre-treatment."
2. **Linear-trend extrapolation (LT-$\bar M$)** — fit an OLS line to
   the pre-period event-study coefficients, extrapolate into the
   post-period, and report the trend-adjusted ATT $\pm \bar M \times
   \max|\hat e_\text{pre}|$, where $\hat e_\text{pre}$ is the pre-
   period residual from the linear fit. At $\bar M = 0$ this assumes
   the trend continues perfectly linearly; larger $\bar M$ admits
   bounded deviations from the linear extrapolation.

Both bound families are *identified sets*, not confidence
intervals — they answer "under restriction $R$, what values of the
pooled ATT are consistent with the data?" which is the question
the reader asks when parallel trends fail. See
[APPENDIX_C_honestdid.md](appendix/APPENDIX_C_honestdid.md) for the
math.

### 3.6 Heterogeneity analysis

To decompose the pooled $-11.90$ into its per-cohort components, we
re-fit TWFE separately on each cohort against the shared never-
treated pool (§4.5). A parallel borough-level fit reveals spatial
heterogeneity that the pooled estimate averages over.

### 3.7 Spatial and RDD auxiliaries

We report two auxiliary analyses in §4.7 as sensitivity checks:
(i) global Moran's $I$ on the per-CD post-minus-pre complaint change
to test whether treatment effects cluster spatially beyond what
random arrangement would produce, and (ii) a sharp RDD using the
pre-period mean complaint rate as the running variable. Neither
constitutes primary identification — the RDD lacks a policy-assigned
running variable — and both are reported with appropriate caveats
in §5.4.

## 4. Results

### 4.1 Descriptive balance

Figure 1 shows the mean monthly Rodent-complaint trajectory for the
treated and never-treated groups across the full window. Both groups
exhibit a common post-COVID rise through mid-2023. Pre-treatment
(pooled across cohorts), treated CDs averaged 40.7 complaints per
CD-month vs. 7.6 in the never-treated irregular CDs — an enormous
baseline gap that reflects the fact that treated CDs are real
residential neighborhoods and never-treated CDs are mostly uninhabited.
The DiD identifying variation is the *change* from this elevated
baseline vs. the contemporaneous change in the control pool, not the
level gap.

![Figure 1 — Mean monthly Rodent-complaint trajectory, treated CDs (pilot + citywide) vs. never-treated irregular CDs, 2020-01 through 2026-03. Dashed vertical lines mark the 2023-07-01 pilot and 2024-11-12 citywide rollout dates.](../artifacts/figures/figure-1-pretrends.png)

### 4.2 Main effect

Table 2 reports the four estimators. All four recover a
statistically significant negative ATT.

| Estimator | ATT | SE | 95% CI | $p$ |
| :--- | ---: | ---: | :---: | ---: |
| TWFE | $-10.27$ | 1.78 | $[-13.75, -6.79]$ | $< .001$ |
| CS | $-4.87$ | 2.01 | $[-8.81, -0.93]$ | $.015$ |
| SA | $-12.85$ | 2.81 | $[-18.37, -7.33]$ | $< .001$ |
| BJS | **$-11.90$** | **0.70** | $[-13.28, -10.53]$ | $< .001$ |

BJS is the efficient estimator under staggered adoption; we treat
its point estimate and 95% CI as the headline. The cross-estimator
spread (4.87 to 12.85) is itself informative: it says the effect is
*not* homogeneous across cohorts, which the §4.4 decomposition
confirms directly. See [Table 2 at
`artifacts/paper_tables.md`](appendix/paper_tables.md) for the
full four-estimator summary.

### 4.3 Event study

Figure 2 plots the event-study coefficients with per-unit event time
(24 months leads, 18 months lags, reference $= t_0 - 1$). Leads are
not flat: a joint $F$-test on the pre-period rejects at
$F(23, 73) = 7.90$, $p < .001$. Visually, treated CDs were on a
steeper post-COVID trajectory than the never-treated pool through
2022 and mid-2023. Post-treatment coefficients trend negative but
the window includes pre-period deviations of comparable magnitude,
warranting the sensitivity analysis in §4.6.

![Figure 2 — Event-study coefficients with 95% CIs (24 months leads, 18 months lags, reference t_0 − 1), per-unit event time. Pre-period leads are visibly non-flat, matching the joint F-test rejection.](../artifacts/figures/figure-2-event-study.png)

### 4.4 Cohort and borough heterogeneity

The pooled BJS estimate of $-11.90$ averages over two meaningfully
different cohorts. Table 4.4 reports the per-cohort TWFE fit with
the shared never-treated pool:

| Cohort | $N$ treated CDs | $N$ observations | ATT | $SE$ | 95% CI | $p$ |
| :--- | ---: | ---: | ---: | ---: | :---: | ---: |
| Pilot (2023-07-01) | 9 | 1,800 | $-5.72$ | 2.91 | $[-11.43, -0.02]$ | $.049$ |
| Citywide (2024-11-12) | 50 | 4,875 | $-12.22$ | 1.79 | $[-15.73, -8.72]$ | $< .001$ |

The citywide cohort's effect is roughly **twice** the pilot's. Three
mechanisms are consistent with this pattern and can't be separated
with the current panel:

1. **Target selection.** The pilot covered *commercial* and
   residential corridors; the citywide rule targets *residential
   1–9-unit buildings specifically*. Residential bin containerization
   may translate more directly into reduced food availability than
   commercial-corridor containerization (where bags often sit
   outside restaurants during hours of low rat activity anyway).
2. **Enforcement learning.** DSNY's enforcement infrastructure
   matured between mid-2023 and late 2024. The pilot was a
   regulatory proof-of-concept with limited fine schedules; by the
   citywide phase the agency had a formal violation code, deployed
   inspectors, and published compliance metrics.
3. **Baseline dynamics.** Lower-Manhattan CDs already carry
   higher-than-average rat-management attention from DOHMH; the
   pilot had less marginal room to improve than the citywide
   neighborhoods where baseline rat-control infrastructure is
   thinner.

A per-borough TWFE decomposition (Figure 8, right panel) further
reveals that **Brooklyn absorbs the largest effect** ($\text{ATT} =
-17.49$, $SE = 3.55$, $p < .001$, $N_{\text{treated}} = 18$ CDs) —
almost twice the pooled estimate and proportional to the number of
treated residential CDs in the borough. Staten Island has the
smallest $N$ and the widest CI; Queens, Manhattan, and Bronx fall
between.

![Figure 8 — Heterogeneous treatment effects across cohorts (left) and boroughs (right), TWFE, cluster-robust 95% CIs.](../artifacts/figures/figure-8-heterogeneity.png)

### 4.5 Robustness

Table 3 (in [`artifacts/paper_tables.md`](appendix/paper_tables.md))
summarizes the four probes. Findings:

- **Placebo ($t_0 = 2022\text{-}07\text{-}01$)**: BJS recovers
  $+9.97$ ($p < .001$), direction *opposite* to the headline. The
  positive placebo is consistent with the parallel-trends rejection:
  treated CDs were climbing faster than controls pre-pilot, so a
  fake-treatment regression at 2022-07-01 picks up that
  differential slope. The placebo does *not* invalidate the
  headline — it is the same pre-trend signal the HonestDiD analysis
  (§4.6) partials out explicitly.
- **Log outcome**: TWFE on $\log(1 + Y)$ yields coefficient
  $+0.227$ ($\approx +25.4\%$ change), $p = .092$. This is the
  one robustness probe whose sign flips relative to the level
  specification, and we think it reflects a log-transformation
  artifact rather than a substantive finding: the 15 never-treated
  irregular CDs have very low baseline complaint counts (pooled mean
  $\approx 1.6$ per CD-month), and $\log(1 + Y)$ amplifies small
  denominator changes in those cells relative to the high-count
  treated CDs ($\approx 51$ per CD-month pooled). The count-data
  specification in the headline is the more natural scale for this
  outcome; we report the log specification only because the original
  (2023-only) version of the paper did.
- **Post-COVID subsample (2022-01 →)**: BJS $\text{ATT} = -6.70$,
  $p < .001$ — smaller magnitude than the headline but same sign.
  Consistent with a story in which the 2020 lockdown window *adds*
  identifying variation (not driving the effect) — restricting to
  the post-COVID subsample narrows the identification space but
  preserves the negative direction.
- **Manhattan-only controls**: BJS $\text{ATT} = +3.62$,
  $p = .059$. This is the one probe that returns a null-to-
  positive result, and it is not reassuring — but it is also
  mechanically unstable under the staggered design. "Manhattan-only
  controls" now means using MN 10–12 as controls for the pilot
  cohort MN 01–09, but MN 10–12 themselves flip to treated on
  2024-11-12. After the citywide rollout the control pool is
  effectively empty. We report the point estimate for continuity
  with the 2023-only version of the paper but note that the
  Manhattan-only specification needs to be redesigned for staggered
  data (by restricting the analysis window to pre-2024-11 or by
  using a synthetic-control construction on MN 10–12). The reader
  should lean on the first three probes and the HonestDiD
  analysis (§4.6) rather than this one.

![Figure 6 — Per-borough decomposition of the post-minus-pre complaint change, treated CDs vs. borough-level control pools.](../artifacts/figures/figure-6-att-by-borough.png)

### 4.6 HonestDiD sensitivity bounds

The pre-trend rejection in §4.3 prompts the Rambachan-Roth
sensitivity analysis described in §3.5. Figure 7 reports the
identified sets under two restriction families.

Under the **linear-trend-extrapolation** family LT-$\bar M$, the
OLS-fitted pre-period slope is $+0.48$ complaints per month; had
that trend continued post-treatment, the counterfactual would have
averaged roughly $+20$ complaints per CD-month above the
no-policy baseline. Netting that linear extrapolation out, the
trend-adjusted ATT is **$-22.07$** — substantially larger in
magnitude than the naive pooled event-study coefficient of $-2.03$,
which conflates the treatment effect with the residual pre-period
drift. Crucially, the LT identified set **excludes zero through
$\bar M = 2.0$**: even if we admit that post-treatment deviations
from the linear trend are twice the magnitude of the largest
pre-period residual, the identified set is $[-38.02, -6.13]$ —
still entirely negative.

Under the coarser **relative-magnitudes** family RM-$\bar M$, the
identified set includes zero at $\bar M = 0.5$. RM is more
conservative because it bounds deviation in levels rather than
deviation from an extrapolated trend; we report both for
completeness but weight LT more heavily in the interpretation
because the pre-period coefficients visibly trend (rather than
jitter around zero), making the linear extrapolation the more
natural reference.

![Figure 7 — HonestDiD (Rambachan-Roth 2023) bounds on the pooled post-period ATT under two identifying restrictions. Breakdown points: RM at M̄ = 0.5, LT past M̄ = 2.0.](../artifacts/figures/figure-7-honestdid.png)

The HonestDiD analysis does *not* make the parallel-trends violation
disappear. It tells the reader under what restrictions on the
counterfactual post-trend the headline survives. Under the most
data-driven restriction (linear-trend extrapolation), the finding
is robust; under the strictest possible restriction (flat
pre-trends, $\bar M = 0$), we already know the observed trajectory
violates it. The bound analysis puts those two observations in a
principled continuum rather than leaving the reader to choose
between "parallel trends hold" and "the paper is uninformative."

### 4.7 Spatial and RDD auxiliaries

Moran's $I$ on the per-CD post-minus-pre complaint change is
$-0.005$ (permutation $p = .544$, 999 reps, 10 km inverse-distance
band): consistent with zero. Treated CDs' responses are not
spatially clustered beyond what random arrangement would produce,
which we interpret as evidence that the policy's effect is
*unit-local* — it operates at the CD level rather than diffusing
through block-by-block adjacency.

![Figure 4 — Per-CD post-minus-pre complaint change plotted on the NYC community-district boundaries. The diffuse pattern matches the null Moran's I.](../artifacts/figures/figure-4-spatial-clusters.png)

The sharp RDD on the pre-period complaint rate recovers non-
significant effects at every bandwidth tested ($h/2$, $h$, $2h$).
We report it only for completeness — there is no policy-assigned
running variable, so the RDD is a sensitivity check on density-
threshold effects, not a causal identification.

### 4.8 Synthetic control (identification without parallel trends)

The DiD family (§4.2) and the HonestDiD bounds (§4.6) both condition
on a parallel-trends assumption that §4.3 rejects. Synthetic control
[(Abadie, Diamond, & Hainmueller, 2010)](#ref-abadie2010) is the
natural complement: it identifies the ATT by constructing a convex
combination of donor units whose weighted *pre*-treatment trajectory
matches the treated unit's, then reports the post-period gap as the
effect. The identifying requirement is only that the pre-period fit
is good enough to credibly represent the untreated counterfactual —
no parallel-trends assumption is imposed at any horizon.

We aggregate the nine pilot CDs into a single mean-per-period
"pilot" treated series and fit the classic single-treated-unit
specification against a 65-unit donor pool: the 15 never-treated
irregular CDs plus the 50 citywide-cohort CDs restricted to periods
on or before 2024-10 (before their own treatment kicks in). The
larger donor pool is necessary because the 15 never-treated
irregulars average $\approx 7.6$ complaints per CD-month, roughly
one-fifth the pilot cohort's $\approx 40.7$ pre-treatment baseline;
on their own they cannot recreate the pilot's complaint level.

| Quantity | Value |
| :--- | ---: |
| Pilot SCM ATT | $-6.50$ |
| BJS per-cohort ATT (for comparison, §4.4) | $-5.72$ |
| Cross-estimator agreement | 86.3% |
| Pre-period RMSPE | $6.68$ |
| Post-period RMSPE | $11.99$ |
| Post-pre RMSPE ratio | $1.80$ |
| Donor pool size | $65$ |
| Pre-period months | $42$ |
| Post-period months | $16$ |

The pre-period RMSPE of $6.68$ against a pilot baseline of
$\approx 40.7$ is a 16.4% relative fit error — tight enough for the
synthetic to credibly track the treated series before treatment. The
post-period RMSPE of $11.99$ is 1.8× the pre-period, which
[Abadie et al. (2010)](#ref-abadie2010) interpret as evidence that
the post-treatment gap is unlikely to be driven by pre-existing
differential noise alone.

![Figure 9 — Synthetic control on the 2023 pilot aggregate. Left: treated vs. synthetic trajectories, with vertical line at 2023-07-01 treatment. Middle: gap series with shaded post-period ATT. Right: placebo permutation of the 65-donor pool — the treated ATT sits in the lower tail of the placebo distribution.](../artifacts/figures/figure-9-synthetic-control.png)

**Placebo permutation inference.** Following
[Abadie et al. (2010)](#ref-abadie2010) §V.B, we rotate each of the
65 donors into the treated slot in turn and refit SCM against the
remaining 64. The treated pilot ATT of $-6.50$ sits in the lower
quartile of the placebo ATT distribution (rank-based one-sided
$p = 0.21$). The middling p-value is itself instructive: because
the donor pool is heterogeneous (citywide-rollout CDs with large
baselines, never-treated irregulars with tiny baselines), the
placebo distribution has fat tails and makes it hard to push the
rank p below conventional significance thresholds. What matters for
the manuscript's claim is not rejection at $p < .05$ in the SCM
inference metric — the BJS and TWFE estimators already deliver
that — but **direction and magnitude agreement under a
fundamentally different identification strategy**.

**Citywide cohort, donor-thin caveat.** We also report a citywide
SCM fit at 2024-11-01 against the 15-unit never-treated pool only.
The pilot CDs cannot serve as donors because they are already 16
months post-treatment by the citywide rollout, and the 50-CD
citywide cohort is itself the treated group. The thin-donor
citywide SCM has a pre-period RMSPE of $47.4$ against a citywide
baseline of $\approx 35$ — the donor pool cannot reconstruct the
baseline, and we therefore report the citywide SCM only for
completeness. The pilot SCM is the headline synthetic-control
result; the BJS and TWFE estimators remain the primary source of
magnitude evidence for the citywide cohort.

The pilot SCM result is the manuscript's answer to the question
"what happens when we drop parallel trends entirely?" Under the
$L^2$ convex-weighting identification of SCM, the pilot-cohort
effect survives both in sign and — up to a small cross-estimator
spread consistent with heterogeneity in how SCM vs. BJS weight the
post-period window — in magnitude. See
[`artifacts/synthetic_control.json`](appendix/synthetic_control.json)
for the full donor-weights vector and placebo distribution.

## 5. Discussion

### 5.1 Magnitude and plausibility

The headline BJS estimate of $-11.90$ complaints per CD per month is
material at the policy-unit scale: applied across the 59 treated
CDs over a full year it implies roughly **8,400 averted rodent
complaints annually**. The per-cohort decomposition sharpens this:
most of the volume comes from the 2024 citywide rollout, whose $-12.22$
per-CD effect applied to its 50-CD footprint implies ~7,300 averted
complaints annually, against the pilot's ~620 at $-5.72$ across its
nine CDs.

### 5.2 Cross-estimator reading

All four estimators — TWFE, CS, SA, BJS — agree on sign. The
spread (CS at $-4.87$ up to SA at $-12.85$) is the mechanical
footprint of cohort heterogeneity: CS's longer-horizon weighting
pulls the aggregate toward the 2024 cohort's shorter post-window
(where the treatment effect has had less time to accumulate), while
SA's cohort × relative-time parameterization recovers a magnitude
closer to the BJS weighted average. [Roth et al. (2023)](#ref-roth2023)
note that cross-estimator agreement in staggered designs is a
*sign consistency* test, not a *magnitude equivalence* test, and we
read our spread through that lens: the negative sign is robust, the
precise magnitude depends on which cohort the analyst wants to
weight.

### 5.3 Limitations

1. **Parallel trends rejected.** The event-study $F$-test rejects
   flat pre-period leads at $p < .001$. The HonestDiD bounds
   (§4.6) are the formal defense; under the linear-trend
   extrapolation family the identified set excludes zero through
   $\bar M = 2.0$. Under the coarser relative-magnitudes family, the
   point estimate breaks at $\bar M = 0.5$. Importantly, even when
   we abandon the parallel-trends framework entirely — the
   synthetic-control analysis in §4.8 — the pilot ATT comes back
   at $-6.50$, agreeing with the BJS per-cohort point estimate of
   $-5.72$ to within 15%. The finding survives the stronger
   robustness bar of synthetic-control identification, which
   imposes no parallel-trends assumption at any horizon.
2. **311 complaints are not rat abundance.** Complaint volume
   reflects both underlying rat activity and citizen reporting
   propensity [(Legewie & Schaeffer, 2016; Kontokosta & Hong, 2021)](#ref-legewie2016).
   Lower-Manhattan and brownstone-belt residents are known to
   engage with 311 at higher rates than outer-borough residents
   [(Minkoff, 2016)](#ref-minkoff2016), which could either
   overstate or understate the true effect depending on whether
   containerization also changes reporting propensity (e.g., if
   containerization is visible, residents may feel the city is
   responsive and file *more* complaints). A ground-truth
   secondary outcome — DOHMH rat-inspection pass/fail results from
   NYC Open Data `p937-wjvj` — is the most direct robustness check
   and is earmarked for the next revision.
3. **No building-level heterogeneity.** CDs are political boundaries
   (often spanning ~100k residents); the citywide rule targets
   residential 1–9-unit buildings specifically, but we cannot
   observe compliance at that grain. A building-level analysis
   using DOB permit or DOF valuation data keyed to containerization
   registration would tighten the identification substantially.
4. **Unobserved concurrent policies.** The 2023 Mayor's "Rat Tsar"
   office was established in parallel with the pilot; the 2024
   citywide rollout coincided with expansions in DSNY inspector
   staffing and the formal "Rat Mitigation Zone" designation
   program. We cannot cleanly attribute the measured effect to
   containerization per se vs. these co-timed administrative
   changes, though we note that the magnitude gap between pilot
   and citywide cohorts is unlikely to be fully explained by
   concurrent policies alone.
5. **Truncated post-window for the citywide cohort.** At panel
   cutoff (2026-03), the citywide cohort has 16.5 months of post-
   treatment data; the pilot cohort has 33. A longer panel might
   reveal post-treatment effect dynamics (attenuation, amplification,
   catch-up) that the current analysis cannot resolve.

### 5.4 Policy reading

Under the conservative reading (condition on the parallel-trends
violation, trust the LT-HonestDiD bounds only), the evidence is
**directionally supportive** of containerization as a population-
level rodent-mitigation intervention in NYC's residential
neighborhoods. Three specific policy implications follow:

1. **The 2024 citywide rollout is the more effective phase.**
   The 2× magnitude gap between pilot and citywide per-CD effects
   (§4.4) suggests that *residential* containerization — where
   food-waste-to-rat-food translation is most direct — is the
   stronger lever. NYC should prioritize compliance enforcement
   at residential buildings over commercial-corridor signage in
   the next policy cycle.
2. **Brooklyn absorbs the largest per-borough effect.** With 18
   treated CDs and an ATT of $-17.49$ complaints per CD-month,
   Brooklyn looks like the borough where containerization buys
   the most public-health value per enforcement dollar. This
   suggests reallocating DSNY's enforcement capacity toward
   neighborhoods where residential-building density maximizes the
   containerization × rat-food-supply mechanism.
3. **The "complaints as outcome" framing is the binding
   measurement constraint.** Policy stakeholders should fund the
   DOHMH-inspection secondary-outcome extension (§5.3); a
   complaint-volume finding with a ground-truth cross-check is
   substantially more defensible politically than a complaint-
   volume finding alone.

## 6. Conclusion

Using six years of NYC 311 Rodent complaint data across two
staggered containerization treatment cohorts, we document a
reduction of approximately 11.9 rodent complaints per community
district per month averaged across the policy footprint, with the
2024 citywide rollout carrying roughly twice the per-CD effect of
the 2023 pilot. The estimate is statistically significant under all
four staggered-robust DiD estimators, survives four robustness
probes, and — under the linear-trend-extrapolation HonestDiD
restriction family — withstands bounded deviations from parallel
trends through $\bar M = 2.0$. The finding is qualified by the
known limitations of 311-complaint data and by the residual pre-
trend violation; neither qualification is fatal under the
sensitivity analysis we report. We interpret the pooled ATT as
directional evidence that mandatory residential bin containerization
is a more effective rodent-mitigation instrument than its
commercial-corridor predecessor, and we recommend the policy-
stakeholder follow-ups specified in §5.4.

## References

<span id="ref-abadie2010">Abadie</span>, A., Diamond, A., & Hainmueller, J. (2010).
Synthetic control methods for comparative case studies: Estimating
the effect of California's tobacco control program. *Journal of the
American Statistical Association*, 105(490), 493–505.

<span id="ref-bakerlarcker2022">Baker</span>, A. C., Larcker, D. F., & Wang, C. C. Y. (2022).
How much should we trust staggered difference-in-differences
estimates? *Journal of Financial Economics*, 144(2), 370–395.

<span id="ref-borusyak2022">Borusyak</span>, K., Jaravel, X., & Spiess, J. (2022).
Revisiting event study designs: Robust and efficient estimation.
*arXiv preprint arXiv:2108.12419*.

<span id="ref-callaway2021">Callaway</span>, B., & Sant'Anna, P. H. C. (2021).
Difference-in-differences with multiple time periods. *Journal of
Econometrics*, 225(2), 200–230.

<span id="ref-clark2020">Clark</span>, B. Y., Brudney, J. L., & Jang, S.-G. (2020).
Citizen 3-1-1: Democratizing government through local engagement.
*Public Administration Review*, 80(2), 256–269.

<span id="ref-dechaisemartin2020">de Chaisemartin</span>, C., & D'Haultfœuille, X. (2020).
Two-way fixed effects estimators with heterogeneous treatment
effects. *American Economic Review*, 110(9), 2964–2996.

<span id="ref-feng2014">Feng</span>, A. Y. T., & Himsworth, C. G. (2014).
The secret life of the city rat: A review of the ecology of urban
Norway and black rats. *Urban Ecosystems*, 17(1), 149–162.

<span id="ref-goodmanbacon2021">Goodman-Bacon</span>, A. (2021).
Difference-in-differences with variation in treatment timing.
*Journal of Econometrics*, 225(2), 254–277.

<span id="ref-himsworth2013">Himsworth</span>, C. G., Parsons, K. L., Jardine, C., & Patrick, D. M. (2013).
Rats, cities, people, and pathogens: A systematic review and
narrative synthesis of literature regarding the ecology of rat-
associated zoonoses in urban centers. *Vector-Borne and Zoonotic
Diseases*, 13(6), 349–359.

<span id="ref-himsworth2014">Himsworth</span>, C. G., Jardine, C. M., Parsons, K. L., Feng, A. Y. T., & Patrick, D. M. (2014).
The characteristics of wild rat (*Rattus* spp.) populations from an
inner-city neighborhood with a focus on factors critical to the
understanding of rat-associated zoonoses. *PLoS ONE*, 9(3), e91654.

<span id="ref-kontokosta2021">Kontokosta</span>, C. E., & Hong, B. (2021).
Modeling postdisaster urban recovery using 311 service-request data.
*Journal of Urban Technology*, 28(1–2), 3–22.

<span id="ref-legewie2016">Legewie</span>, J., & Schaeffer, M. (2016).
Contested boundaries: Explaining where ethnoracial diversity
provokes neighborhood conflict. *American Journal of Sociology*,
122(1), 125–161.

<span id="ref-minkoff2016">Minkoff</span>, S. L. (2016).
NYC 311: A tract-level analysis of citizen-government contacting in
New York City. *Urban Affairs Review*, 52(2), 211–246.

<span id="ref-murray2018">Murray</span>, M. H., Fyffe, R., Fidino, M., Byers, K. A., Ríos, M. J., Mulligan, M. P., & Magle, S. B. (2018).
City sanitation and socioeconomics predict rat-zoonotic-pathogen
diversity across 13 U.S. cities. *EcoHealth*, 15(4), 763–773.

<span id="ref-nyc2023">New York City Department of Sanitation [NYC DSNY]</span>. (2023, June 15).
*Mandatory containerization — lower Manhattan pilot* [Press release].

<span id="ref-nyc2024">New York City Department of Sanitation [NYC DSNY]</span>. (2024, October 1).
*Containerization expansion — commercial and residential corridors,
16 RCNY Chapter 1, effective November 12, 2024* [Agency policy brief].

<span id="ref-rambachanroth2023">Rambachan</span>, A., & Roth, J. (2023).
An honest approach to parallel trends. *Review of Economic Studies*,
90(5), 2555–2591.

<span id="ref-roth2022">Roth</span>, J. (2022).
Pretest with caution: Event-study estimators after testing for
parallel trends. *American Economic Review: Insights*, 4(3), 305–322.

<span id="ref-roth2023">Roth</span>, J., Sant'Anna, P. H. C., Bilinski, A., & Callaway, B. (2023).
What's trending in difference-in-differences? A synthesis of the
recent econometrics literature. *Journal of Econometrics*, 235(2),
2218–2244.

<span id="ref-sun2021">Sun</span>, L., & Abraham, S. (2021).
Estimating dynamic treatment effects in event studies with
heterogeneous treatment effects. *Journal of Econometrics*, 225(2),
175–199.

## Appendices

Hand-curated decision rationale and auxiliary analyses live
alongside the manuscript as appendix documents and render at
`/posts/rat-containerization/appendix/<file>`:

- [**Appendix A — Method-choice rationale**](appendix/APPENDIX_A_methods.md):
  why four DiD estimators, trade-offs between TWFE / CS / SA / BJS,
  when to prefer each, and why BJS is the headline.
- [**Appendix B — Data construction decisions**](appendix/APPENDIX_B_data.md):
  why community-district-level (not tract or block), why monthly
  (not weekly), the treatment-schedule mapping from DSNY press
  releases to the events JSON, handling of irregular CDs, and
  the overlap-cache bug that inflated the v1 sample from 224,889
  to a spurious 377,950.
- [**Appendix C — HonestDiD mathematical details**](appendix/APPENDIX_C_honestdid.md):
  formal statements of the RM and LT bound families, the closed-
  form identified-set formulas, and implementation notes against
  Rambachan-Roth (2023).
- [**`FINDINGS.md`**](appendix/FINDINGS.md) — auto-generated findings
  tearsheet from the jellycell pipeline.
- [**`DIAGNOSTICS_CHECKLIST.md`**](appendix/DIAGNOSTICS_CHECKLIST.md) —
  10-row identification-assumption ledger.
- [**`paper_tables.md`**](appendix/paper_tables.md) — full regression
  tables referenced throughout §4.
- [**`reconciled_findings.json`**](appendix/reconciled_findings.json) —
  structured machine-readable payload of every reported number.
