# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# %% [markdown]
# # 02 — Balance + parallel-trends (NEW vs. upstream)
#
# Upstream's analysis reports a pre-trend F-test (F=0.48, p=0.78) but
# **no covariate balance table** between treated and control districts.
# This notebook fills that gap: pre-treatment standardized mean
# differences (SMD) on baseline complaint volume + ACS demographics,
# plus a visual parallel-trends check.

# %% tags=["jc.load", "name=balance"]
import sys
from pathlib import Path
import jellycell.api as jc
import pandas as pd
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import load_or_build_panel, add_treatment_indicator, load_demographics

panel = add_treatment_indicator(load_or_build_panel())
demo = load_demographics()

# Pre-treatment slice (Jan–May 2024, before June 2024 pilot)
periods = pd.to_datetime(panel.index.get_level_values("period").astype(str))
pre_mask = periods < pd.Timestamp("2024-06-01")
pre = panel[pre_mask].reset_index()
unit_means = pre.groupby("unit_id")["complaint_count"].mean().rename("pre_complaints_mean")

# Join demographics
combined = unit_means.to_frame().join(demo, how="inner")
combined["treated"] = combined.index.isin([f"MANHATTAN 0{i}" for i in range(1, 10)]).astype(int)

# Standardized mean difference per covariate
def smd(treated_vals, control_vals):
    import numpy as np
    pooled_sd = ((treated_vals.var() + control_vals.var()) / 2) ** 0.5
    if pooled_sd == 0:
        return 0.0
    return (treated_vals.mean() - control_vals.mean()) / pooled_sd

t = combined[combined["treated"] == 1]
c = combined[combined["treated"] == 0]
covariates = ["pre_complaints_mean", "population", "pct_nonwhite", "log_median_income", "pct_renter"]
balance_rows = []
for cov in covariates:
    if cov in combined.columns and t[cov].notna().any() and c[cov].notna().any():
        balance_rows.append({
            "covariate": cov,
            "treated_mean": round(float(t[cov].mean()), 3),
            "control_mean": round(float(c[cov].mean()), 3),
            "smd": round(float(smd(t[cov].dropna(), c[cov].dropna())), 3),
            "imbalanced": "***" if abs(smd(t[cov].dropna(), c[cov].dropna())) > 0.5 else ("*" if abs(smd(t[cov].dropna(), c[cov].dropna())) > 0.1 else ""),
        })

balance_df = pd.DataFrame(balance_rows)
jc.table(
    balance_df,
    name="pretreatment_balance",
    caption="Pre-treatment covariate balance (treated 9 Manhattan CDs vs. control)",
    notes="|SMD|>0.1 typically flagged as imbalance; |SMD|>0.5 is severe.",
)
print(balance_df.to_string(index=False))
jc.save(
    {"n_treated": int(len(t)), "n_control": int(len(c)), "covariates": balance_rows},
    "artifacts/balance_table.json",
    caption="Pre-treatment SMD balance",
)

# %% tags=["jc.figure", "name=parallel_trends"]
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import load_or_build_panel, add_treatment_indicator

panel = add_treatment_indicator(load_or_build_panel())
panel_r = panel.reset_index()
panel_r["period_dt"] = pd.to_datetime(panel_r["period"].astype(str))
group_means = panel_r.groupby(["period_dt", "treated_unit"])["complaint_count"].mean().unstack("treated_unit")

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(group_means.index, group_means[0], label="Control mean", marker="o", color="#1f77b4")
ax.plot(group_means.index, group_means[1], label="Treated mean", marker="s", color="#d62728")
ax.axvline(pd.Timestamp("2024-06-01"), color="grey", linestyle="--", alpha=0.7, label="Pilot start")
ax.set_xlabel("Period")
ax.set_ylabel("Mean complaints / district / month")
ax.set_title("Parallel-trends visual: treated (Manhattan 01–09) vs. control")
ax.legend()
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig("artifacts/parallel_trends.png", dpi=110, bbox_inches="tight")
plt.show()

# %% [markdown]
# **Continue to** [`03_main_effects.py`](03_main_effects.py)
# — multi-estimator DiD: TWFE + Callaway & Sant'Anna + synthetic control.
