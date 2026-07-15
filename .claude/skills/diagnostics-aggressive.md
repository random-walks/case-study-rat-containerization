---
name: diagnostics-aggressive
description: Report full statistical diagnostics aggressively — effect sizes alongside p-values, CIs, multiple-comparison correction, robustness checks, honest acknowledgment of assumption violations. Apply to every quantitative claim in every notebook.
---

# Aggressive diagnostics

"Report p < .05" by itself is the floor, not the ceiling. This skill encodes
the diagnostic rigor this case study reaches for.

## The minimum reporting set for any test

For a regression coefficient:

```
β = 0.263, SE = 0.017, 95% CI [.230, .296], *t*(2313) = 15.93, *p* < .001
```

Not:
```
β = 0.263***
```

For a group comparison:

```
*t*(2315) = -3.34, *p* < .001, Cohen's *d* = -0.14, 95% CI [-0.19, -0.09]
```

For a proportion / count test:

```
χ²(1, *N* = 157) = 4.82, *p* = .028, Cramer's *V* = 0.18
```

**Always include**:
1. Point estimate (β, M, r, etc.)
2. Dispersion (SE, SD)
3. 95% confidence interval
4. Test statistic (*t*, *F*, χ², *z*)
5. Degrees of freedom
6. Exact p-value (to 3 decimal places unless < .001)
7. Effect size (Cohen's *d*, *η*², *R*², OR, RR, Cramer's *V*)

## Effect size conventions (Cohen, 1988)

| Statistic | Small | Medium | Large |
| :--- | ---: | ---: | ---: |
| Cohen's *d* | 0.20 | 0.50 | 0.80 |
| *r* | .10 | .30 | .50 |
| *η*² | .01 | .06 | .14 |
| Cramer's *V* | .10 | .30 | .50 |

Always name the magnitude alongside the number. "Cohen's *d* = 0.29, small per Cohen (1988)".

## Multiple comparison correction

If you test ≥ 3 hypotheses simultaneously, correct. Default to **Benjamini-Hochberg** (false discovery rate); use Bonferroni only if you have strong a priori reasons to prefer family-wise error control.

```python
from scipy.stats import false_discovery_control
# or statsmodels
from statsmodels.stats.multitest import multipletests

pvals_raw = [r.pvalue for r in results]
reject, pvals_bh, _, _ = multipletests(pvals_raw, method="fdr_bh", alpha=0.05)
```

Report both raw and BH-corrected in the same table. Do not silently drop findings that survive raw but not BH; discuss the difference.

## Robustness — the minimum set for an observational claim

Any causal/quasi-causal claim ships with:

1. **Specification robustness** — main model ± key covariates. Coefficient stability informs confound concerns.
2. **Functional form** — linear + quadratic, or linear + log-transformed outcome. Report both.
3. **Sample restrictions** — full sample + at least one sensible subsample (e.g., exclude outlier tracts). Report both.
4. **Placebo** — rerun the main spec on an outcome that shouldn't be affected. Null effect = reassuring.
5. **Alternative estimator** — e.g., for DiD: TWFE + Callaway-Sant'Anna + Sun-Abraham + Borusyak-Jaravel-Spiess. `factor_factory.engines.did.estimate(methods=(...))` gives you all four in one call.

## Assumption checking — the honest list per method

### OLS
- **Heteroskedasticity**: Breusch-Pagan or White test. If significant, use HC1 robust SE (`cov_type="HC1"` in statsmodels).
- **Normality of residuals**: Q-Q plot + Shapiro-Wilk. For *n* > 1000 the test over-rejects; trust the Q-Q plot.
- **Multicollinearity**: VIF per predictor. VIF > 10 is a problem; VIF > 5 warrants discussion.
- **Spatial autocorrelation** (geographic data): Moran's *I* on residuals. Significant = OLS SE likely understated; use Conley/spatial-HAC SE or switch to SAR.
- **Influential observations**: Cook's *D*, leverage plots. Inspect any obs with Cook's *D* > 4/*n*.

### DiD
- **Parallel trends**: event study / pre-trend plot, aggregate pre-period F-test. If trends diverge pre-treatment, report it and discuss.
- **Treatment timing heterogeneity**: if staggered adoption, use Callaway-Sant'Anna or Sun-Abraham (TWFE is biased under heterogeneous ATT).
- **Anticipation**: shift placebo treatment 1-2 periods early. Null coefficient = no anticipation.
- **Spillovers**: check if untreated units geographically adjacent to treated units are themselves affected. If so, control coverage is contaminated.

### RDD
- **Density continuity** at cutoff (McCrary 2008 or rddensity Cattaneo et al. 2020). `rddensity` 2.4.6 is broken on pandas 2 — fall back to manual chi-square binning of the running variable around the cutoff.
- **Covariate balance** at cutoff — regress each pretreatment covariate on treatment × running-variable. Coefficients should be ≈0.
- **Bandwidth sensitivity**: rerun with h/2, h, 2h. `rdrobust` reports MSERD-optimal *h* by default; report estimates at ±50% and ±100%.
- **Placebo cutoffs**: rerun at cutoffs ±10% of the real one. Null = reassuring.

### Spatial
- **Weights matrix sensitivity**: rerun with distance-band (1km, 2km, 5km) + k-nearest (k=4, 8, 16). Qualitative conclusions should hold.
- **Row-standardization**: W vs. W* (row-standardized). Report both Moran's *I* estimates.

## Power + MDE

For any null result, report the **minimum detectable effect** (MDE) at 80% power, α = .05, for your sample size. "Null" without MDE is uninformative.

```python
from statsmodels.stats.power import TTestIndPower
analysis = TTestIndPower()
mde = analysis.solve_power(effect_size=None, nobs1=n_treat, ratio=n_ctrl/n_treat,
                            alpha=0.05, power=0.80)
# report as Cohen's d MDE; convert to natural units for interpretability
```

## When to invoke this skill

- Writing any `03_*.py`, `04_*.py`, `05_*.py` notebook with a statistical claim.
- Reviewing an `AUDIT.md` or paper draft for diagnostic gaps.
- Before calling the study "done" — checklist the assumptions for every reported spec.

## When NOT to invoke this skill

- Descriptive stats in `01_load_and_explore.py` — means/medians/SDs without tests are fine.
- Purely synthetic-data demos where the goal is showing the API, not making a claim.
