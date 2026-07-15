**Table 1. Descriptive statistics, 2020-01 → 2026-06 panel.**

| Variable | Treated (9) | Control (65) | Total |
| --- | --- | --- | --- |
| Community districts | 9 | 65 | 74 |
| Months in window | 78 | 78 | 78 |
| CD-month observations | 702 | 5070 | 5,772 |
| Pre-treatment mean complaints/CD/month | 51.1 | 1.6 | — |
| Total Rodent complaints in window | — | — | 232,447 |

**Table 2. Four staggered-DiD estimators of the containerization effect (both cohorts).**

| Estimator | ATT | SE | p |
| --- | --- | --- | --- |
| TWFE | -10.26 | 1.76 | <.001 |
| CS | -4.77 | 2.22 | 0.032 |
| SA | -12.10 | 2.61 | <.001 |
| BJS | -11.93 | 0.65 | <.001 |

**Table 3. Robustness checks.**

| Check | ATT | p | Reading |
| --- | --- | --- | --- |
| Placebo t₀ = 2022-07-01 (BJS) | +9.97 | <.001 | SIGN FLIP vs. headline; p < .05. Picks up the pre-trend slope; see §4.5. |
| Log(1 + complaints) TWFE | +0.187 (+20.6%) | 0.119 | SIGN FLIP vs. headline; n.s.. Scale artifact; see §4.5. |
| Post-COVID (2022-01 →) (BJS) | -17.43 | <.001 | same sign as headline; p < .05. |
| Manhattan-only controls (BJS) | -20.20 | <.001 | same sign as headline; p < .05. Thin control pool after 2024-11; see §4.5. |
| Phase-in guard (window < 2025-06) | -8.84 | <.001 | same sign as headline; p < .05. Pre-dates the 2025–26 building phase-ins; see §5.3. |

**Table 4. RDD bandwidth sensitivity (cutoff = 35.1).**

| Bandwidth | h | ATT | SE | p |
| --- | --- | --- | --- | --- |
| h/2 | 6.72 | -0.01 | 5.09 | 0.998 |
| h | 13.45 | +1.02 | 3.50 | 0.770 |
| 2h | 26.89 | -2.06 | 3.00 | 0.493 |

**Table 5. Identification + statistical diagnostic checklist.**

| Diagnostic | Value | p | Reading |
| --- | --- | --- | --- |
| Parallel-trends F | F = 4.26 | <.001 | Reject flat pre-trends. |
| Breusch-Pagan | see §4.2 | <.001 | Heteroskedastic; cluster-robust SE. |
| TWFE R² | 0.799 | — | Within-panel variance absorbed. |
| MDE (α=.05, power=.80) | ~14.3 complaints (|d| ~ 0.81) | — | Exceeds observed |ATT|; see §5.3. |
| BH survivors | 10/13 | BH 0.05 | Main estimators surviving: TWFE, CS, SA, BJS. |
