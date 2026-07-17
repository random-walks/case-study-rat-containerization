# Appendix C — HonestDiD mathematical details

Formal statements of the two Rambachan-Roth-style bound families
reported in §4.6, plus implementation notes.

## C.1 Setting

Let $\delta_t$ denote the event-study coefficient at relative time
$t$, with $\delta_{-1} = 0$ by convention (the reference period).
Under no bias from pre-treatment trends, $\delta_t = 0$ for all
$t < 0$ and $\delta_t = \tau_t$ for $t \ge 0$, where $\tau_t$ is
the dynamic ATT at lag $t$. The pooled post-period ATT is

$$
\tau = \frac{1}{T_\text{post}} \sum_{t=0}^{T_\text{post}-1} \tau_t
$$

In practice, $\hat\delta_t$ for $t < 0$ is not identically zero;
the pre-period event-study coefficients $\{\hat\delta_t\}_{t<0}$
carry the empirical signature of the parallel-trends violation.
The [Rambachan & Roth (2023)](../../MANUSCRIPT.md#ref-rambachan2023)
framework expresses the *bias* in the pooled post-period ATT as a
function of the (unobservable) counterfactual trend $\delta_t^{CF}$
at post-period lags, and bounds the bias under a restriction on
how much $\delta_t^{CF}$ can deviate from the extrapolated
pre-trend.

The identified set for $\tau$ under restriction $R$ is

$$
\mathcal{I}(R) = \left\{ \hat\tau - B(R) : B(R) \text{ consistent with } R \right\}
$$

where $B(R)$ is the bias under $R$ and $\hat\tau$ is the observed
pooled post-period coefficient.

## C.2 Relative-magnitudes (RM-$\bar M$)

**Restriction.** Define $D_\text{pre} = \max_{t<0} |\hat\delta_t|$.
The RM-$\bar M$ restriction asserts

$$
|\delta_t^{CF}| \le \bar M \cdot D_\text{pre} \quad \forall\, t \ge 0
$$

— the counterfactual post-period deviation is bounded by a
multiple of the largest observed pre-period deviation. At $\bar M
= 0$, the restriction is "parallel trends hold" (vanilla DiD); at
$\bar M = 1$, "post-period deviations are no larger than the
biggest pre-period deviation"; as $\bar M \to \infty$, the
restriction imposes nothing and the identified set is the real
line.

**Bound.** Under RM-$\bar M$, the bias is

$$
B(\bar M) = \frac{1}{T_\text{post}} \sum_{t=0}^{T_\text{post}-1} \delta_t^{CF} \in [-\bar M D_\text{pre}, \bar M D_\text{pre}]
$$

so the identified set is

$$
\mathcal{I}(\bar M) = [\hat\tau - \bar M D_\text{pre},\, \hat\tau + \bar M D_\text{pre}]
$$

This is a symmetric interval centered on the observed pooled ATT
with half-width $\bar M D_\text{pre}$.

**Breakdown point.** The smallest $\bar M$ such that
$\mathcal{I}(\bar M)$ includes zero:

$$
\bar M^* = \frac{|\hat\tau|}{D_\text{pre}}
$$

In our panel (per-unit event-study spec), $\hat\tau = -1.77$,
$D_\text{pre} = 19.45$, so $\bar M^* = 0.091$. Reported as
"breakdown at $\bar M = 0.5$" in the paper because we only sweep
the grid $\{0, 0.5, 1.0, 1.5, 2.0\}$.

## C.3 Linear-trend extrapolation (LT-$\bar M$)

The RM family is coarse: it bounds deviation in levels, not
deviation from a clear trend signal. When the pre-period
coefficients visibly trend (as ours do, with a fitted slope of
$+0.49$ complaints per month), the relevant "counterfactual trend"
is the *continuation* of that linear trend, not the absolute level.

**Setup.** Fit an OLS line to the pre-period coefficients:

$$
\hat\delta_t = \hat a + \hat b \cdot t + \hat e_t \quad \text{for } t < 0
$$

The extrapolated counterfactual trend at post-period lag $t \ge 0$
is $\hat a + \hat b \cdot t$. Define the **maximum absolute
pre-period residual** as

$$
R_\text{pre} = \max_{t < 0} |\hat e_t|
$$

**Restriction.** The LT-$\bar M$ restriction asserts

$$
|\delta_t^{CF} - (\hat a + \hat b t)| \le \bar M R_\text{pre} \quad \forall\, t \ge 0
$$

— the counterfactual deviation from the extrapolated linear trend
is bounded by a multiple of the largest pre-period residual. At
$\bar M = 0$, we assume the linear extrapolation holds exactly; at
$\bar M = 1$, we allow deviations up to the largest residual.

**Bound.** Under LT-$\bar M$, the trend-adjusted ATT is

$$
\tau_\text{adj}(\bar M) = \hat\tau - \overline{(\hat a + \hat b t)}_{t \ge 0}
$$

where the second term is the mean of the extrapolated linear trend
over the post-period. The identified set is

$$
\mathcal{I}(\bar M) = [\tau_\text{adj} - \bar M R_\text{pre},\, \tau_\text{adj} + \bar M R_\text{pre}]
$$

— a symmetric interval centered on the trend-adjusted ATT with
half-width $\bar M R_\text{pre}$.

**Breakdown point.**

$$
\bar M^* = \frac{|\tau_\text{adj}|}{R_\text{pre}}
$$

In our panel, $\tau_\text{adj} = -22.12$, $R_\text{pre} = 8.00$,
so $\bar M^* = 2.77$. Reported as "breakdown beyond $\bar M = 2.0$"
because the sweep grid tops out at $2.0$.

## C.4 Why we report LT alongside RM

When the pre-period is *stationary around zero with bounded
jitter*, RM is the natural restriction family — there is no trend
to extrapolate, just noise. When the pre-period visibly *trends*,
RM is overly conservative because it bounds deviation in levels
(which grow with time under a linear trend) rather than deviation
from the trend's extrapolation. Our pre-period is the second case,
so LT is the more informative restriction family.

The LT family is not the original Rambachan-Roth smoothness (SD)
restriction — SD bounds the second difference of the
counterfactual trend, which grows the identified-set half-width
quadratically in the post-period horizon and quickly becomes
uninformative for long post-windows. LT is a simpler cousin that
keeps the half-width constant by construction and is more
interpretable for a 19-month post-window.

## C.5 Interpretation for a non-econometrician

The LT-$\bar M$ restriction says: "imagine the pre-period trend
kept going — what post-period deviation from that smooth
extrapolation can you tolerate before the estimate becomes zero?"
At $\bar M = 2$ we're asking "can we tolerate a deviation twice as
large as the biggest pre-period jitter?" The answer is yes — the
identified set is still entirely negative.

This is the concrete operational content of "the HonestDiD bounds
say the parallel-trends rejection is not fatal." The pre-period
trend was doing something — but whatever the counterfactual
post-period trend was, within a reasonable bound on deviation
from its linear extrapolation, the treatment effect is robustly
negative.

## C.6 Caveats and limitations of this implementation

1. **Single-number summary of the pooled post-period ATT.** We
   report bounds on the pooled ATT rather than on individual
   post-period event-study coefficients. The original
   Rambachan-Roth construction is lag-by-lag; pooled bounds are a
   summary.
2. **Linear extrapolation assumption.** LT assumes the pre-period
   trend is well-approximated by OLS. In our panel the fit is
   good (R² ≈ 0.6 for the linear OLS on 23 pre-period points),
   but a non-linear pre-trend would require a more flexible fit.
3. **No confidence-interval coverage.** The bounds are
   *identified sets*, not confidence intervals. Combining
   statistical uncertainty (the event-study SEs) with
   identification uncertainty (the $\bar M$ sensitivity) requires
   the Rambachan-Roth conditional-coverage construction, which
   we have not implemented in the Python port. A follow-up
   revision will either add this or swap in the R
   [HonestDiD](https://github.com/asheshrambachan/HonestDiD)
   package through an `rpy2` bridge.
4. **Bounds on pooled ATT, not on per-cohort ATT.** The per-cohort
   decomposition in §4.4 is NOT subjected to the HonestDiD
   analysis directly; it uses the standard TWFE confidence
   intervals. An extension would apply HonestDiD to each cohort's
   own event study separately.

The implementation lives in
[`notebooks/11_honestdid_sensitivity.py`](https://github.com/random-walks/case-study-rat-containerization/blob/main/notebooks/11_honestdid_sensitivity.py)
and consumes the event-study CSV from `notebooks/04_diagnostics.py`.
Regeneration is deterministic (same CSV → same bounds) and takes
under a second on the cached artifacts.
