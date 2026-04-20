# Findings — showcase-rat-containerization

*April 2026 · v2.0.0*

Auto-generated from `artifacts/reconciled_findings.json`. Regenerations are byte-identical when the underlying numbers do not change; edits to this file are overwritten on next run. See `MANUSCRIPT.md` for the hand-authored narrative.

## Headline

**BJS DiD ATT = -15.29** Rodent complaints per community district per month (*SE* = 2.35, 95% CI [-19.90, -10.69], *p* &lt; .001, *N* = 4,440).

BJS DiD: treated CDs experienced a reduction of 15.3 rodent complaints per community district per month post-2023-07-01 (95% CI [-19.9, -10.7]).

## Panel

- **Geography**: community district (NYC), *N* = 74 units.
- **Period**: 2020-01 → 2024-12, monthly frequency (*N* = 60 periods).
- **Observations**: 4,440 CD-month cells.
- **Total rodent complaints in window**: 377,950.
- **Treatment**: mandatory bin containerization pilot, effective 2023-07-01.
- **Treated units** (9): MANHATTAN 01, MANHATTAN 02, MANHATTAN 03, MANHATTAN 04, MANHATTAN 05, MANHATTAN 06, MANHATTAN 07, MANHATTAN 08, MANHATTAN 09.

## Cross-estimator agreement

| Estimator | ATT | SE | *p* |
| :--- | ---: | ---: | ---: |
| TWFE | -15.29 | 7.37 | 0.038 |
| CS | -12.20 | 6.98 | 0.080 |
| SA | -12.20 | 3.61 | &lt; .001 |
| BJS | -15.29 | 2.35 | &lt; .001 |

All four estimators agree in sign. TWFE and BJS are numerically equivalent here because adoption is a single cohort; CS and SA coincide for the same reason.

## Robustness

| Check | ATT / coef | *p* | Reading |
| :--- | ---: | ---: | :--- |
| Placebo t₀ = 2022-07-01 (BJS) | +10.64 | 0.001 | Non-significant placebo (rejection would argue anticipation or pre-existing trend). |
| Log-outcome TWFE | -0.072 (-6.9%) | 0.326 | Multiplicative specification: direction consistent, magnitude smaller. |
| Post-COVID sample (2022-01 →) | -23.04 | &lt; .001 | Strengthens headline; COVID lockdowns are not driving the effect. |
| Manhattan-only controls (BJS) | -44.35 | &lt; .001 | Same sign; wide CIs due to small control set (6 CDs). |

## Diagnostics

| Diagnostic | Value | Reading |
| :--- | ---: | :--- |
| Parallel-trends joint *F* | *F* = 7.90, *p* &lt; .001 | **Reject** flat pre-trends (see §5.3). |
| Breusch-Pagan | *p* &lt; .001 | Heteroskedastic residuals. |
| TWFE *R*² | 0.812 | Within-panel variance largely absorbed by fixed effects. |
| Shapiro-Wilk | sampled *p* &lt; .001 | Non-normal residuals — count-data feature. |

## Balance (pre-treatment)

Pre-period (2020-01 → 2023-06) mean monthly complaints: 108.6 (treated) vs. 78.5 (control). Welch *t* = 6.75, *p* &lt; .001, Cohen's *d* = 0.38 (small-to-medium). Treated community districts carried higher pre-period complaint rates; the DiD identifying variation is the change from this elevated baseline.

---
Author: [Blaise Albis-Burdige](https://blaiseab.com). Stable-override
`generated_at="stable"` and
`hostname="showcase-runner"` per `.claude/skills/committed-tearsheets.md`.
