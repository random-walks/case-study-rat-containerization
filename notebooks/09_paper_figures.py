# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# %% [markdown]
# # 09 — Paper figures (consolidated)
#
# Re-renders the five paper figures (F1–F5) from §02, §04, §07, §08
# plus an additional Figure 6 (treatment-group attribution heatmap) so
# the manuscript can reference canonical filenames under
# `artifacts/figures/`. Figures F1–F5 were rendered in their
# originating notebooks; this notebook is the **pointer index** used
# by MANUSCRIPT.md.

# %% tags=["jc.step", "name=figure_index"]
import json
from pathlib import Path

import jellycell.api as jc

figures = [
    {"id": "F1", "file": "artifacts/figures/figure-1-pretrends.png",
     "caption": "Mean monthly rodent-complaint volume by group over the full panel window.",
     "source_notebook": "02_balance_and_pretrends.py"},
    {"id": "F2", "file": "artifacts/figures/figure-2-event-study.png",
     "caption": "Event-study coefficients (TWFE, cluster-robust 95% CI).",
     "source_notebook": "04_diagnostics.py"},
    {"id": "F3", "file": "artifacts/figures/figure-3-residual-diagnostics.png",
     "caption": "TWFE residual Q-Q plot and residual-vs-fitted scatter.",
     "source_notebook": "04_diagnostics.py"},
    {"id": "F4", "file": "artifacts/figures/figure-4-spatial-clusters.png",
     "caption": "Spatial pattern of per-CD post-minus-pre complaint change.",
     "source_notebook": "07_rdd_and_spatial.py"},
    {"id": "F5", "file": "artifacts/figures/figure-5-power-curve.png",
     "caption": "Power curve for the headline DiD specification (α = .05).",
     "source_notebook": "08_extended_robustness.py"},
]
present = [f for f in figures if Path(f["file"]).exists()]
jc.save(present, "artifacts/figure_index.json",
        caption=f"{len(present)}/{len(figures)} paper figures on disk.")
print(f"{len(present)}/{len(figures)} figures rendered")

# %% tags=["jc.figure", "name=fig6_att_by_borough"]
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

panel = pd.read_parquet("artifacts/panel_long.parquet").reset_index()
events = json.loads(open("data/rat_mitigation_events_2023.json").read())
TREATED = sorted({e["unit"] for e in events["events"]})
panel["period"] = pd.to_datetime(panel["period"].astype(str))

# Per-CD post-minus-pre change under STAGGERED adoption: each treated CD
# splits at its own event date; never-treated CDs split at the modal
# treatment date (the citywide rollout) as a descriptive reference. The
# pilot-era version of this cell split everything at 2023-07-01 and
# labeled the bars "Pilot CDs" — wrong once the 2024 cohort entered.
event_date = {e["unit"]: pd.Timestamp(e["event_date"]) for e in events["events"]}
modal_onset = pd.Series(list(event_date.values())).mode().iloc[0]

deltas = []
for unit, grp in panel.groupby("unit_id"):
    onset = event_date.get(unit, modal_onset)
    pre_mean = grp.loc[grp["period"] < onset, "complaint_count"].mean()
    post_mean = grp.loc[grp["period"] >= onset, "complaint_count"].mean()
    deltas.append({"unit_id": unit, "delta": post_mean - pre_mean})
delta = pd.DataFrame(deltas)
delta["borough"] = delta["unit_id"].str.split().str[0]
delta["is_treated"] = delta["unit_id"].isin(TREATED)

# Bar plot — per-borough mean delta, treated vs. never-treated.
fig, ax = plt.subplots(figsize=(10, 5))
boroughs = sorted(delta["borough"].unique())
xs = range(len(boroughs))
untreated_means = [delta[(delta["borough"] == b) & (~delta["is_treated"])]["delta"].mean() for b in boroughs]
treated_means = [delta[(delta["borough"] == b) & (delta["is_treated"])]["delta"].mean() if ((delta["borough"] == b) & (delta["is_treated"])).any() else None for b in boroughs]
w = 0.35
ax.bar([x - w / 2 for x in xs], untreated_means, width=w, label="Never-treated CDs", color="#888")
treated_xs = [x + w / 2 for x, v in zip(xs, treated_means) if v is not None]
treated_vals = [v for v in treated_means if v is not None]
ax.bar(treated_xs, treated_vals, width=w, label="Treated CDs (own onset)", color="#c84")
ax.axhline(0, color="black", linewidth=0.5)
ax.set_xticks(list(xs)); ax.set_xticklabels(boroughs, rotation=15)
ax.set_ylabel("Post-minus-pre Δ in mean monthly rodent complaints")
ax.set_title("Figure 6. Mean Δ complaints, by borough, treated vs. never-treated CDs")
ax.legend(loc="upper right", frameon=False)
fig.tight_layout()
Path("artifacts/figures").mkdir(parents=True, exist_ok=True)
fig.savefig("artifacts/figures/figure-6-att-by-borough.png", dpi=150)
plt.close(fig)

from IPython.display import Image
Image("artifacts/figures/figure-6-att-by-borough.png")

# %% [markdown]
# **Next:** `10_paper_tables.py` — reconcile tables T1–T5.
