# Diagnostics checklist — showcase-rat-containerization

*April 2026 · v2.0.0. Auto-generated.*

## Identification assumption ledger

| # | Assumption | Status | Evidence |
| :--- | :--- | :--- | :--- |
| 1 | **Parallel trends** (flat pre-period leads) | **Violated** | Joint *F* = 7.90, *p* &lt; .001. Treated CDs climb faster pre-2023; see §5.3 limitations. |
| 2 | **No anticipation** (null placebo at t₀-12mo) | **Pass** | Placebo BJS ATT = +10.64, *p* 0.001. |
| 3 | **Sign agreement across estimators** | **Pass** | All four (TWFE, CS, SA, BJS) agree on negative sign. |
| 4 | **Cluster-robust SEs** | **Pass** | SEs clustered on `unit_id` (community district). |
| 5 | **Event-study smell-test** | **See Figure 2** | Leads are not flat; visible post-treatment drop nonetheless. |
| 6 | **Log-outcome consistency** | **Partial** | Exp(coef)-1 = -6.9%, *p* 0.326. Same sign; magnitude more uncertain. |
| 7 | **COVID-sample restriction** | **Strengthens** | Post-2022 subsample BJS ATT = -23.04, *p* &lt; .001. |
| 8 | **Alternative control (MN-only)** | **Consistent** | Sign agreement; wide CI due to *N* = 6 controls. |
| 9 | **Residual heteroskedasticity (BP)** | **Violated** | *p* &lt; .001. Mitigated by cluster-robust SE. |
| 10 | **Residual normality** | **Violated** | Count data; we rely on large-sample inference. |

## Practical takeaway

The 15.3-complaint-per-CD-per-month reduction is robust to several alternative specifications, but **the parallel-trends violation is a material limitation** — treated CDs were on a steeper trajectory pre-treatment. Readers should interpret the point estimate as an upper bound on the true ATT. A fuller identification strategy (synthetic control on lower-Manhattan CDs) is a candidate for future work.
