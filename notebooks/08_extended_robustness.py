# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# %% [markdown]
# # 08 — Extended robustness
#
# Two probes:
# 1. **Minimum detectable effect (MDE)** at α = .05, power = .80 for the
#    headline specification — without this number, "significant / not
#    significant" is uninformative.
# 2. **Benjamini-Hochberg correction** across the full set of
#    p-values we report (four DiD estimators × four robustness probes
#    + RDD + Moran's I). Reports whether any claim survives at the
#    5% FDR.

# %% tags=["jc.step", "name=mde_analysis"]
import json

import jellycell.api as jc
import numpy as np
import pandas as pd

panel = pd.read_parquet("artifacts/panel_long.parquet").reset_index()
panel["period"] = pd.to_datetime(panel["period"].astype(str))

# Cell-level SD of the outcome (after within-panel de-meaning) is a
# reasonable MDE-noise proxy for a two-sided test on a DiD coefficient.
y = panel["complaint_count"].to_numpy()
# Crude within-SD (subtract unit + period means).
unit_means = panel.groupby("unit_id")["complaint_count"].transform("mean")
period_means = panel.groupby("period")["complaint_count"].transform("mean")
resid_approx = y - unit_means - period_means + y.mean()
sd = float(resid_approx.std(ddof=1))

import json as _j
rec = _j.loads(open("artifacts/reconciled_findings.json").read())
# Staggered schema: treated = both cohorts (the pre-staggered reconciled
# JSON carried a flat n_treated key; this notebook was never updated).
n_treated = (
    rec["panel"]["cohort_1_pilot"]["n_units"]
    + rec["panel"]["cohort_2_citywide"]["n_units"]
)
n_control = rec["panel"]["n_units"] - n_treated

# Standard two-sample MDE approximation at α = .05 (two-sided), 80% power.
# d = (z_{α/2} + z_β) * sqrt(1/n_t + 1/n_c)
from scipy.stats import norm
z_a = norm.ppf(1 - 0.025)  # 1.96
z_b = norm.ppf(0.80)       # 0.8416
mde_d = (z_a + z_b) * np.sqrt(1 / n_treated + 1 / n_control)
mde_natural = float(mde_d * sd)

payload = {
    "within_residual_sd": sd,
    "n_treated_units": int(n_treated),
    "n_control_units": int(n_control),
    "alpha": 0.05,
    "power": 0.80,
    "mde_cohens_d": float(mde_d),
    "mde_natural_units": mde_natural,
    "observed_att_bjs": rec["cross_estimator"]["bjs"]["att"],
    "observed_abs_att_bjs": abs(rec["cross_estimator"]["bjs"]["att"]),
    "observed_exceeds_mde": abs(rec["cross_estimator"]["bjs"]["att"]) > mde_natural,
    "interpretation": (
        "At α = .05 and 80% power, the smallest detectable ATT is "
        f"{mde_natural:.2f} complaints per CD per month (Cohen's d ~ "
        f"{mde_d:.2f}). The observed |ATT_BJS| = "
        f"{abs(rec['cross_estimator']['bjs']['att']):.2f} does "
        f"{'exceed' if abs(rec['cross_estimator']['bjs']['att']) > mde_natural else 'not exceed'} this floor."
    ),
}
jc.save(payload, "artifacts/mde_analysis.json",
        caption="Minimum detectable effect (MDE) at α = .05, power = .80.")
print(json.dumps(payload, indent=2))

# %% tags=["jc.step", "name=bh_correction"]
import json

import jellycell.api as jc
import pandas as pd
from statsmodels.stats.multitest import multipletests

did = json.loads(open("artifacts/did_results.json").read())
placebo = json.loads(open("artifacts/placebo_did.json").read())
log_out = json.loads(open("artifacts/log_outcome_did.json").read())
pc = json.loads(open("artifacts/post_covid_did.json").read())
mn = json.loads(open("artifacts/manhattan_only_did.json").read())
rdd = json.loads(open("artifacts/rdd_density_sensitivity.json").read())
mi = json.loads(open("artifacts/spatial_morans_i.json").read())

entries = [
    ("main_twfe",          did["twfe"]["p_value"]),
    ("main_cs",            did["cs"]["p_value"]),
    ("main_sa",            did["sa"]["p_value"]),
    ("main_bjs",           did["bjs"]["p_value"]),
    ("placebo_twfe",       placebo["twfe"]["p_value"]),
    ("placebo_cs",         placebo["cs"]["p_value"]),
    ("placebo_sa",         placebo["sa"]["p_value"]),
    ("placebo_bjs",        placebo["bjs"]["p_value"]),
    ("log_outcome",        log_out["p_value"]),
    ("post_covid_bjs",     pc["bjs"]["p_value"]),
    ("mn_only_bjs",        mn["bjs"]["p_value"]),
    ("rdd_conventional",   rdd["p_value"]),
    ("morans_i_perm",      mi["permutation_p_value"]),
]
labels = [e[0] for e in entries]
raw_p = [e[1] for e in entries]
reject, p_bh, _, _ = multipletests(raw_p, method="fdr_bh", alpha=0.05)
rows = [
    {"test": labels[i], "raw_p": float(raw_p[i]),
     "bh_p": float(p_bh[i]), "reject_at_bh_05": bool(reject[i])}
    for i in range(len(labels))
]
payload = {
    "method": "benjamini_hochberg_fdr",
    "alpha": 0.05,
    "n_tests": len(labels),
    "results": rows,
    "n_surviving_bh": int(sum(reject)),
}
jc.save(payload, "artifacts/bh_correction.json",
        caption="Benjamini-Hochberg correction across the full reported test set.")
df = pd.DataFrame(rows)
df["raw_p"] = df["raw_p"].astype(str)
df["bh_p"] = df["bh_p"].astype(str)
jc.table(df, name="bh_correction_table",
         caption="Benjamini-Hochberg FDR correction across all reported *p*-values.")
print(df.to_string(index=False))

# %% tags=["jc.step", "name=power_curve"]
import json

import jellycell.api as jc
import numpy as np
import pandas as pd
from scipy.stats import norm

mde = json.loads(open("artifacts/mde_analysis.json").read())
sd = mde["within_residual_sd"]
n_t = mde["n_treated_units"]; n_c = mde["n_control_units"]
z_a = norm.ppf(0.975)

rows = []
for effect in np.arange(0, 30, 1.0):
    d = effect / sd
    non_centrality = d / np.sqrt(1 / n_t + 1 / n_c)
    power = 1 - norm.cdf(z_a - non_centrality) + norm.cdf(-z_a - non_centrality)
    rows.append({"effect_natural": float(effect), "cohens_d": float(d), "power": float(power)})
df = pd.DataFrame(rows)
jc.save(df.to_dict(orient="records"), "artifacts/power_curve.json",
        caption="Power curve for the headline DiD specification.")
print(df.head(15).to_string(index=False))

# %% tags=["jc.figure", "name=fig5_power_curve"]
from pathlib import Path
import json

import matplotlib.pyplot as plt
import pandas as pd

pc = pd.DataFrame(json.loads(open("artifacts/power_curve.json").read()))
mde = json.loads(open("artifacts/mde_analysis.json").read())
rec = json.loads(open("artifacts/reconciled_findings.json").read())

fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(pc["effect_natural"], pc["power"], color="#333", linewidth=2)
ax.axhline(0.80, color="red", linestyle="--", alpha=0.5, label="Power = 0.80")
ax.axvline(mde["mde_natural_units"], color="orange", linestyle="--", alpha=0.7,
           label=f"MDE = {mde['mde_natural_units']:.1f}")
ax.axvline(abs(rec["cross_estimator"]["bjs"]["att"]), color="green", linestyle="--", alpha=0.8,
           label=f"|Observed BJS ATT| = {abs(rec['cross_estimator']['bjs']['att']):.1f}")
ax.set_xlabel("Effect size (complaints per CD per month)")
ax.set_ylabel("Power")
ax.set_title("Figure 5. Power curve — headline DiD, α = .05")
ax.legend(loc="lower right", frameon=False)
ax.set_ylim(0, 1.02)
fig.tight_layout()
Path("artifacts/figures").mkdir(parents=True, exist_ok=True)
fig.savefig("artifacts/figures/figure-5-power-curve.png", dpi=150)
plt.close(fig)

from IPython.display import Image
Image("artifacts/figures/figure-5-power-curve.png")

# %% [markdown]
# **Next:** `09_paper_figures.py` — consolidate figures; `10_paper_tables.py`
# — consolidate tables.
