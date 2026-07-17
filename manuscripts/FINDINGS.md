# Findings — case-study-rat-containerization

*July 2026 · v4.0.0*

Auto-generated from `artifacts/reconciled_findings.json`. Regenerations are byte-identical when the underlying numbers do not change; edits to this file are overwritten on next run. See `MANUSCRIPT.md` for the hand-authored narrative.

## Headline

**BJS staggered DiD ATT = -11.93** Rodent complaints per community district per month (*SE* = 0.65, 95% CI [-13.19, -10.66], *p* &lt; .001, *N* = 5,772).

BJS staggered-DiD: across both cohorts (2023 pilot + 2024 citywide rollout), treated community districts experienced a reduction of 11.9 rodent complaints per CD per month post-treatment (95% CI [-13.2, -10.7]).

## Panel

- **Geography**: community district (NYC), *N* = 74 units.
- **Period**: 2020-01 → 2026-06, monthly frequency (*N* = 78 periods).
- **Observations**: 5,772 CD-month cells.
- **Total rodent complaints in window**: 232,447.
- **Cohort 1 (pilot, 2023-07-01)**: 9 treated CDs — MANHATTAN 01, MANHATTAN 02, MANHATTAN 03, MANHATTAN 04, MANHATTAN 05, MANHATTAN 06, MANHATTAN 07, MANHATTAN 08, MANHATTAN 09.
- **Cohort 2 (citywide rollout, 2024-11-12)**: 50 treated CDs across the remaining boroughs.
- **Never-treated controls**: 15 irregular districts (airports, parks, cemeteries, geocoding-failure catch-alls).

## Cross-estimator agreement

| Estimator | ATT | SE | *p* |
| :--- | ---: | ---: | ---: |
| TWFE | -10.26 | 1.76 | &lt; .001 |
| CS | -4.77 | 2.22 | 0.032 |
| SA | -12.10 | 2.61 | &lt; .001 |
| BJS | -11.93 | 0.65 | &lt; .001 |

All four estimators agree in sign. With staggered adoption (two cohorts), TWFE and BJS no longer coincide mechanically — the spread between TWFE (the naive panel fixed-effects estimate) and the heterogeneity-robust triple (CS, SA, BJS) is itself evidence of treatment-effect heterogeneity between the pilot and the citywide cohort.

## Robustness

| Check | ATT / coef | *p* | Reading |
| :--- | ---: | ---: | :--- |
| Placebo t₀ = 2022-07-01 (BJS) | +9.97 | &lt; .001 | Direction of the placebo tells us whether unobserved pre-trends would produce a spurious effect. |
| Log-outcome TWFE | +0.187 (+20.6%) | 0.119 | Multiplicative specification — see §4.5 for the scale-artifact discussion; read sign against the table value, not this caption. |
| Post-COVID sample (2022-01 →) | -17.43 | &lt; .001 | Isolates the policy window from 2020 lockdown variance. |
| Manhattan-only controls (BJS) | -20.20 | &lt; .001 | Manhattan-only slice with per-cohort onsets; thin control pool after 2024-11 — see §4.5. |
| Phase-in guard (window < 2025-06) | -8.84 | &lt; .001 | Truncates before the 2025–26 medium/large-building phase-ins that partially treat the control pool. |

## Diagnostics

| Diagnostic | Value | Reading |
| :--- | ---: | :--- |
| Parallel-trends joint *F* | *F* = 4.26, *p* &lt; .001 | **Reject** flat pre-trends — see HonestDiD sensitivity in §4.6 and Appendix C. |
| Breusch-Pagan | *p* &lt; .001 | Heteroskedastic residuals; cluster-robust SEs mitigate. |
| TWFE *R*² | 0.799 | Within-panel variance absorbed by fixed effects. |
| Shapiro-Wilk | sampled *p* &lt; .001 | Non-normal residuals — count-data feature; large-*N* CLT applies. |

## Balance (pre-treatment)

Pre-period mean monthly complaints: 51.1 (treated pooled across both cohorts) vs. 1.6 (never-treated controls). Welch *t* = 65.52, *p* &lt; .001, Cohen's *d* = 1.89. Treated community districts carry higher pre-period complaint rates; the staggered-DiD identifying variation is the change from this elevated baseline vs. the contemporaneous change in the never-treated pool.

---
Author: [Blaise Albis-Burdige](https://blaiseab.com). Stable-override
`generated_at="stable"` and
`hostname="showcase-runner"` per `.claude/skills/committed-tearsheets.md`.
