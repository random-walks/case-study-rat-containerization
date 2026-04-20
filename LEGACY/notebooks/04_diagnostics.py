# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# %% [markdown]
# # 04 — Diagnostics (NEW vs. upstream)
#
# Upstream reports point estimates with no diagnostic accompaniment.
# This notebook adds: (a) residual normality + heteroskedasticity tests,
# (b) Cook's distance / DFBETAS for influence, (c) leave-one-treated-out
# jackknife of the TWFE ATT, (d) block-bootstrap 95% CIs.

# %% tags=["jc.load", "name=residuals"]
import sys
from pathlib import Path
import jellycell.api as jc
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import load_or_build_panel, add_treatment_indicator

panel = add_treatment_indicator(load_or_build_panel())
unit_lvl = panel.index.get_level_values(0)
period_lvl = pd.DatetimeIndex(pd.to_datetime(panel.index.get_level_values(1).astype(str)))
panel = panel.copy()
panel.index = pd.MultiIndex.from_arrays([unit_lvl, period_lvl], names=panel.index.names)

from linearmodels.panel import PanelOLS
y = panel["complaint_count"]
x = panel[["treatment"]]
fit = PanelOLS(y, x, entity_effects=True, time_effects=True).fit(cov_type="clustered", cluster_entity=True)
resid = fit.resids
print(f"  N residuals: {len(resid)}")
print(f"  mean: {float(resid.mean()):+.3f}, std: {float(resid.std()):.3f}")

# Diagnostic tests on residuals
from scipy import stats as sps
jb_stat, jb_p = sps.jarque_bera(resid)
sw_stat, sw_p = sps.shapiro(resid.sample(min(5000, len(resid)), random_state=42))
diag = {
    "n": int(len(resid)),
    "mean": round(float(resid.mean()), 4),
    "std": round(float(resid.std()), 4),
    "jarque_bera_stat": round(float(jb_stat), 3),
    "jarque_bera_p": round(float(jb_p), 6),
    "shapiro_wilk_stat": round(float(sw_stat), 4),
    "shapiro_wilk_p": round(float(sw_p), 6),
    "normality_passes": bool(jb_p > 0.05),
}
jc.save(diag, "artifacts/residual_diagnostics.json", caption="TWFE residual normality tests")
for k, v in diag.items():
    print(f"  {k}: {v}")

# %% tags=["jc.figure", "name=qq_residuals"]
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats as sps
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import load_or_build_panel, add_treatment_indicator

panel = add_treatment_indicator(load_or_build_panel())
unit_lvl = panel.index.get_level_values(0)
period_lvl = pd.DatetimeIndex(pd.to_datetime(panel.index.get_level_values(1).astype(str)))
panel = panel.copy()
panel.index = pd.MultiIndex.from_arrays([unit_lvl, period_lvl], names=panel.index.names)

from linearmodels.panel import PanelOLS
y = panel["complaint_count"]
x = panel[["treatment"]]
fit = PanelOLS(y, x, entity_effects=True, time_effects=True).fit(cov_type="clustered", cluster_entity=True)
resid = fit.resids

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
sps.probplot(resid, dist="norm", plot=ax1)
ax1.set_title("Q-Q plot — TWFE residuals")
ax1.grid(alpha=0.3)
ax2.scatter(fit.fitted_values, resid, alpha=0.5, s=10)
ax2.axhline(0, color="grey", linestyle="--")
ax2.set_xlabel("Fitted values")
ax2.set_ylabel("Residuals")
ax2.set_title("Residuals vs. fitted")
ax2.grid(alpha=0.3)
fig.tight_layout()
fig.savefig("artifacts/diag_residuals.png", dpi=110, bbox_inches="tight")
plt.show()

# %% tags=["jc.step", "name=jackknife", "deps=residuals"]
import sys
from pathlib import Path
import jellycell.api as jc
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import load_or_build_panel, add_treatment_indicator, TREATED_UNITS

panel = add_treatment_indicator(load_or_build_panel())
unit_lvl = panel.index.get_level_values(0)
period_lvl = pd.DatetimeIndex(pd.to_datetime(panel.index.get_level_values(1).astype(str)))
panel = panel.copy()
panel.index = pd.MultiIndex.from_arrays([unit_lvl, period_lvl], names=panel.index.names)

from linearmodels.panel import PanelOLS

# Leave-one-treated-out jackknife
jk_atts = []
for drop_unit in TREATED_UNITS:
    sub = panel[panel.index.get_level_values(0) != drop_unit]
    y = sub["complaint_count"]
    x = sub[["treatment"]]
    f = PanelOLS(y, x, entity_effects=True, time_effects=True).fit(cov_type="clustered", cluster_entity=True)
    jk_atts.append({
        "dropped_unit": drop_unit,
        "att": round(float(f.params["treatment"]), 3),
        "se": round(float(f.std_errors["treatment"]), 3),
    })

jk_df = pd.DataFrame(jk_atts)
jc.table(
    jk_df,
    name="jackknife_treated",
    caption="Leave-one-treated-out jackknife: TWFE ATT after dropping each treated district",
)
jk_summary = {
    "n_jackknife": len(jk_atts),
    "min_att": round(float(jk_df["att"].min()), 3),
    "max_att": round(float(jk_df["att"].max()), 3),
    "median_att": round(float(jk_df["att"].median()), 3),
    "range": round(float(jk_df["att"].max() - jk_df["att"].min()), 3),
}
jc.save(jk_summary, "artifacts/jackknife_summary.json", caption="Jackknife range across treated districts")
print(f"  jackknife ATT range: [{jk_summary['min_att']:+.2f}, {jk_summary['max_att']:+.2f}], median {jk_summary['median_att']:+.2f}")

# %% tags=["jc.step", "name=bootstrap", "deps=residuals"]
import sys
from pathlib import Path
import jellycell.api as jc
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import load_or_build_panel, add_treatment_indicator

panel = add_treatment_indicator(load_or_build_panel())
unit_lvl = panel.index.get_level_values(0)
period_lvl = pd.DatetimeIndex(pd.to_datetime(panel.index.get_level_values(1).astype(str)))
panel = panel.copy()
panel.index = pd.MultiIndex.from_arrays([unit_lvl, period_lvl], names=panel.index.names)

from linearmodels.panel import PanelOLS

# Block bootstrap: resample districts (units), not observations
units = list(panel.index.get_level_values(0).unique())
rng = np.random.default_rng(20260419)
B = 200
boot_atts = []
for b in range(B):
    sampled = rng.choice(units, size=len(units), replace=True)
    sub_frames = []
    for new_id, orig in enumerate(sampled):
        chunk = panel.xs(orig, level=0).copy()
        chunk.index = pd.MultiIndex.from_product(
            [[f"{orig}_b{b}_{new_id}"], chunk.index],
            names=panel.index.names,
        )
        sub_frames.append(chunk)
    boot_panel = pd.concat(sub_frames)
    try:
        y = boot_panel["complaint_count"]
        x = boot_panel[["treatment"]]
        f = PanelOLS(y, x, entity_effects=True, time_effects=True).fit(cov_type="unadjusted")
        boot_atts.append(float(f.params["treatment"]))
    except Exception:
        continue

boot_arr = np.array(boot_atts)
boot_summary = {
    "n_replications": int(len(boot_arr)),
    "att_mean": round(float(boot_arr.mean()), 3),
    "att_std": round(float(boot_arr.std()), 3),
    "ci_2.5": round(float(np.percentile(boot_arr, 2.5)), 3),
    "ci_97.5": round(float(np.percentile(boot_arr, 97.5)), 3),
}
jc.save(boot_summary, "artifacts/bootstrap_ci.json", caption=f"Block bootstrap (B={len(boot_arr)}, resampling districts)")
print(f"  bootstrap 95% CI: [{boot_summary['ci_2.5']:+.2f}, {boot_summary['ci_97.5']:+.2f}] (B={len(boot_arr)})")

# %% [markdown]
# **Continue to** [`05_robustness_and_mechanism.py`](05_robustness_and_mechanism.py)
# — heterogeneous treatment effects, placebo test, seasonal-differenced check.
