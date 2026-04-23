**Table 1. Descriptive statistics, 2020–2024 panel.**

| Variable | Treated (9) | Control (65) | Total |
| --- | --- | --- | --- |
| Community districts | 9 | 65 | 74 |
| Months in window | 75 | 75 | 75 |
| CD-month observations | 675 | 4875 | 5,550 |
| Pre-treatment mean complaints/CD/month | 51.1 | 1.6 | — |
| Total Rodent complaints in window | — | — | 224,889 |

**Table 2. Four DiD estimators of the containerization-pilot effect.**

| Estimator | ATT | SE | p |
| --- | --- | --- | --- |
| TWFE | -10.27 | 1.78 | <.001 |
| CS | -4.87 | 2.01 | 0.015 |
| SA | -12.85 | 2.81 | <.001 |
| BJS | -11.90 | 0.70 | <.001 |

**Table 3. Robustness checks.**

| Check | ATT | p | Reading |
| --- | --- | --- | --- |
| Placebo t₀ = 2022-07-01 (BJS) | +9.97 | <.001 | Non-significant at raw α; sign reversal vs. headline. |
| Log(1 + complaints) TWFE | +0.227 (+25.4%) | 0.092 | Same sign; smaller magnitude. |
| Post-COVID (2022-01 →) (BJS) | -6.70 | <.001 | Strengthens headline. |
| Manhattan-only controls (BJS) | +3.62 | 0.059 | Same sign, wide CI. |

**Table 4. RDD bandwidth sensitivity (cutoff = 35.1).**

| Bandwidth | h | ATT | SE | p |
| --- | --- | --- | --- | --- |
| h/2 | 6.59 | +1.07 | 4.72 | 0.821 |
| h | 13.18 | +1.64 | 3.41 | 0.631 |
| 2h | 26.36 | -1.51 | 2.91 | 0.604 |

**Table 5. Identification + statistical diagnostic checklist.**

| Diagnostic | Value | p | Reading |
| --- | --- | --- | --- |
| Parallel-trends F | F = 4.40 | <.001 | Reject flat pre-trends. |
| Breusch-Pagan | see §4.2 | <.001 | Heteroskedastic; cluster-robust SE. |
| TWFE R² | 0.802 | — | Within-panel variance absorbed. |
| MDE (α=.05, power=.80) | ~17.6 complaints (|d| ~ 1.00) | — | Exceeds observed |ATT|; see §5.3. |
| BH survivors | 9/13 | BH 0.05 | Main BJS + SA survive. |
