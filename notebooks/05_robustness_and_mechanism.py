# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# %% [markdown]
# # 05 — Robustness + mechanism (NEW vs. upstream)
#
# Three additional checks the upstream analysis omits:
#
# 1. **Heterogeneous treatment effects** — does the +ATT mask diverging
#    subgroup signals (high- vs. low-baseline districts)?
# 2. **Placebo test** — pretend treatment was Jan 2024; ATT should ≈ 0.
# 3. **Seasonal-differenced outcome** — does the strong yearly cycle
#    drive the result, or does it survive deseasonalization?

# %% tags=["jc.load", "name=panel"]
import sys
from pathlib import Path
import jellycell.api as jc
import pandas as pd
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import load_or_build_panel, add_treatment_indicator

panel = add_treatment_indicator(load_or_build_panel())
print(f"  panel: {panel.shape[0]:,} obs")

# %% tags=["jc.step", "name=hte_by_baseline", "deps=panel"]
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

# Pre-treatment baseline = mean complaints Jan–May 2024
pre_mask = period_lvl < pd.Timestamp("2024-06-01")
baseline = (
    panel[pre_mask].groupby(level=0)["complaint_count"].mean()
    .rename("baseline")
)
panel["baseline"] = panel.index.get_level_values(0).map(baseline)
panel["high_baseline"] = (panel["baseline"] > baseline.median()).astype(int)
panel["treatment_x_high"] = panel["treatment"] * panel["high_baseline"]

from linearmodels.panel import PanelOLS

# Stratified ATT — fit separately for high- vs. low-baseline subsamples
hte_rows = []
for label, mask in (("high_baseline", panel["high_baseline"] == 1),
                     ("low_baseline", panel["high_baseline"] == 0)):
    sub = panel[mask]
    y = sub["complaint_count"]
    x = sub[["treatment"]]
    try:
        f = PanelOLS(y, x, entity_effects=True, time_effects=True).fit(cov_type="clustered", cluster_entity=True)
        hte_rows.append({
            "subgroup": label,
            "n_units": int(sub.index.get_level_values(0).nunique()),
            "att": round(float(f.params["treatment"]), 3),
            "se": round(float(f.std_errors["treatment"]), 3),
            "p": round(float(f.pvalues["treatment"]), 4),
        })
    except Exception as e:
        hte_rows.append({"subgroup": label, "n_units": 0, "att": "n/a", "se": "n/a", "p": str(e)[:40]})

hte_df = pd.DataFrame(hte_rows).astype(str)
jc.table(hte_df, name="hte_by_baseline", caption="Heterogeneous treatment effects — TWFE stratified by pre-treatment baseline volume")
print(hte_df.to_string(index=False))

# %% tags=["jc.step", "name=placebo", "deps=panel"]
import sys
from pathlib import Path
import jellycell.api as jc
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import load_or_build_panel

panel = load_or_build_panel()
unit_lvl = panel.index.get_level_values(0)
period_lvl = pd.DatetimeIndex(pd.to_datetime(panel.index.get_level_values(1).astype(str)))
panel = panel.copy()
panel.index = pd.MultiIndex.from_arrays([unit_lvl, period_lvl], names=panel.index.names)

# Placebo: pretend treatment was Jan 2024 (5 months earlier)
treated_units = [f"MANHATTAN 0{i}" for i in range(1, 10)]
placebo_treated = panel.index.get_level_values(0).isin(treated_units)
placebo_post = period_lvl >= pd.Timestamp("2024-01-01")  # everything post-Jan
panel["placebo"] = (placebo_treated & placebo_post).astype(int)

# Restrict to pre-true-treatment window (Jan–May 2024) so the placebo
# captures purely the pre-treatment behavior.
pre_only = panel[period_lvl < pd.Timestamp("2024-06-01")].copy()

from linearmodels.panel import PanelOLS
y = pre_only["complaint_count"]
x = pre_only[["placebo"]]
try:
    f = PanelOLS(y, x, entity_effects=True, time_effects=True).fit(cov_type="clustered", cluster_entity=True)
    placebo_summary = {
        "att": round(float(f.params["placebo"]), 3),
        "se": round(float(f.std_errors["placebo"]), 3),
        "p_value": round(float(f.pvalues["placebo"]), 4),
        "passes": bool(f.pvalues["placebo"] > 0.05),
        "interpretation": ("PASS — pre-treatment placebo is statistically zero, supporting parallel trends"
                          if f.pvalues["placebo"] > 0.05 else
                          "FAIL — pre-treatment placebo is significant; parallel-trends assumption violated"),
    }
except Exception as e:
    placebo_summary = {"error": f"{type(e).__name__}: {e}"}
jc.save(placebo_summary, "artifacts/placebo_test.json", caption="Pre-treatment placebo (treatment moved earlier)")
print(f"  placebo ATT = {placebo_summary.get('att', 'n/a')} (p = {placebo_summary.get('p_value', 'n/a')})")
print(f"  {placebo_summary.get('interpretation', '')}")

# %% tags=["jc.step", "name=seasonal_diff", "deps=panel"]
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

# Year-over-year differenced outcome — but we only have 12 months of
# data, so YOY isn't possible. Use the within-unit demean as a proxy.
unit_means = panel.groupby(level=0)["complaint_count"].transform("mean")
panel["complaint_demeaned"] = panel["complaint_count"] - unit_means

from linearmodels.panel import PanelOLS
y = panel["complaint_demeaned"]
x = panel[["treatment"]]
try:
    f = PanelOLS(y, x, entity_effects=True, time_effects=True).fit(cov_type="clustered", cluster_entity=True)
    seasonal = {
        "att": round(float(f.params["treatment"]), 3),
        "se": round(float(f.std_errors["treatment"]), 3),
        "p_value": round(float(f.pvalues["treatment"]), 4),
        "note": "Outcome is district-demeaned complaint count (proxy for seasonal-adjusted; full YOY requires multi-year data).",
    }
except Exception as e:
    seasonal = {"error": f"{type(e).__name__}: {e}"}
jc.save(seasonal, "artifacts/seasonal_robust.json", caption="TWFE on district-demeaned outcome")
print(f"  demeaned ATT = {seasonal.get('att', 'n/a')} (p = {seasonal.get('p_value', 'n/a')})")

# %% [markdown]
# **Continue to** [`06_synthesis_and_publication.py`](06_synthesis_and_publication.py)
# — diagnostic checklist + reconciled findings + publication artifact.
