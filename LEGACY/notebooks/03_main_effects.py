# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# %% [markdown]
# # 03 — Main effects: multi-estimator
#
# Three estimators on the same panel — robustness to specification
# choice (which upstream lacks):
#
# 1. **Two-way fixed effects** — district + month FE, clustered SE
# 2. **Callaway & Sant'Anna staggered DiD** — heterogeneity-robust
# 3. **Synthetic control** — Manhattan 03 vs. weighted donor pool

# %% tags=["jc.load", "name=panel"]
import sys
from pathlib import Path
import jellycell.api as jc
import pandas as pd
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import load_or_build_panel, add_treatment_indicator

panel = add_treatment_indicator(load_or_build_panel())
print(f"  panel: {panel.shape[0]:,} obs")

# %% tags=["jc.step", "name=twfe", "deps=panel"]
import sys
from pathlib import Path
import jellycell.api as jc
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
m = PanelOLS(y, x, entity_effects=True, time_effects=True)
r = m.fit(cov_type="clustered", cluster_entity=True)
twfe = {
    "att": round(float(r.params["treatment"]), 3),
    "se": round(float(r.std_errors["treatment"]), 3),
    "t": round(float(r.tstats["treatment"]), 3),
    "p_value": round(float(r.pvalues["treatment"]), 4),
    "ci_lower": round(float(r.conf_int().loc["treatment", "lower"]), 3),
    "ci_upper": round(float(r.conf_int().loc["treatment", "upper"]), 3),
    "n": int(r.nobs),
    "r_squared": round(float(r.rsquared), 4),
}
jc.save(twfe, "artifacts/twfe_result.json", caption="Two-way FE: complaint_count ~ treatment + district FE + month FE (clustered SE)")
print(f"  TWFE ATT = {twfe['att']:+.2f} (SE = {twfe['se']:.2f}, p = {twfe['p_value']:.4f}, 95% CI [{twfe['ci_lower']:+.2f}, {twfe['ci_upper']:+.2f}])")

# %% tags=["jc.step", "name=staggered_did", "deps=panel"]
import sys
from datetime import date
from pathlib import Path
import jellycell.api as jc
import pandas as pd
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import load_or_build_panel, add_treatment_indicator, TREATED_UNITS, TREATMENT_DATE
from nyc311.stats import staggered_did

panel = add_treatment_indicator(load_or_build_panel())

# Build the inputs: per-unit per-period outcome + treatment-cohort indicator
panel_r = panel.reset_index()
panel_r["period_date"] = pd.to_datetime(panel_r["period"].astype(str)).dt.date
treated_set = set(TREATED_UNITS)
panel_r["treatment_cohort"] = panel_r["unit_id"].apply(
    lambda u: TREATMENT_DATE if u in treated_set else None
)

try:
    sa = staggered_did(
        panel=panel_r,
        unit_col="unit_id",
        time_col="period_date",
        outcome_col="complaint_count",
        treatment_cohort_col="treatment_cohort",
    )
    sa_summary = {
        "att": round(float(sa.aggregated_att), 3),
        "ci_lower": round(float(sa.aggregated_ci_lower), 3),
        "ci_upper": round(float(sa.aggregated_ci_upper), 3),
        "p_value": round(float(sa.aggregated_p_value), 4),
        "n_groups": int(sa.n_groups),
        "n_periods": int(sa.n_periods),
    }
    jc.save(sa_summary, "artifacts/staggered_did.json", caption="Callaway & Sant'Anna staggered DiD")
    print(f"  C&S ATT = {sa_summary['att']:+.2f} (95% CI [{sa_summary['ci_lower']:+.2f}, {sa_summary['ci_upper']:+.2f}], p = {sa_summary['p_value']:.4f})")
except Exception as e:
    sa_summary = {"error": f"{type(e).__name__}: {e}"}
    jc.save(sa_summary, "artifacts/staggered_did.json", caption="Staggered DiD — failed")
    print(f"  staggered_did failed: {e}")

# %% tags=["jc.step", "name=synthetic_control", "deps=panel"]
import sys
from datetime import date
from pathlib import Path
import jellycell.api as jc
import pandas as pd
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import load_or_build_panel, TREATMENT_DATE
from nyc311.stats import synthetic_control

panel = load_or_build_panel()
panel_r = panel.reset_index()
panel_r["period_date"] = pd.to_datetime(panel_r["period"].astype(str)).dt.date

try:
    sc = synthetic_control(
        panel=panel_r,
        unit_col="unit_id",
        time_col="period_date",
        outcome_col="complaint_count",
        treated_unit="MANHATTAN 03",
        treatment_date=TREATMENT_DATE,
    )
    # Top 5 donor weights
    top_donors = sorted(sc.donor_weights.items(), key=lambda kv: kv[1], reverse=True)[:5]
    sc_summary = {
        "treated_unit": "MANHATTAN 03",
        "att": round(float(sc.att), 3),
        "pre_treatment_mspe": round(float(sc.pre_treatment_mspe), 3),
        "n_donors": len(sc.donor_weights),
        "top_donors": [(uid, round(float(w), 3)) for uid, w in top_donors],
    }
    jc.save(sc_summary, "artifacts/synthetic_control.json", caption="Synthetic control: Manhattan 03 vs. donor pool")
    print(f"  SCM ATT = {sc_summary['att']:+.2f} (pre-MSPE = {sc_summary['pre_treatment_mspe']:.2f})")
    print(f"  top donors: {sc_summary['top_donors']}")
except Exception as e:
    sc_summary = {"error": f"{type(e).__name__}: {e}"}
    jc.save(sc_summary, "artifacts/synthetic_control.json", caption="SCM — failed")
    print(f"  synthetic_control failed: {e}")

# %% tags=["jc.step", "name=results_table", "deps=twfe"]
import json
from pathlib import Path
import jellycell.api as jc
import pandas as pd

artifacts = Path("artifacts")
def _load(n):
    p = artifacts / n
    return json.loads(p.read_text()) if p.exists() else {}

twfe = _load("twfe_result.json")
sa = _load("staggered_did.json")
sc = _load("synthetic_control.json")

rows = [
    ("Two-way FE", twfe.get("att"), twfe.get("se"), twfe.get("p_value"), f"[{twfe.get('ci_lower')}, {twfe.get('ci_upper')}]"),
    ("Staggered DiD (C&S)", sa.get("att", "n/a"), "—", sa.get("p_value", "n/a"), f"[{sa.get('ci_lower', 'n/a')}, {sa.get('ci_upper', 'n/a')}]"),
    ("Synthetic control (MN 03)", sc.get("att", "n/a"), "—", "n/a", "n/a"),
]
results_df = pd.DataFrame(rows, columns=["estimator", "att", "se", "p", "ci_95"])
results_df = results_df.astype(str)  # mixed types
jc.table(results_df, name="multi_estimator_results", caption="DiD estimators side-by-side")
print(results_df.to_string(index=False))

# %% [markdown]
# **Continue to** [`04_diagnostics.py`](04_diagnostics.py)
# — residual diagnostics, Cook's distance, jackknife, bootstrap CIs.
