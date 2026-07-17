# Appendix A — Method-choice rationale

Why four difference-in-differences estimators, what each buys,
what each cannot see, and why BJS sits at the top of the
headline column.

## Why four estimators at all

Under homogeneous treatment effects and a single-cohort design,
all four of our estimators (TWFE, CS, SA, BJS) converge to the same
number. A staggered rollout with heterogeneous effects — which is
what NYC's containerization policy actually delivered — drives a
wedge between them. The four estimators therefore function as an
internal consistency check: sign agreement across the four is
evidence that the direction of the effect is robust to
methodological choice; disagreement in magnitude is evidence of
treatment-effect heterogeneity that the analyst should decompose
rather than average.

[Roth, Sant'Anna, Bilinski & Callaway (2023)](../../MANUSCRIPT.md#ref-roth2023)
synthesize the post-2020 DiD methodological literature and
recommend reporting multiple heterogeneity-robust estimators for
exactly this reason. [Baker, Larcker & Wang (2022)](../../MANUSCRIPT.md#ref-baker2022)
survey empirical finance applications and find that TWFE
estimates can be sign-flipped relative to the heterogeneity-robust
triple in up to 25% of published staggered-DiD papers; reporting
the triple alongside TWFE is the cheapest defense against that
failure mode.

## Estimator-by-estimator

### 1. Two-way fixed effects (TWFE)

The canonical DiD specification:

$$
Y_{it} = \alpha_i + \gamma_t + \beta \cdot D_{it} + \varepsilon_{it}
$$

where $D_{it} = 1$ if unit $i$ is treated at time $t$. Under
treatment-effect heterogeneity with staggered adoption,
[Goodman-Bacon (2021)](../../MANUSCRIPT.md#ref-goodmanbacon2021)
shows that $\hat\beta$ is a *weighted average* of 2×2 DiD
comparisons, and the weights can be negative when already-treated
units serve as controls for later-treated units with different
ATTs. In pathological cases the estimator can flip sign.

**Role in this paper**: baseline specification + cross-check. If
TWFE and the heterogeneity-robust estimators agree on sign, the
pathology is not binding; if they disagree we trust the robust
triple.

### 2. Callaway-Sant'Anna (CS)

Proposed by [Callaway & Sant'Anna (2021)](../../MANUSCRIPT.md#ref-callaway2021).
Estimates group-time ATT(g,t) — a separate average treatment effect
for each treatment cohort at each relative-time post-treatment —
and aggregates them with user-chosen weights ("simple" = equal
weights; "event study" = weight by relative time). CS can use
"not-yet-treated" units as controls for each cohort, which is why
we pass `control_group="not_yet_treated"` in notebook 03 and
construct the 15-unit never-treated pool as a fallback.

**Role**: the *conservative* heterogeneity-robust estimator. CS's
simple aggregation pulls toward later-cohort / short-horizon ATTs,
which in our panel means it down-weights the pilot (long post-
window, larger effect accumulates) relative to the citywide cohort
(short post-window, effect still building). This is why CS's point
estimate ($-4.77$) is the smallest in magnitude.

### 3. Sun-Abraham (SA)

Proposed by [Sun & Abraham (2021)](../../MANUSCRIPT.md#ref-sun2021).
Parameterizes the event study directly with cohort × relative-time
interaction dummies — effectively a fully-saturated event study
that lets each cohort's pattern of leads and lags differ. The
aggregate ATT is a weighted sum of cohort-specific coefficients
using sample-size weights.

**Role**: the *event-study-native* heterogeneity-robust estimator.
SA is the closest methodological cousin of our figure-2 event study
plot. Its point estimate ($-12.10$) is on the larger-magnitude side
of the range because the sample-weighted aggregation gives the
pilot cohort (9 CDs × 33 post-months) substantial weight despite
its smaller individual effect.

### 4. Borusyak-Jaravel-Spiess (BJS)

Proposed by [Borusyak, Jaravel & Spiess (2022)](../../MANUSCRIPT.md#ref-borusyak2022).
A matrix-imputation estimator: fit the TWFE model on never-treated
and not-yet-treated observations only, use it to impute
counterfactual outcomes for treated observations, and report the
average imputation residual as the ATT. Asymptotically efficient
under cohort homogeneity; still unbiased under heterogeneity.

**Role**: the *efficient* heterogeneity-robust estimator, and our
headline. BJS's standard error ($0.65$) is ~3.4× tighter than CS's
($2.22$) and ~4× tighter than SA's ($2.61$) in our panel, which is
why we quote BJS's $[-13.19, -10.66]$ CI as the leading number. The
efficiency gain comes from pooling the never-treated and
not-yet-treated counterfactual information rather than using only
never-treated.

## How the cross-estimator spread should be read

Under cohort homogeneity the four estimators coincide (up to
efficiency); our observed spread — CS at $-4.77$, TWFE at $-10.26$,
BJS at $-11.93$, SA at $-12.10$ — therefore **is** the empirical
signature of cohort heterogeneity. The §4.4 per-cohort
decomposition isolates the source: pilot ATT is $-6.60$, citywide
ATT is $-12.01$, and the four pooled estimators weight those two
cohorts differently. CS pulls toward the citywide cohort's earlier
post-window (smaller accumulated effect); BJS and SA pull toward
the treated-units-weighted average; TWFE pulls somewhere in the
middle because its Goodman-Bacon decomposition contains a mix.

The headline should be read as "the pooled effect is approximately
$-12$, the heterogeneity between cohorts is real, and the policy
stakeholder should consume §4.4 alongside the headline rather than
stop at the abstract." A single-number summary is a genuine
disservice to the user of this research.

## Why the headline is BJS, not TWFE

Four criteria drove the choice:

1. **Efficiency** — BJS has by far the smallest standard error in
   our panel ($SE = 0.65$), which translates into the tightest
   confidence interval for the pooled ATT.
2. **Cohort robustness** — BJS is unbiased under treatment-effect
   heterogeneity, unlike TWFE.
3. **Interpretability** — the BJS point estimate is an
   imputation-based counterfactual residual, which maps directly
   onto the layman reading "how many complaints would have happened
   without the policy."
4. **Convention** — recent applied DiD papers in the
   post-[Goodman-Bacon (2021)](../../MANUSCRIPT.md#ref-goodmanbacon2021)
   era increasingly report BJS as the primary estimate with the
   other three as robustness [(Baker et al., 2022)](../../MANUSCRIPT.md#ref-baker2022).

We note TWFE and CS as robustness checks in the main body and
report SA in the cross-estimator table but do not lead with any
of them.

## Clustered inference

All four estimators use cluster-robust standard errors clustered
on `unit_id` (community district). The cluster choice is driven by
the panel's autocorrelation structure: observations within a
community district across months are highly correlated (persistent
rat-ecology, persistent DSNY enforcement capacity, persistent
reporting propensity). Clustering on the treated unit is the
standard prescription (Abadie, Athey, Imbens & Wooldridge, 2017).
The 74 clusters in our panel comfortably exceed the rule-of-thumb
40-cluster minimum for cluster-robust asymptotics to be well-
behaved.
