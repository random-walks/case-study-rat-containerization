# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# %% [markdown]
# # 08 — Power, multi-year trends, reporting bias, multiple-comparison correction
#
# The remaining four diagnostics from
# [`DIAGNOSTICS_CHECKLIST`](../manuscripts/DIAGNOSTICS_CHECKLIST.md):
#
# 1. **MDE power analysis** — what's the smallest effect this design can
#    detect at 80% power?
# 2. **Multi-year parallel-trends test** — using vendored 2022–2024
#    Rodent data (3-year window), formal pre-trend regression
# 3. **Reporting-bias latent EM** — separate true rates from reporting
>    propensities (now plausibly identifiable with 36 months of data)
# 4. **Benjamini-Hochberg correction** — adjust p-values across the
#    full set of hypothesis tests in this showcase

# %% tags=["jc.step", "name=mde_power"]
import sys
from pathlib import Path
import jellycell.api as jc
import pandas as pd
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import load_or_build_panel
from nyc311.stats import minimum_detectable_effect

panel = load_or_build_panel()
n_units = panel.index.get_level_values("unit_id").nunique()
n_periods = panel.index.get_level_values("period").nunique()
outcome_var = float(panel["complaint_count"].var())
proportion_treated = 9 / n_units  # 9 treated / 68 total

# Sweep across reasonable ICC values + R-squared improvements
mde_rows = []
for icc in (0.01, 0.05, 0.10, 0.20):
    for r2 in (0.0, 0.3, 0.6):
        m = minimum_detectable_effect(
            n_units=n_units,
            n_periods=n_periods,
            icc=icc,
            alpha=0.05,
            power=0.8,
            proportion_treated=proportion_treated,
            outcome_variance=outcome_var,
            r_squared=r2,
        )
        mde_rows.append({
            "icc": icc,
            "r_squared": r2,
            "mde": round(float(m.mde), 2),
            "n_units": int(m.n_units),
            "n_periods": int(m.n_periods),
        })
mde_df = pd.DataFrame(mde_rows).astype(str)
jc.table(
    mde_df,
    name="mde_sweep",
    caption="Minimum Detectable Effect — sensitivity to ICC and covariate R²",
    notes="MDE = smallest effect detectable at 80% power, alpha=0.05.",
)
print(mde_df.to_string(index=False))

# Headline number for the "default" ICC = 0.05, no covariates
default = next(r for r in mde_rows if r["icc"] == 0.05 and r["r_squared"] == 0.0)
jc.save(
    {**default, "outcome_variance": round(outcome_var, 2), "proportion_treated": round(proportion_treated, 4)},
    "artifacts/mde_default.json",
    caption=f"MDE at default settings: {default['mde']} complaints (compare to observed ATT)",
)

# %% tags=["jc.load", "name=multi_year_panel"]
import sys
from pathlib import Path
import jellycell.api as jc
import pandas as pd
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import load_or_build_multi_year_panel, add_treatment_indicator

multi = add_treatment_indicator(load_or_build_multi_year_panel())
print(f"  multi-year panel: {multi.shape[0]:,} obs ({multi.index.get_level_values(0).nunique()} units × {multi.index.get_level_values(1).nunique()} months)")
period_str = multi.index.get_level_values("period").astype(str)
print(f"  span: {period_str.min()} → {period_str.max()}")

# %% tags=["jc.step", "name=multi_year_pretrends", "deps=multi_year_panel"]
import sys
from pathlib import Path
import jellycell.api as jc
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import load_or_build_multi_year_panel, add_treatment_indicator

multi = add_treatment_indicator(load_or_build_multi_year_panel())
unit_lvl = multi.index.get_level_values(0)
period_lvl = pd.DatetimeIndex(pd.to_datetime(multi.index.get_level_values(1).astype(str)))
multi = multi.copy()
multi.index = pd.MultiIndex.from_arrays([unit_lvl, period_lvl], names=multi.index.names)

# Restrict to PRE-treatment window only (before June 2024)
pre = multi[period_lvl < pd.Timestamp("2024-06-01")].copy()
# Build a "pre-treatment placebo treatment" — should be ATT ≈ 0 if true
# parallel trends hold across 2022-2024.
treated_set = {f"MANHATTAN 0{i}" for i in range(1, 10)}
pre["treated_unit"] = pre.index.get_level_values(0).isin(treated_set).astype(int)

# Add a linear time trend and the treated × time interaction — significant
# interaction = differential pre-trend = parallel trends violated
pre = pre.reset_index()
pre["time_idx"] = (pre["period"] - pre["period"].min()).dt.days / 30.4
pre["trend_x_treated"] = pre["time_idx"] * pre["treated_unit"]
pre = pre.set_index(["unit_id", "period"])

from linearmodels.panel import PanelOLS
y = pre["complaint_count"]
x = pre[["trend_x_treated"]]
try:
    f = PanelOLS(y, x, entity_effects=True, time_effects=True).fit(cov_type="clustered", cluster_entity=True)
    pretrends = {
        "n_pre_periods": int(period_lvl[period_lvl < pd.Timestamp("2024-06-01")].nunique()),
        "interaction_coef": round(float(f.params["trend_x_treated"]), 4),
        "interaction_se": round(float(f.std_errors["trend_x_treated"]), 4),
        "interaction_p": round(float(f.pvalues["trend_x_treated"]), 4),
        "passes": bool(f.pvalues["trend_x_treated"] > 0.05),
        "interpretation": (
            "PASS — pre-treatment differential trend is statistically zero (parallel trends hold)"
            if f.pvalues["trend_x_treated"] > 0.05 else
            "FAIL — significant pre-treatment trend differential between treated and control"
        ),
    }
except Exception as e:
    pretrends = {"error": f"{type(e).__name__}: {e}"}
jc.save(pretrends, "artifacts/multi_year_pretrends.json", caption="Multi-year parallel-trends test (2022-May 2024 pre-window)")
for k, v in pretrends.items():
    print(f"  {k}: {v}")

# %% tags=["jc.figure", "name=multi_year_trends"]
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import load_or_build_multi_year_panel, add_treatment_indicator

multi = add_treatment_indicator(load_or_build_multi_year_panel())
multi_r = multi.reset_index()
multi_r["period_dt"] = pd.to_datetime(multi_r["period"].astype(str))
gm = multi_r.groupby(["period_dt", "treated_unit"])["complaint_count"].mean().unstack("treated_unit")

fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(gm.index, gm[0], label="Control (mean)", marker="o", color="#1f77b4", linewidth=1.5)
ax.plot(gm.index, gm[1], label="Treated (mean, Manhattan 01-09)", marker="s", color="#d62728", linewidth=1.5)
ax.axvline(pd.Timestamp("2024-06-01"), color="grey", linestyle="--", alpha=0.7, label="Pilot start")
ax.axvline(pd.Timestamp("2024-11-12"), color="grey", linestyle=":", alpha=0.5, label="Citywide enforcement")
ax.set_xlabel("Period")
ax.set_ylabel("Mean monthly complaints / district")
ax.set_title("Multi-year (2022-2024) trends: treated vs. control")
ax.legend()
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig("artifacts/multi_year_trends.png", dpi=110, bbox_inches="tight")
plt.show()

# %% tags=["jc.step", "name=reporting_bias_em"]
import sys
from pathlib import Path
import jellycell.api as jc
import pandas as pd
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import load_or_build_multi_year_panel, load_demographics
from nyc311.stats import latent_reporting_bias_em

multi = load_or_build_multi_year_panel()
demo = load_demographics()

unit_totals = multi.groupby("unit_id")["complaint_count"].sum()
shared = sorted(set(unit_totals.index) & set(demo.index))
complaint_counts = {uid: int(unit_totals[uid]) for uid in shared}
populations = {uid: max(int(demo.loc[uid, "population"]), 1) for uid in shared}
covariates = {
    uid: {
        "pct_nonwhite": float(demo.loc[uid, "pct_nonwhite"]),
        "log_median_income": float(demo.loc[uid, "log_median_income"]),
        "pct_renter": float(demo.loc[uid, "pct_renter"]),
    }
    for uid in shared
}

try:
    em = latent_reporting_bias_em(
        complaint_counts=complaint_counts,
        populations=populations,
        covariates=covariates,
        max_iter=200,
    )
    rho_vals = list(em.reporting_probabilities.values())
    em_summary = {
        "converged": bool(em.converged),
        "n_iterations": int(em.n_iterations),
        "n_units": len(rho_vals),
        "rho_min": round(min(rho_vals), 4),
        "rho_max": round(max(rho_vals), 4),
        "rho_mean": round(sum(rho_vals) / len(rho_vals), 4),
        "rho_std": round(float(pd.Series(rho_vals).std()), 4),
        "interpretation": (
            "Reporting probabilities span a meaningful range — model is identified."
            if (max(rho_vals) - min(rho_vals)) > 0.05 else
            "Reporting probabilities collapse to ~uniform — model is underdetermined "
            "even with 36 months and demographic covariates."
        ),
    }
    jc.save(em_summary, "artifacts/reporting_bias_em.json", caption="Latent reporting-bias EM (multi-year + demographic covariates)")
    for k, v in em_summary.items():
        print(f"  {k}: {v}")
except Exception as e:
    em_summary = {"error": f"{type(e).__name__}: {e}"}
    jc.save(em_summary, "artifacts/reporting_bias_em.json", caption="EM — failed")
    print(f"  EM failed: {e}")

# %% tags=["jc.step", "name=bh_correction"]
import json
import sys
from pathlib import Path
import jellycell.api as jc
import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

# Collect every p-value produced across notebooks 03-08
artifacts = Path("artifacts")
def _load(name):
    p = artifacts / name
    return json.loads(p.read_text()) if p.exists() else {}

twfe = _load("twfe_result.json")
sa = _load("staggered_did.json")
placebo = _load("placebo_test.json")
seasonal = _load("seasonal_robust.json")
spatial = _load("spatial_lag_did.json")
pretrends = _load("multi_year_pretrends.json")
mccrary = _load("mccrary_density.json")

# Pull p-values from RDD sensitivity (multiple bandwidth × poly combos) too
rdd_sens_path = artifacts / "rdd_sensitivity.parquet"
rdd_p_values = []
if rdd_sens_path.exists():
    df = pd.read_parquet(rdd_sens_path)
    if "p_value" in df.columns:
        for v in df["p_value"]:
            try:
                rdd_p_values.append(float(v))
            except (ValueError, TypeError):
                continue

p_records = []
for label, p in [
    ("TWFE main effect", twfe.get("p_value")),
    ("Staggered DiD", sa.get("p_value")),
    ("Placebo (pre-treatment)", placebo.get("p_value")),
    ("Seasonal-demeaned", seasonal.get("p_value")),
    ("Spatial-lag treatment", spatial.get("treatment_p")),
    ("Spatial-lag rho", spatial.get("rho_p")),
    ("Multi-year pretrends", pretrends.get("interaction_p")),
    ("McCrary density", mccrary.get("p_value")),
]:
    if p is not None and isinstance(p, (int, float)) and not (isinstance(p, float) and p != p):
        p_records.append({"test": label, "p_raw": float(p)})
for i, p in enumerate(rdd_p_values):
    if not (isinstance(p, float) and p != p):
        p_records.append({"test": f"RDD bandwidth/poly #{i+1}", "p_raw": float(p)})

if p_records:
    p_arr = np.array([r["p_raw"] for r in p_records])
    reject, p_adj, _, _ = multipletests(p_arr, alpha=0.05, method="fdr_bh")
    for i, r in enumerate(p_records):
        r["p_adj_bh"] = round(float(p_adj[i]), 4)
        r["sig_at_05_after_bh"] = bool(reject[i])
        r["p_raw"] = round(r["p_raw"], 4)

    bh_df = pd.DataFrame(p_records).astype(str)
    jc.table(
        bh_df,
        name="bh_correction",
        caption="Benjamini-Hochberg multiple-comparison correction across all hypothesis tests",
        notes=f"Total tests: {len(p_records)}. Family-wise alpha=0.05.",
    )
    print(bh_df.to_string(index=False))
    n_sig_raw = int(sum(p < 0.05 for p in p_arr))
    n_sig_adj = int(sum(reject))
    jc.save(
        {
            "n_tests": len(p_records),
            "n_significant_raw": n_sig_raw,
            "n_significant_after_bh": n_sig_adj,
            "method": "Benjamini-Hochberg (fdr_bh)",
            "alpha": 0.05,
        },
        "artifacts/bh_summary.json",
        caption=f"BH correction: {n_sig_raw} → {n_sig_adj} significant tests after FDR control",
    )
    print(f"\n  Before BH: {n_sig_raw} significant; After BH: {n_sig_adj} significant")
else:
    print("  no p-values found to correct")

# %% [markdown]
# All seven previously-deferred diagnostics now run. The
# [`DIAGNOSTICS_CHECKLIST`](../manuscripts/DIAGNOSTICS_CHECKLIST.md)
# is updated accordingly; [`MANUSCRIPT.md`](../manuscripts/MANUSCRIPT.md)
# limitations section drops the corresponding bullets.
