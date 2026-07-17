# 12 — Heterogeneous treatment effects

> **Tearsheet** for [`notebooks/12_heterogeneous_effects.py`](../../notebooks/12_heterogeneous_effects.py) · [HTML report](../../site/12_heterogeneous_effects.html) · last run `2026-07-15T18:31:15+00:00`

Staggered DiD's headline (§3.3) pools across both the 2023 pilot
(MN 01–09, $N = 9$) and the 2024 citywide rollout (all other
standard CDs, $N = 50$). The pooled ATT of $-11.90$ masks the
per-cohort effects. This notebook decomposes it by re-fitting
TWFE and BJS separately on each cohort against the 15 never-
treated control CDs.

Why this matters for policy: the pilot CDs are in lower Manhattan
(high population density, high commercial share, professional
collection infrastructure); the citywide cohort includes outer-
borough residential neighborhoods with different baseline rat
ecology, different waste-generation profiles, and different DSNY
enforcement capacity. A pooled estimate has to average those two
very different treatment contexts into one number; the per-cohort
breakdown tells a city planner which type of neighborhood the
policy moves the needle in.

We also split the pooled effect by **borough** (Manhattan, Bronx,
Brooklyn, Queens, Staten Island) so the reader can see the spatial
distribution of the response.

**Per-cohort TWFE decomposition of the pooled staggered-DiD ATT. Pilot and citywide-rollout cohorts fit separately against the never-treated control pool.**

| field | value |
| --- | --- |
| `by_cohort.pilot_2023.label` | Pilot (2023-07-01) |
| `by_cohort.pilot_2023.n_treated_units` | `9` |
| `by_cohort.pilot_2023.n_control_units` | `15` |
| `by_cohort.pilot_2023.n_observations` | `1872` |
| `by_cohort.pilot_2023.att` | `-6.596` |
| `by_cohort.pilot_2023.se` | `2.965` |
| `by_cohort.pilot_2023.p_value` | `0.02612` |
| `by_cohort.pilot_2023.ci_95_low` | `-12.41` |
| `by_cohort.pilot_2023.ci_95_high` | `-0.7841` |
| `by_cohort.pilot_2023.r_squared` | `0.8892` |
| `by_cohort.citywide_2024.label` | Citywide (2024-11-12) |
| `by_cohort.citywide_2024.n_treated_units` | `50` |
| `by_cohort.citywide_2024.n_control_units` | `15` |
| `by_cohort.citywide_2024.n_observations` | `5070` |
| `by_cohort.citywide_2024.att` | `-12.01` |
| `by_cohort.citywide_2024.se` | `1.693` |
| `by_cohort.citywide_2024.p_value` | `1.292e-12` |
| `by_cohort.citywide_2024.ci_95_low` | `-15.33` |
| `by_cohort.citywide_2024.ci_95_high` | `-8.695` |
| `by_cohort.citywide_2024.r_squared` | `0.7912` |


**Borough-stratified TWFE treatment effects. Each row fits only that borough's treated CDs against the shared never-treated pool, so differences reflect borough-specific response heterogeneity (baseline rat ecology, waste-gen mix, DSNY enforcement capacity), not control-pool differences.**

| field | value |
| --- | --- |
| `by_borough.Manhattan.borough` | Manhattan |
| `by_borough.Manhattan.n_treated_units` | `12` |
| `by_borough.Manhattan.n_control_units` | `15` |
| `by_borough.Manhattan.n_observations` | `2106` |
| `by_borough.Manhattan.att` | `-12.46` |
| `by_borough.Manhattan.se` | `4.31` |
| `by_borough.Manhattan.p_value` | `0.003847` |
| `by_borough.Manhattan.ci_95_low` | `-20.91` |
| `by_borough.Manhattan.ci_95_high` | `-4.01` |
| `by_borough.Bronx.borough` | Bronx |
| `by_borough.Bronx.n_treated_units` | `12` |
| `by_borough.Bronx.n_control_units` | `15` |
| `by_borough.Bronx.n_observations` | `2106` |
| `by_borough.Bronx.att` | `-9.862` |
| `by_borough.Bronx.se` | `3.099` |
| `by_borough.Bronx.p_value` | `0.001461` |
| `by_borough.Bronx.ci_95_low` | `-15.94` |
| `by_borough.Bronx.ci_95_high` | `-3.788` |
| `by_borough.Brooklyn.borough` | Brooklyn |
| `by_borough.Brooklyn.n_treated_units` | `18` |
| `by_borough.Brooklyn.n_control_units` | `15` |
| `by_borough.Brooklyn.n_observations` | `2574` |
| `by_borough.Brooklyn.att` | `-16.91` |
| `by_borough.Brooklyn.se` | `3.405` |
| `by_borough.Brooklyn.p_value` | `6.838e-07` |
| `by_borough.Brooklyn.ci_95_low` | `-23.59` |
| `by_borough.Brooklyn.ci_95_high` | `-10.24` |
| `by_borough.Queens.borough` | Queens |
| `by_borough.Queens.n_treated_units` | `14` |
| `by_borough.Queens.n_control_units` | `15` |
| `by_borough.Queens.n_observations` | `2262` |
| `by_borough.Queens.att` | `-7.317` |
| `by_borough.Queens.se` | `1.701` |
| `by_borough.Queens.p_value` | `1.698e-05` |
| `by_borough.Queens.ci_95_low` | `-10.65` |
| `by_borough.Queens.ci_95_high` | `-3.983` |
| `by_borough.Staten Island.borough` | Staten Island |
| `by_borough.Staten Island.n_treated_units` | `3` |
| `by_borough.Staten Island.n_control_units` | `15` |
| `by_borough.Staten Island.n_observations` | `1404` |
| `by_borough.Staten Island.att` | `-6.165` |
| `by_borough.Staten Island.se` | `2.291` |
| `by_borough.Staten Island.p_value` | `0.007127` |
| `by_borough.Staten Island.ci_95_low` | `-10.66` |
| `by_borough.Staten Island.ci_95_high` | `-1.675` |


![fig8_heterogeneity](../../artifacts/figures/figure-8-heterogeneity.png)

**Figure 8. Treatment-effect heterogeneity across cohorts (left) and across boroughs (right). The pooled ATT masks meaningfully different cohort-level effects — see §4.5 for the policy implication.**

| field | value |
| --- | --- |
| `path` | artifacts/figures/figure-8-heterogeneity.png |


**Next:** `13_dohmh_rat_inspections.py` (scaffold) — secondary-outcome
robustness using DOHMH inspection pass/fail data.

---

*Auto-generated by `jellycell export tearsheet notebooks/12_heterogeneous_effects.py`. Regenerating overwrites this file — for hand-authored writeups put a `.md` at the root of `manuscripts/` instead of under `tearsheets/`.*
