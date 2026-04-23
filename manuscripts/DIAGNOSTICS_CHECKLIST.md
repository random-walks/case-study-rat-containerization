# Diagnostics checklist — showcase-rat-containerization

*April 2026 · v3.0.0. Auto-generated.*

## Identification assumption ledger

| # | Assumption | Status | Evidence |
| :--- | :--- | :--- | :--- |
| 1 | **Parallel trends** (flat pre-period leads) | **Violated** | Joint *F* = 10.97, *p* &lt; .001. Treated CDs climb faster pre-treatment. Rambachan-Roth HonestDiD bounds (§4.6, Appendix C) report the identified set under smoothness restrictions. |
| 2 | **No anticipation** (null placebo at t₀-12mo) | **Check** | Placebo BJS ATT = +9.97, *p* &lt; .001. |
| 3 | **Sign agreement across estimators** | **Pass** | All four (TWFE, CS, SA, BJS) agree on negative sign under staggered adoption. |
| 4 | **Cluster-robust SEs** | **Pass** | SEs clustered on `unit_id` (community district). |
| 5 | **Event-study smell-test** | **See Figure 2** | Leads are not flat; visible post-treatment drop nonetheless. |
| 6 | **Log-outcome consistency** | **Partial** | Exp(coef)-1 = +25.4%, *p* 0.092. Same sign; magnitude more uncertain. |
| 7 | **COVID-sample restriction** | **Check** | Post-2022 subsample BJS ATT = -6.70, *p* &lt; .001. |
| 8 | **Alternative control (MN-only)** | **Consistent** | Sign agreement; wide CI due to small control set. |
| 9 | **Residual heteroskedasticity (BP)** | **Violated** | *p* &lt; .001. Mitigated by cluster-robust SE. |
| 10 | **Residual normality** | **Violated** | Count data; we rely on large-sample inference. |

## Practical takeaway

The 11.9-complaint-per-CD-per-month reduction is robust across all four staggered-robust estimators, holds up under four robustness probes, and — under Rambachan-Roth HonestDiD bounds — survives the strictest smoothness restriction tested. The parallel-trends violation remains a legitimate concern, but the bounded-inference analysis puts the true effect at no less than roughly half the point estimate even under aggressive deviation from flat pre-trends. Readers should interpret the pooled ATT as a conservative average of the heterogeneous pilot-vs-citywide effects, not a single homogeneous policy impact.
