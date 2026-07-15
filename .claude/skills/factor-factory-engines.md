---
name: factor-factory-engines
description: Engine family selection guide for factor-factory 1.x. Apply when designing a notebook analysis — picks the right engine family for the research question and ensures the Panel / Estimate protocol is followed.
---

# factor-factory engine selection

`factor-factory` 1.0.2 ships 20 engine families organized by research task.
Every engine consumes a `factor_factory.tidy.Panel` and returns a frozen
result dataclass. This skill maps research questions to engines.

## Engine map

| Research question | Family | Method(s) | Extra |
| :--- | :--- | :--- | :--- |
| "Did *X* cause *Y*?" with panel + staggered treatment | `did` | `twfe`, `cs` (Callaway-Sant'Anna), `sa` (Sun-Abraham), `bjs` (Borusyak-Jaravel-Spiess) | `[did]` |
| "Does effect jump discontinuously at cutoff *c*?" | `rdd` | `rd_robust` (Calonico-Cattaneo-Farrell-Titiunik) | `[rdd]` |
| "What would *Y* have been without policy *P*?" | `scm` | `augmented`, `vanilla` | `[scm]` |
| "Is the outcome spatially clustered?" | `spatial` | `morans_i`, `lisa`, `spatial_lag` | `[spatial]` |
| "Trend decomposition?" | `stl` | `stl` (seasonal-trend-loess) | `[stl]` |
| "Where are the structural breaks?" | `changepoint` | `pelt`, `binary_segmentation`, `window` | `[changepoint]` |
| "Inequality — by group, over time?" | `inequality` | `theil`, `gini`, `oaxaca_blinder` | `[inequality]` |
| "Simple panel regression, fixed effects?" | `panel_reg` | `twfe`, `pooled`, `first_diff` | (in `[did]`) |
| "Power calc / MDE for planning?" | `power` | `mde`, `power_curve` | (stdlib only) |
| "Event-study plot for a DiD?" | `did.event_study` | via `estimate(..., event_study=True)` | `[did]` |

## The Panel contract

Every engine requires `factor_factory.tidy.Panel`:

```python
from factor_factory.tidy import Panel, TreatmentEvent

panel = Panel.from_dataframe(
    df,                                    # pandas DataFrame, long format
    unit_col="tract_id",                   # str, entity identifier
    time_col="year",                       # str, time period (int or datetime)
    outcome_cols=["rat_complaints"],       # list[str], one or more
    covariates=["poverty_rate", "income"], # list[str], optional
    treatment_events=[                     # list[TreatmentEvent], optional
        TreatmentEvent(unit_id="tract_001", event_time=2022, kind="policy"),
        ...
    ],
    weights_col=None,                      # str | None, sample weights
)
```

**From a nyc311 pipeline** (the usual path for real data):

```python
from nyc311.pipeline import Pipeline

pipe = Pipeline.from_query(complaint_types=("Rodent",), start="2020-01-01", end="2024-12-31")
panel = pipe.to_factor_factory_panel(
    unit_level="tract",
    time_level="month",
    treatment_events=nyc311.data.rat_mitigation_events_2023(),
)
# panel is already a factor_factory.tidy.Panel
```

## The Estimate contract

All `did.estimate()`, `rdd.rd_robust()`, etc. return frozen dataclasses with:

```python
result.atte           # point estimate (float)
result.se             # std error (float)
result.pvalue         # two-sided p (float)
result.ci_low, ci_high  # 95% CI (float, float)
result.method         # method name (str)
result.n              # sample size (int)
result.diagnostics    # dict[str, Any] with method-specific extras
result.to_dict()      # JSON-serializable
```

For multi-method calls (`did.estimate(methods=("twfe", "cs", "sa", "bjs"))`), you get a `dict[str, Estimate]` keyed by method name.

## Canonical DiD pattern

```python
from factor_factory.engines.did import estimate as did_estimate

result = did_estimate(
    panel,
    outcome="rat_complaints",
    methods=("twfe", "cs", "sa", "bjs"),
    covariates=["poverty_rate", "seasonal_dummies"],
    se="clustered",         # cluster SE on unit
    cluster_col="tract_id",
    event_study=True,       # emits pre-trend diagnostics in result.diagnostics
)

# Cross-estimator sanity: all four should agree on sign of ATTE.
signs = {m: (r.atte > 0) for m, r in result.items()}
assert len(set(signs.values())) == 1, f"Estimators disagree on sign: {signs}"
```

## Canonical RDD pattern

```python
from factor_factory.engines.rdd import rd_robust

result = rd_robust(
    panel,
    running_var="store_sqft",
    outcome="compliance_rate",
    cutoff=3000,
    bandwidth=None,         # None → MSERD-optimal via rdrobust
    polynomial_order=1,     # local linear; bump to 2 for sensitivity
)

# Sensitivity — rerun at ±50% and ±100% of optimal h
h_opt = result.diagnostics["bandwidth"]
for h in (h_opt * 0.5, h_opt, h_opt * 2):
    r = rd_robust(panel, running_var="store_sqft", outcome="compliance_rate",
                  cutoff=3000, bandwidth=h)
    print(f"h={h:.0f}  ATTE={r.atte:.3f}  p={r.pvalue:.3f}")
```

## Canonical spatial pattern

```python
from factor_factory.engines.spatial import morans_i, lisa, spatial_lag

# Global clustering
moran = morans_i(panel, variable="gap_score", weights="distance_band", threshold_m=2000)
# moran.atte is the Moran's I statistic

# Local clustering (LISA)
local = lisa(panel, variable="gap_score", weights="distance_band", threshold_m=2000)
# local.diagnostics["cluster_labels"] is a tuple of "HH"/"LL"/"HL"/"LH"/"ns" per unit

# Spatial lag model (autoregressive)
lag = spatial_lag(panel, outcome="gap_score",
                  covariates=["poverty_rate", "disability_rate"],
                  weights="distance_band", threshold_m=2000)
```

## The jellycell bridge

`factor_factory.jellycell` (shipped in 1.0+) provides:

- `factor_factory.jellycell.cells.as_jc_artifact(result)` — converts an Estimate to a dict that `jc.save()` can consume cleanly.
- `factor_factory.jellycell.figure.event_study_plot(result)` — returns matplotlib Figure for `jc.figure`.
- `factor_factory.jellycell.tearsheets.findings_payload(results)` — canonical dict structure for `jellycell.tearsheets.findings()`.

## Common mistakes

1. **Passing a `pd.DataFrame` directly to an engine** — wrap in `Panel.from_dataframe` first.
2. **Forgetting `treatment_events` on the Panel** — DiD engines will error with a crisp message.
3. **Running TWFE on staggered treatment without checking** — TWFE is biased under heterogeneous ATT; always run `cs`/`sa`/`bjs` alongside.
4. **Using `methods="twfe"` (string) instead of `methods=("twfe",)` (tuple)** — the API expects iterable. String will work but iterate character-by-character in weird error messages.
5. **Mutating the Panel between engines** — Panels are frozen, don't try.

## When to invoke this skill

- Before writing any engine call — pick family first.
- When refactoring hand-rolled stats code to factor-factory engines.
- When deciding whether to add a new method vs. use an existing engine.

## Reference
- [factor-factory docs/og_context/03_specs/engine_protocol.md](https://github.com/random-walks/factor-factory/blob/main/docs/og_context/03_specs/engine_protocol.md)
- [factor-factory docs/og_context/03_specs/panel_contract.md](https://github.com/random-walks/factor-factory/blob/main/docs/og_context/03_specs/panel_contract.md)
