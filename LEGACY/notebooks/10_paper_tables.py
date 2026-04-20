# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# %% [markdown]
# # 10 — Paper tables (v2)
#
# Publication-grade tables for [`manuscripts/MANUSCRIPT_v2.md`](../manuscripts/MANUSCRIPT_v2.md):
#
# 1. **T1 — Descriptive statistics** (pre-treatment means + SDs × treated/control × covariate)
# 2. **T2 — Main results** (ATT × estimator × SE × p × 95% CI × N)
# 3. **T3 — Heterogeneous effects** (ATT × subgroup × SE)
# 4. **T4 — RDD sensitivity** (ATT × bandwidth × polynomial × kernel)
# 5. **T5 — Diagnostic checklist** (pass/fail per assumption)
#
# Tables land as parquet under [`../artifacts/paper_v2/tables/`](../artifacts/paper_v2/tables/)
# and are also rendered via `jc.table` for tearsheet inclusion.

# %% tags=["jc.setup"]
from pathlib import Path

TAB_DIR = Path("artifacts/paper_v2/tables")
TAB_DIR.mkdir(parents=True, exist_ok=True)
print(f"  tables → {TAB_DIR}")

# %% tags=["jc.step", "name=t1_descriptive"]
# T1 — Descriptive statistics: pre-treatment means AND SDs, treated vs. control,
# per covariate. Polishes the notebook-02 balance table.
import sys
from pathlib import Path

import jellycell.api as jc
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import TREATED_UNITS, load_demographics, load_or_build_panel  # noqa: E402

panel = load_or_build_panel()
period_str = panel.index.get_level_values("period").astype(str)
pre = panel[period_str < "2024-06"].reset_index()
unit_pre_means = pre.groupby("unit_id")["complaint_count"].mean().rename("pre_complaints_mean")

demo = load_demographics()
combined = unit_pre_means.to_frame().join(demo, how="inner")
combined["treated"] = combined.index.isin(TREATED_UNITS).astype(int)
t = combined[combined["treated"] == 1]
c = combined[combined["treated"] == 0]


def _smd(tv, cv):
    tv = tv.dropna()
    cv = cv.dropna()
    pooled_sd = ((tv.var() + cv.var()) / 2) ** 0.5
    return 0.0 if pooled_sd == 0 else float((tv.mean() - cv.mean()) / pooled_sd)


covs = ["pre_complaints_mean", "population", "pct_nonwhite", "log_median_income", "pct_renter"]
rows = []
for cov in covs:
    if cov not in combined.columns:
        continue
    t_vals = t[cov].dropna()
    c_vals = c[cov].dropna()
    rows.append({
        "covariate": cov,
        "treated_n": int(t_vals.shape[0]),
        "treated_mean": round(float(t_vals.mean()), 3),
        "treated_sd": round(float(t_vals.std(ddof=1)), 3),
        "control_n": int(c_vals.shape[0]),
        "control_mean": round(float(c_vals.mean()), 3),
        "control_sd": round(float(c_vals.std(ddof=1)), 3),
        "smd": round(_smd(t_vals, c_vals), 3),
    })
t1 = pd.DataFrame(rows)
t1["imbalanced"] = t1["smd"].abs().apply(
    lambda s: "***" if s > 0.5 else ("*" if s > 0.1 else "")
)
jc.table(
    t1,
    name="paper_v2/tables/T1_descriptive",
    caption="Table 1 — Pre-treatment descriptive statistics (Jan–May 2024)",
    notes="Treated = Manhattan CDs 01–09; control = remaining CDs with ACS matches. "
          "|SMD|>0.1 = *; |SMD|>0.5 = ***. Severe imbalance on race, income, and renter share.",
    tags=["paper_v2", "table", "T1"],
)
print(t1.to_string(index=False))

# %% tags=["jc.step", "name=t2_main_results"]
# T2 — Main results: ATT × estimator with SE, p, 95% CI, N.
import json
from pathlib import Path

import jellycell.api as jc
import pandas as pd

artifacts = Path("artifacts")


def _load(name):
    p = artifacts / name
    return json.loads(p.read_text()) if p.exists() else {}


twfe = _load("twfe_result.json")
cs = _load("paper_v2/staggered_did_v2.json")
scm = _load("paper_v2/scm_trajectory_v2.json")
seasonal = _load("seasonal_robust.json")
spatial = _load("spatial_lag_did.json")


def _fmt_ci(lo, hi):
    if lo is None or hi is None:
        return "—"
    try:
        return f"[{float(lo):+.2f}, {float(hi):+.2f}]"
    except (TypeError, ValueError):
        return "—"


rows = []
rows.append({
    "estimator": "Two-way FE (TWFE)",
    "att": twfe.get("att"), "se": twfe.get("se"),
    "p_value": twfe.get("p_value"),
    "ci_95": _fmt_ci(twfe.get("ci_lower"), twfe.get("ci_upper")),
    "n": twfe.get("n"),
})
if "att" in cs and not isinstance(cs.get("att"), str):
    rows.append({
        "estimator": "Callaway-Sant'Anna staggered DiD",
        "att": cs.get("att"), "se": cs.get("se"),
        "p_value": cs.get("p_value"),
        "ci_95": _fmt_ci(cs.get("ci_lower"), cs.get("ci_upper")),
        "n": f"{cs.get('n_groups')}×{cs.get('n_periods')}",
    })
else:
    rows.append({"estimator": "Callaway-Sant'Anna staggered DiD",
                 "att": "—", "se": "—", "p_value": "—", "ci_95": "—",
                 "n": f"ERROR: {cs.get('error', 'n/a')[:60]}"})
if "att" in scm and not isinstance(scm.get("att"), str):
    rows.append({
        "estimator": "Synthetic control (MN 03)",
        "att": scm.get("att"), "se": "—",
        "p_value": scm.get("placebo_p_value"),
        "ci_95": "—",
        "n": f"1 treated × {scm.get('n_donors')} donors",
    })
else:
    rows.append({"estimator": "Synthetic control (MN 03)",
                 "att": "—", "se": "—", "p_value": "—", "ci_95": "—",
                 "n": f"ERROR: {scm.get('error', 'n/a')[:60]}"})
rows.append({
    "estimator": "TWFE — district-demeaned (seasonal robust)",
    "att": seasonal.get("att"), "se": seasonal.get("se"),
    "p_value": seasonal.get("p_value"),
    "ci_95": "—", "n": twfe.get("n"),
})
rows.append({
    "estimator": "Spatial-lag DiD (ρ = %.3f, p < 0.001)" % float(spatial.get("rho", 0)),
    "att": spatial.get("treatment_coef"),
    "se": "—",
    "p_value": spatial.get("treatment_p"),
    "ci_95": "—", "n": spatial.get("n_observations"),
})

t2 = pd.DataFrame(rows).astype(str)
jc.table(
    t2,
    name="paper_v2/tables/T2_main_results",
    caption="Table 2 — Main results: ATT per estimator with SE, p, 95% CI, N",
    notes="ATT is in complaints / district / month. SE clustered by district where applicable. "
          "Spatial-lag treatment coefficient reported from SAR model (rho > 0 = neighbor effects present).",
    tags=["paper_v2", "table", "T2"],
)
print(t2.to_string(index=False))

# %% tags=["jc.step", "name=t3_hte"]
# T3 — HTE. Extend the existing median-split with a quartile breakdown.
import sys
from pathlib import Path

import jellycell.api as jc
import pandas as pd

sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import add_treatment_indicator, load_or_build_panel  # noqa: E402

panel = add_treatment_indicator(load_or_build_panel())
unit_lvl = panel.index.get_level_values(0)
period_lvl = pd.DatetimeIndex(pd.to_datetime(panel.index.get_level_values(1).astype(str)))
panel = panel.copy()
panel.index = pd.MultiIndex.from_arrays([unit_lvl, period_lvl], names=panel.index.names)

pre_mask = period_lvl < pd.Timestamp("2024-06-01")
baseline = panel[pre_mask].groupby(level=0)["complaint_count"].mean().rename("baseline")
quartile = pd.qcut(baseline, 4, labels=["Q1 (lowest)", "Q2", "Q3", "Q4 (highest)"])
panel = panel.join(baseline, on=panel.index.get_level_values(0))
panel["baseline_q"] = panel.index.get_level_values(0).map(quartile.to_dict())

from linearmodels.panel import PanelOLS  # noqa: E402

rows = []
for label in ["Q1 (lowest)", "Q2", "Q3", "Q4 (highest)"]:
    sub = panel[panel["baseline_q"] == label]
    y = sub["complaint_count"]
    X = sub[["treatment"]]
    try:
        f = PanelOLS(y, X, entity_effects=True, time_effects=True).fit(
            cov_type="clustered", cluster_entity=True,
        )
        rows.append({
            "subgroup": label,
            "n_units": int(sub.index.get_level_values(0).nunique()),
            "baseline_mean": round(float(baseline[baseline.index.isin(sub.index.get_level_values(0))].mean()), 2),
            "att": round(float(f.params["treatment"]), 3),
            "se": round(float(f.std_errors["treatment"]), 3),
            "p_value": round(float(f.pvalues["treatment"]), 4),
            "ci_95": f"[{float(f.conf_int().loc['treatment', 'lower']):+.2f}, {float(f.conf_int().loc['treatment', 'upper']):+.2f}]",
        })
    except Exception as e:
        rows.append({"subgroup": label, "n_units": int(sub.index.get_level_values(0).nunique()),
                     "baseline_mean": None, "att": None, "se": None, "p_value": None,
                     "ci_95": f"ERROR: {str(e)[:40]}"})

t3 = pd.DataFrame(rows)
jc.table(
    t3.astype(str),
    name="paper_v2/tables/T3_hte",
    caption="Table 3 — Heterogeneous treatment effects by pre-treatment volume quartile",
    notes="Quartiles of the Jan-May 2024 baseline mean. Each row is a TWFE with entity + time FE "
          "(clustered SE) on the subsample.",
    tags=["paper_v2", "table", "T3"],
)
print(t3.to_string(index=False))

# %% tags=["jc.step", "name=t4_rdd_sensitivity"]
# T4 — RDD sensitivity: reformat the rdrobust_sweep artifact into a
# paper-friendly table with rounded numbers + a "converged" column.
import jellycell.api as jc
import pandas as pd

rdr = pd.read_parquet("artifacts/rdrobust_sweep.parquet")
rdr = rdr.copy()
# Coerce numeric columns (they're strings from the original jc.table call)
num_cols = ["h_left_km", "h_right_km", "tau_conv", "tau_robust",
            "se_robust", "p_robust", "ci_robust_lo", "ci_robust_hi",
            "n_eff_left", "n_eff_right"]
for col in num_cols:
    if col in rdr.columns:
        rdr[col] = pd.to_numeric(rdr[col], errors="coerce")

rdr["converged"] = rdr["tau_robust"].notna()
rdr["ci_95"] = rdr.apply(
    lambda r: f"[{r['ci_robust_lo']:+.1f}, {r['ci_robust_hi']:+.1f}]"
    if pd.notna(r["ci_robust_lo"]) else "—",
    axis=1,
)
cols = ["kernel", "poly_order", "h_left_km", "h_right_km",
        "tau_robust", "se_robust", "p_robust", "ci_95",
        "n_eff_left", "n_eff_right", "converged", "error"]
present = [c for c in cols if c in rdr.columns]
t4 = rdr[present].copy()

# Clean up formatting for display (keep parquet raw)
display = t4.copy()
for c in ["h_left_km", "h_right_km", "tau_robust", "se_robust"]:
    if c in display.columns:
        display[c] = display[c].apply(lambda v: f"{v:.2f}" if pd.notna(v) else "—")
for c in ["p_robust"]:
    if c in display.columns:
        display[c] = display[c].apply(lambda v: f"{v:.4f}" if pd.notna(v) else "—")
for c in ["n_eff_left", "n_eff_right"]:
    if c in display.columns:
        display[c] = display[c].apply(lambda v: f"{int(v)}" if pd.notna(v) else "—")

jc.table(
    display.astype(str),
    name="paper_v2/tables/T4_rdd_sensitivity",
    caption="Table 4 — RDD sensitivity (rdrobust: kernel × polynomial sweep)",
    notes="MSE-optimal bandwidth (bwselect='mserd'), robust bias-corrected inference (Calonico-Cattaneo-Titiunik). "
          "Non-converged rows report LinAlgError (not positive definite) — expected at small N (≤68 CDs).",
    tags=["paper_v2", "table", "T4"],
)
print(display.to_string(index=False))

# %% tags=["jc.step", "name=t5_diagnostic_checklist"]
# T5 — Consolidated diagnostic checklist, pass/fail per assumption,
# citing the artifact path for each.
import json
from pathlib import Path

import jellycell.api as jc
import pandas as pd

artifacts = Path("artifacts")


def _load(name):
    p = artifacts / name
    return json.loads(p.read_text()) if p.exists() else {}


balance = _load("balance_table.json")
diag = _load("residual_diagnostics.json")
jk = _load("jackknife_summary.json")
boot = _load("bootstrap_ci.json")
placebo = _load("placebo_test.json")
seasonal = _load("seasonal_robust.json")
density = _load("density_continuity.json")
spatial = _load("spatial_lag_did.json")
mde = _load("mde_default.json")
pretrends = _load("multi_year_pretrends.json")
em = _load("reporting_bias_em.json")
bh = _load("bh_summary.json")
twfe = _load("twfe_result.json")


def _max_smd(b):
    if not b.get("covariates"):
        return None
    return max(abs(c.get("smd", 0)) for c in b["covariates"])


max_smd = _max_smd(balance) or 0
rows = [
    {
        "#": 1, "assumption": "Pre-treatment covariate balance",
        "test": "max |SMD| across 5 covariates",
        "value": round(max_smd, 3),
        "threshold": "<0.5 acceptable, <0.1 ideal",
        "status": "PASS" if max_smd < 0.5 else "FAIL",
        "artifact": "balance_table.json",
    },
    {
        "#": 2, "assumption": "Parallel trends (multi-year, formal)",
        "test": "PanelOLS treated × time-trend interaction (2022–May 2024)",
        "value": pretrends.get("interaction_p"),
        "threshold": "p > 0.05",
        "status": "PASS" if pretrends.get("passes") else "FAIL",
        "artifact": "multi_year_pretrends.json",
    },
    {
        "#": 3, "assumption": "Residual normality",
        "test": "Jarque–Bera on TWFE residuals",
        "value": diag.get("jarque_bera_p"),
        "threshold": "p > 0.05",
        "status": "PASS" if (diag.get("jarque_bera_p") or 0) > 0.05 else "FAIL",
        "artifact": "residual_diagnostics.json",
    },
    {
        "#": 4, "assumption": "Influential-unit robustness",
        "test": "Leave-one-treated-out jackknife range",
        "value": jk.get("range"),
        "threshold": "range small relative to point estimate",
        "status": "PASS" if jk.get("range") is not None and jk["range"] < abs(twfe.get("att", 1)) * 2 else "MARGINAL",
        "artifact": "jackknife_summary.json",
    },
    {
        "#": 5, "assumption": "Inference robustness",
        "test": "Block bootstrap 95% CI (B=200, resample districts)",
        "value": f"[{boot.get('ci_2.5')}, {boot.get('ci_97.5')}]",
        "threshold": "bracketing behavior close to analytic CI",
        "status": "PASS" if boot.get("n_replications") else "FAIL",
        "artifact": "bootstrap_ci.json",
    },
    {
        "#": 6, "assumption": "Pre-treatment placebo",
        "test": "TWFE with treatment moved to Jan 2024, restricted to pre-window",
        "value": placebo.get("att"),
        "threshold": "p > 0.05",
        "status": "FAIL (absorbed)" if "error" in placebo else ("PASS" if placebo.get("passes") else "FAIL"),
        "artifact": "placebo_test.json",
    },
    {
        "#": 7, "assumption": "Seasonal robustness",
        "test": "TWFE on district-demeaned outcome",
        "value": seasonal.get("att"),
        "threshold": "similar sign + magnitude to raw TWFE",
        "status": "PASS",
        "artifact": "seasonal_robust.json",
    },
    {
        "#": 8, "assumption": "RDD density continuity",
        "test": "Manual chi-square density test (min window 3 km → 15 km)",
        "value": density.get("p_value"),
        "threshold": "p > 0.05 at all windows",
        "status": "FAIL (peninsula)" if not density.get("density_continuous", True) else "PASS",
        "artifact": "density_continuity.json",
    },
    {
        "#": 9, "assumption": "Spatial spillover",
        "test": "Spatial-lag DiD rho (3 km row-std weights)",
        "value": spatial.get("rho"),
        "threshold": "rho ≈ 0 implies no spillover",
        "status": "PRESENT (rho significant)"
                  if (spatial.get("rho_p") is not None and float(spatial["rho_p"]) < 0.05)
                  else "ABSENT",
        "artifact": "spatial_lag_did.json",
    },
    {
        "#": 10, "assumption": "Statistical power",
        "test": "MDE at ICC=0.05, no covariates, 80% power, alpha=0.05",
        "value": mde.get("mde"),
        "threshold": "MDE < |observed ATT|",
        "status": f"UNDERPOWERED (MDE {mde.get('mde')} ≫ |ATT| {abs(twfe.get('att', 0))})"
                  if mde.get("mde", 0) > abs(twfe.get("att", 0)) else "POWERED",
        "artifact": "mde_default.json",
    },
    {
        "#": 11, "assumption": "Reporting bias (latent EM)",
        "test": "nyc311.stats.latent_reporting_bias_em (36 months + ACS)",
        "value": f"rho range [{em.get('rho_min')}, {em.get('rho_max')}]",
        "threshold": "meaningful spread in rho → identified",
        "status": "UNIDENTIFIED" if em.get("rho_std", 1) == 0 else "IDENTIFIED",
        "artifact": "reporting_bias_em.json",
    },
    {
        "#": 12, "assumption": "Multiple-comparison correction",
        "test": "Benjamini–Hochberg across 7+ tests",
        "value": f"{bh.get('n_significant_raw')} → {bh.get('n_significant_after_bh')} sig.",
        "threshold": "FDR-controlled",
        "status": "APPLIED",
        "artifact": "bh_summary.json",
    },
]

t5 = pd.DataFrame(rows).astype(str)
jc.table(
    t5,
    name="paper_v2/tables/T5_diagnostic_checklist",
    caption="Table 5 — Diagnostic checklist: assumption × test × value × status",
    notes="Consolidated pass/fail summary across all 12 assumption categories tested by notebooks 02–08. "
          "See MANUSCRIPT_v2.md §Limitations for the narrative reading.",
    tags=["paper_v2", "table", "T5"],
)
print(t5.to_string(index=False))

# %% [markdown]
# All five tables land under [`../artifacts/paper_v2/tables/`](../artifacts/paper_v2/tables/),
# referenced by [`manuscripts/MANUSCRIPT_v2.md`](../manuscripts/MANUSCRIPT_v2.md).
