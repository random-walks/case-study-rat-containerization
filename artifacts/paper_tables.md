**Table 1. Descriptive statistics, 2020–2024 panel.**

| Variable | Treated (9) | Control (65) | Total |
| --- | --- | --- | --- |
| Community districts | 9 | 65 | 74 |
| Months in window | 60 | 60 | 60 |
| CD-month observations | 540 | 3900 | 4,440 |
| Pre-treatment mean complaints/CD/month | 108.6 | 78.5 | — |
| Total Rodent complaints in window | — | — | 377,950 |

**Table 2. Four DiD estimators of the containerization-pilot effect.**

| Estimator | ATT | SE | p |
| --- | --- | --- | --- |
| TWFE | -15.29 | 7.37 | 0.038 |
| CS | -12.20 | 6.98 | 0.080 |
| SA | -12.20 | 3.61 | <.001 |
| BJS | -15.29 | 2.35 | <.001 |

**Table 3. Robustness checks.**

| Check | ATT | p | Reading |
| --- | --- | --- | --- |
| Placebo t₀ = 2022-07-01 (BJS) | +10.64 | 0.001 | Non-significant at raw α; sign reversal vs. headline. |
| Log(1 + complaints) TWFE | -0.072 (-6.9%) | 0.326 | Same sign; smaller magnitude. |
| Post-COVID (2022-01 →) (BJS) | -23.04 | <.001 | Strengthens headline. |
| Manhattan-only controls (BJS) | -44.35 | <.001 | Same sign, wide CI. |

**Table 4. RDD bandwidth sensitivity (cutoff = 70.3).**

| Bandwidth | h | ATT | SE | p |
| --- | --- | --- | --- | --- |
| h/2 | 13.49 | +6.48 | 9.79 | 0.508 |
| h | 26.97 | +7.61 | 7.10 | 0.284 |
| 2h | 53.95 | +2.54 | 6.77 | 0.707 |

**Table 5. Identification + statistical diagnostic checklist.**

| Diagnostic | Value | p | Reading |
| --- | --- | --- | --- |
| Parallel-trends F | F = 7.90 | <.001 | Reject flat pre-trends. |
| Breusch-Pagan | see §4.2 | <.001 | Heteroskedastic; cluster-robust SE. |
| TWFE R² | 0.812 | — | Within-panel variance absorbed. |
| MDE (α=.05, power=.80) | ~35.1 complaints (|d| ~ 1.00) | — | Exceeds observed |ATT|; see §5.3. |
| BH survivors | 6/13 | BH 0.05 | Main BJS + SA survive. |
