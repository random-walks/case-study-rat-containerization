# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# %% [markdown]
# # 01 — Load + preprocess
#
# Builds the 12-month rodent-complaint panel (Jan–Dec 2024, 68 districts)
# from the vendored Socrata pull. Treatment: Manhattan CDs 01–09 from
# June 2024 (matches upstream `random-walks/nyc311` analysis).

# %% tags=["jc.load", "name=panel"]
import sys
from pathlib import Path
import jellycell.api as jc
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import load_or_build_panel, add_treatment_indicator, load_demographics

panel = add_treatment_indicator(load_or_build_panel())
demo = load_demographics()
units = panel.index.get_level_values("unit_id").unique()
print(f"panel: {panel.shape[0]:,} obs ({len(units)} districts × {panel.shape[0]//len(units)} months)")
print(f"demographics: {len(demo)} districts ({len(set(units) & set(demo.index))} matched)")

summary = {
    "n_districts": int(len(units)),
    "n_periods": int(panel.shape[0] // len(units)),
    "n_observations": int(panel.shape[0]),
    "total_complaints": int(panel["complaint_count"].sum()),
    "treated_units": 9,
    "treatment_date": "2024-06-01",
    "post_treatment_obs": int(panel["treatment"].sum()),
    "demographics_matched": int(len(set(units) & set(demo.index))),
}
jc.save(summary, "artifacts/panel_summary.json", caption="2024 rat-complaint panel summary")

# %% tags=["jc.step", "name=monthly_volume", "deps=panel"]
import sys
from pathlib import Path
import jellycell.api as jc
import pandas as pd
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import load_or_build_panel, add_treatment_indicator

panel = add_treatment_indicator(load_or_build_panel())
monthly = panel.groupby(["treated_unit", "period"])["complaint_count"].mean().unstack("treated_unit")
monthly.columns = ["control_mean", "treated_mean"]
monthly_df = monthly.reset_index()
monthly_df["period"] = monthly_df["period"].astype(str)
jc.table(monthly_df, name="monthly_means_by_group", caption="Mean monthly complaints — treated vs. control districts (2024)")
print(monthly_df.to_string(index=False))

# %% tags=["jc.step", "name=top_districts", "deps=panel"]
import sys
from pathlib import Path
import jellycell.api as jc
import pandas as pd
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import load_or_build_panel

panel = load_or_build_panel()
totals = (
    panel.groupby("unit_id")["complaint_count"].sum()
    .sort_values(ascending=False).head(10).reset_index()
    .rename(columns={"complaint_count": "total_complaints_2024"})
)
jc.table(totals, name="top_10_districts", caption="Top 10 districts by 2024 rodent complaint volume")
print(totals.to_string(index=False))

# %% [markdown]
# **Continue to** [`02_balance_and_pretrends.py`](02_balance_and_pretrends.py)
# — pre-treatment covariate balance + parallel-trends visual.
