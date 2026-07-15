# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# %% [markdown]
# # 02 — Balance and parallel trends
#
# Pre-treatment covariate balance (treated vs. control community
# districts) and a parallel-trends visual for the headline monthly
# complaint series. A parallel-trends visual that diverges
# pre-treatment would undermine the identification strategy; a stable
# common slope up to 2023-07-01 is the precondition for the DiD
# headline in notebook 03.

# %% tags=["jc.step", "name=group_means"]
import json
from datetime import date
from pathlib import Path

import jellycell.api as jc
import pandas as pd

panel_df = pd.read_parquet("artifacts/panel_long.parquet")
panel_df = panel_df.reset_index()

# Pull treated-unit list from the hand-curated event file.
events = json.loads(Path("data/rat_mitigation_events_2023.json").read_text())
TREATED = sorted({e["unit"] for e in events["events"]})
TREATMENT_DATE = pd.Timestamp("2023-07-01")

panel_df["period"] = pd.to_datetime(panel_df["period"].astype(str))
panel_df["treated_unit"] = panel_df["unit_id"].isin(TREATED).astype(int)
panel_df["post"] = (panel_df["period"] >= TREATMENT_DATE).astype(int)

pre = panel_df[panel_df["period"] < TREATMENT_DATE]

group_means = (
    pre.groupby("treated_unit")["complaint_count"]
    .agg(["count", "mean", "std", "median"])
    .round(3)
    .reset_index()
    .rename(columns={
        "treated_unit": "group",
        "count": "n_cells",
        "mean": "mean_complaints",
        "std": "sd_complaints",
        "median": "median_complaints",
    })
)
group_means["group"] = group_means["group"].map({0: "control", 1: "treated"})

# Welch t-test on pre-period monthly complaint counts.
from scipy import stats as sps
import numpy as np
pre_t = pre.loc[pre["treated_unit"] == 1, "complaint_count"].to_numpy()
pre_c = pre.loc[pre["treated_unit"] == 0, "complaint_count"].to_numpy()
t_stat, p_val = sps.ttest_ind(pre_t, pre_c, equal_var=False)
pooled_sd = float(np.sqrt((pre_t.var(ddof=1) + pre_c.var(ddof=1)) / 2))
cohens_d = float((pre_t.mean() - pre_c.mean()) / pooled_sd) if pooled_sd > 0 else 0.0

balance = {
    "group_means": group_means.to_dict(orient="records"),
    "welch_t": {
        "t_stat": float(t_stat),
        "p_value": float(p_val),
        "df_welch_approx": int(len(pre_t) + len(pre_c) - 2),
        "cohens_d": cohens_d,
        "n_treated_cells": int(len(pre_t)),
        "n_control_cells": int(len(pre_c)),
    },
}
jc.save(balance, "artifacts/balance_pretreatment.json",
        caption="Pre-treatment balance: treated vs. control monthly rodent-complaint counts (2020-01 → 2023-06)")

# %% tags=["jc.table", "name=balance_table"]
import jellycell.api as jc
import pandas as pd

import json
balance_raw = json.loads(open("artifacts/balance_pretreatment.json").read())
rows = balance_raw["group_means"]
df = pd.DataFrame(rows)[["group", "n_cells", "mean_complaints", "sd_complaints", "median_complaints"]]
# Append Welch row.
w = balance_raw["welch_t"]
summary_rows = [
    {"group": "control",  "n_cells": rows[0]["n_cells"],
     "mean_complaints": rows[0]["mean_complaints"],
     "sd_complaints": rows[0]["sd_complaints"],
     "median_complaints": rows[0]["median_complaints"]},
    {"group": "treated",  "n_cells": rows[1]["n_cells"],
     "mean_complaints": rows[1]["mean_complaints"],
     "sd_complaints": rows[1]["sd_complaints"],
     "median_complaints": rows[1]["median_complaints"]},
    {"group": "Welch t-test", "n_cells": "",
     "mean_complaints": f"t = {w['t_stat']:.2f}",
     "sd_complaints": f"p = {w['p_value']:.4f}",
     "median_complaints": f"Cohen's d = {w['cohens_d']:.3f}"},
]
out = pd.DataFrame(summary_rows)
out = out.astype(str)  # #13 workaround
jc.table(out, name="balance_table",
         caption="Pre-treatment monthly complaint counts, treated vs. control CDs (2020-01 → 2023-06).")

# %% tags=["jc.step", "name=pretrends_series"]
import json
from pathlib import Path

import jellycell.api as jc
import pandas as pd

panel_df = pd.read_parquet("artifacts/panel_long.parquet").reset_index()
events = json.loads(Path("data/rat_mitigation_events_2023.json").read_text())
TREATED = sorted({e["unit"] for e in events["events"]})
panel_df["period"] = pd.to_datetime(panel_df["period"].astype(str))
panel_df["treated_unit"] = panel_df["unit_id"].isin(TREATED).astype(int)

monthly = (
    panel_df.groupby(["treated_unit", "period"])["complaint_count"]
    .mean().unstack(level=0)
    .rename(columns={0: "control_mean", 1: "treated_mean"})
)
monthly.index = monthly.index.astype(str)
window = f"{panel_df['period'].min():%Y-%m} → {panel_df['period'].max():%Y-%m}"
jc.save(monthly.reset_index().to_dict(orient="records"),
        "artifacts/monthly_means_by_group.json",
        caption=f"Mean monthly rodent complaints — treated vs. never-treated CDs, {window}")

# %% tags=["jc.figure", "name=fig1_pretrends"]
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

panel_df = pd.read_parquet("artifacts/panel_long.parquet").reset_index()
events = json.loads(Path("data/rat_mitigation_events_2023.json").read_text())
TREATED = sorted({e["unit"] for e in events["events"]})
panel_df["period"] = pd.to_datetime(panel_df["period"].astype(str))
panel_df["treated_unit"] = panel_df["unit_id"].isin(TREATED).astype(int)

monthly = (
    panel_df.groupby(["treated_unit", "period"])["complaint_count"]
    .mean().unstack(level=0)
)

# Groups, cohort dates, and the window all derive from the data — never
# hard-code them (the pilot-era version of this cell shipped a stale
# "Control (65 CDs)" legend long after the staggered design landed).
n_control = panel_df.loc[panel_df["treated_unit"] == 0, "unit_id"].nunique()
n_treated = panel_df.loc[panel_df["treated_unit"] == 1, "unit_id"].nunique()
cohort_dates = sorted({(e["kind"], e["event_date"]) for e in events["events"]},
                      key=lambda kd: kd[1])

fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(monthly.index, monthly[0],
        label=f"Never-treated ({n_control} irregular CDs)", color="#444", linewidth=1.5)
ax.plot(monthly.index, monthly[1],
        label=f"Treated ({n_treated} CDs, pilot + citywide)", color="#c84", linewidth=1.8)
for (kind, date), style in zip(cohort_dates, ["--", ":"]):
    ax.axvline(pd.Timestamp(date), color="red", linestyle=style, alpha=0.8,
               label=f"{kind.replace('_', ' ').title()} ({date})")
window = f"{monthly.index.min():%Y-%m} through {monthly.index.max():%Y-%m}"
ax.set_xlabel("Month")
ax.set_ylabel("Mean Rodent complaints per CD")
ax.set_title(f"Figure 1. Mean monthly rodent-complaint volume by group, {window}")
ax.legend(loc="upper left", frameon=False)
fig.tight_layout()
Path("artifacts/figures").mkdir(parents=True, exist_ok=True)
fig.savefig("artifacts/figures/figure-1-pretrends.png", dpi=150)
plt.close(fig)

from IPython.display import Image
Image("artifacts/figures/figure-1-pretrends.png")

# %% [markdown]
# **Next:** `03_main_effects.py` — four-estimator DiD on the containerization pilot.
