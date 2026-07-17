# 11 — HonestDiD sensitivity bounds (Rambachan-Roth)

> **Tearsheet** for [`notebooks/11_honestdid_sensitivity.py`](../../notebooks/11_honestdid_sensitivity.py) · [HTML report](../../site/11_honestdid_sensitivity.html) · last run `2026-07-15T18:31:13+00:00`

The parallel-trends assumption the main-effect DiD leans on is
*rejected* by the pre-period joint $F$-test (§4.3 diagnostic).
Rambachan & Roth (2023, *Review of Economic Studies*) propose
bounds on the true $\tau$ under two families of identifying
restrictions that permit *some* deviation from flat pre-trends
without abandoning DiD entirely:

1. **Relative magnitudes (RM-$\bar M$)** — post-treatment deviation
   from parallel trends is at most $\bar M$ times the maximum
   pre-period deviation. At $\bar M = 0$, enforces flat pre-trends
   (the vanilla DiD assumption); at $\bar M = 1$, assumes post-
   deviation is no larger than the biggest pre-deviation; at
   $\bar M \to \infty$, imposes nothing.

2. **Smoothness (SD-$M$)** — the second difference of the
   counterfactual trend is bounded by $M$, enforcing that
   post-trends can extrapolate linearly from pre-trends with at
   most per-period smoothness $M$. $M = 0$ enforces a perfectly
   linear pre-period extrapolation.

We implement both restriction families in closed form using the
event-study coefficients from notebook 04. Because the
`HonestDiD` reference package is R-only (Rambachan & Roth's
original; an R/Julia ecosystem also hosts `HonestDiDR.jl`), we
inline a minimal Python port of the SD- and RM-bound formulae —
enough for the two robustness numbers the manuscript claims.

The bounds are *identified sets*, not confidence intervals — they
answer "under restriction X, what values of $\tau$ are consistent
with the data?", which is precisely what the reader asks when
parallel trends are rejected.

**Rambachan-Roth HonestDiD-style bounds: RM breakdown Mbar = 0.5; LT (linear-trend extrapolation) breakdown Mbar = None.**

| field | value |
| --- | --- |
| `inputs.n_pre_coefs` | `23` |
| `inputs.n_post_coefs` | `19` |
| `inputs.pre_coef_max_abs` | `19.45` |
| `inputs.pre_coef_mean` | `9.642` |
| `inputs.post_coef_mean` | `-1.772` |
| `relative_magnitudes_sweep` | `[{'Mbar': 0.0, 'D_pre': 19.454692293613466, 'tau_hat': -1.7715420577716894, 'lower': -1.7715420577716894, 'upper': -1.7715420577716894, 'half_width': 0.0, 'includes_zero': False}, {'Mbar': 0.5, 'D_pre': 19.454692293613466, 'tau_hat': -1.7715420577716894, 'lower': -11.498888204578423, 'upper': 7.955804089035043, 'half_width': 9.727346146806733, 'includes_zero': True}, {'Mbar': 1.0, 'D_pre': 19.454692293613466, 'tau_hat': -1.7715420577716894, 'lower': -21.226234351385155, 'upper': 17.683150235841776, 'half_width': 19.454692293613466, 'includes_zero': True}, {'Mbar': 1.5, 'D_pre': 19.454692293613466, 'tau_hat': -1.7715420577716894, 'lower': -30.95358049819189, 'upper': 27.41049638264851, 'half_width': 29.1820384404202, 'includes_zero': True}, {'Mbar': 2.0, 'D_pre': 19.454692293613466, 'tau_hat': -1.7715420577716894, 'lower': -40.68092664499862, 'upper': 37.13784252945524, 'half_width': 38.90938458722693, 'includes_zero': True}]` |
| `linear_trend_sweep` | `[{'Mbar': 0.0, 'pre_trend_slope_per_month': 0.4866822850337067, 'pre_trend_intercept': 15.969263871817509, 'max_abs_pre_residual': 7.999886069247907, 'bias_linear_extrapolation': 20.34940443712087, 'tau_hat_uncorrected': -1.7715420577716894, 'tau_adj_linear': -22.12094649489256, 'lower': -22.12094649489256, 'upper': -22.12094649489256, 'half_width': 0.0, 'includes_zero': False}, {'Mbar': 0.5, 'pre_trend_slope_per_month': 0.4866822850337067, 'pre_trend_intercept': 15.969263871817509, 'max_abs_pre_residual': 7.999886069247907, 'bias_linear_extrapolation': 20.34940443712087, 'tau_hat_uncorrected': -1.7715420577716894, 'tau_adj_linear': -22.12094649489256, 'lower': -26.120889529516514, 'upper': -18.121003460268607, 'half_width': 3.9999430346239535, 'includes_zero': False}, {'Mbar': 1.0, 'pre_trend_slope_per_month': 0.4866822850337067, 'pre_trend_intercept': 15.969263871817509, 'max_abs_pre_residual': 7.999886069247907, 'bias_linear_extrapolation': 20.34940443712087, 'tau_hat_uncorrected': -1.7715420577716894, 'tau_adj_linear': -22.12094649489256, 'lower': -30.120832564140468, 'upper': -14.121060425644654, 'half_width': 7.999886069247907, 'includes_zero': False}, {'Mbar': 1.5, 'pre_trend_slope_per_month': 0.4866822850337067, 'pre_trend_intercept': 15.969263871817509, 'max_abs_pre_residual': 7.999886069247907, 'bias_linear_extrapolation': 20.34940443712087, 'tau_hat_uncorrected': -1.7715420577716894, 'tau_adj_linear': -22.12094649489256, 'lower': -34.120775598764425, 'upper': -10.1211173910207, 'half_width': 11.99982910387186, 'includes_zero': False}, {'Mbar': 2.0, 'pre_trend_slope_per_month': 0.4866822850337067, 'pre_trend_intercept': 15.969263871817509, 'max_abs_pre_residual': 7.999886069247907, 'bias_linear_extrapolation': 20.34940443712087, 'tau_hat_uncorrected': -1.7715420577716894, 'tau_adj_linear': -22.12094649489256, 'lower': -38.12071863338838, 'upper': -6.121174356396747, 'half_width': 15.999772138495814, 'includes_zero': False}]` |
| `breakdown_Mbar_RM` | `0.5` |
| `breakdown_Mbar_LT` | `null` |
| `interpretation` | Under relative-magnitudes restriction RM(Mbar): the pooled post-period ATT re… |


![fig7_honestdid](../../artifacts/figures/figure-7-honestdid.png)

**Figure 7. HonestDiD (Rambachan-Roth 2023) sensitivity bounds on the pooled post-period ATT under two identifying restrictions. Left: relative-magnitudes RM(M̄). Right: smoothness SD(M). Breakdown points (smallest restriction that permits a zero-effect identified set) are reported in the manuscript §4.6.**

| field | value |
| --- | --- |
| `path` | artifacts/figures/figure-7-honestdid.png |


**Next:** `12_synthetic_control.py` — Abadie-Diamond-Hainmueller
synthetic control as a complementary identification strategy that
does not assume parallel trends at all.

---

*Auto-generated by `jellycell export tearsheet notebooks/11_honestdid_sensitivity.py`. Regenerating overwrites this file — for hand-authored writeups put a `.md` at the root of `manuscripts/` instead of under `tearsheets/`.*
