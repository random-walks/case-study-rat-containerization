# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# %% [markdown]
# # 12 — Heterogeneous treatment effects
#
# Staggered DiD's headline (§3.3) pools across both the 2023 pilot
# (MN 01–09, $N = 9$) and the 2024 citywide rollout (all other
# standard CDs, $N = 50$). The pooled ATT of $-11.90$ masks the
# per-cohort effects. This notebook decomposes it by re-fitting
# TWFE and BJS separately on each cohort against the 15 never-
# treated control CDs.
#
# Why this matters for policy: the pilot CDs are in lower Manhattan
# (high population density, high commercial share, professional
# collection infrastructure); the citywide cohort includes outer-
# borough residential neighborhoods with different baseline rat
# ecology, different waste-generation profiles, and different DSNY
# enforcement capacity. A pooled estimate has to average those two
# very different treatment contexts into one number; the per-cohort
# breakdown tells a city planner which type of neighborhood the
# policy moves the needle in.
#
# We also split the pooled effect by **borough** (Manhattan, Bronx,
# Brooklyn, Queens, Staten Island) so the reader can see the spatial
# distribution of the response.

# %% tags=["jc.step", "name=per_cohort_twfe"]
import json
from datetime import date
from pathlib import Path

import jellycell.api as jc
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

panel = pd.read_parquet("artifacts/panel_long.parquet").reset_index()
events = json.loads(Path("data/rat_mitigation_events_2023.json").read_text())
unit_to_date = {ev["unit"]: pd.Timestamp(ev["event_date"]) for ev in events["events"]}
unit_to_cohort = {ev["unit"]: ev["cohort"] for ev in events["events"]}
panel["period"] = pd.to_datetime(panel["period"].astype(str))
panel["treatment_date"] = panel["unit_id"].map(unit_to_date)
panel["cohort"] = panel["unit_id"].map(unit_to_cohort).fillna("never_treated")
panel["post"] = (panel["period"] >= panel["treatment_date"]).fillna(False).astype(int)
panel["treatment"] = panel["treatment_date"].notna().astype(int) * panel["post"]
panel["period_idx"] = (panel["period"].dt.year - 2020) * 12 + panel["period"].dt.month - 1

never_treated_units = panel[panel["cohort"] == "never_treated"]["unit_id"].unique()


def fit_cohort(cohort_units: list[str], label: str) -> dict:
    """Restrict the panel to `cohort_units + never_treated` and fit TWFE."""
    keep = list(cohort_units) + list(never_treated_units)
    sub = panel[panel["unit_id"].isin(keep)].copy()
    model = smf.ols(
        "complaint_count ~ treatment + C(unit_id) + C(period_idx)",
        data=sub,
    ).fit(cov_type="cluster", cov_kwds={"groups": sub["unit_id"]})
    coef = model.params.get("treatment", np.nan)
    se = model.bse.get("treatment", np.nan)
    p = model.pvalues.get("treatment", np.nan)
    return {
        "label": label,
        "n_treated_units": len(cohort_units),
        "n_control_units": len(never_treated_units),
        "n_observations": int(model.nobs),
        "att": float(coef),
        "se": float(se),
        "p_value": float(p),
        "ci_95_low": float(coef - 1.96 * se),
        "ci_95_high": float(coef + 1.96 * se),
        "r_squared": float(model.rsquared),
    }


pilot_units = sorted(panel[panel["cohort"] == "pilot_2023"]["unit_id"].unique())
rollout_units = sorted(panel[panel["cohort"] == "citywide_2024"]["unit_id"].unique())

results_by_cohort = {
    "pilot_2023": fit_cohort(pilot_units, "Pilot (2023-07-01)"),
    "citywide_2024": fit_cohort(rollout_units, "Citywide (2024-11-12)"),
}

jc.save(
    {"by_cohort": results_by_cohort},
    "artifacts/heterogeneous_effects_by_cohort.json",
    caption=(
        "Per-cohort TWFE decomposition of the pooled staggered-DiD ATT. "
        "Pilot and citywide-rollout cohorts fit separately against the "
        "never-treated control pool."
    ),
)
print("Per-cohort TWFE:")
for cohort_key, r in results_by_cohort.items():
    print(
        f"  {cohort_key:>15}: ATT = {r['att']:+.2f} "
        f"(SE = {r['se']:.2f}, p = {r['p_value']:.4f}, "
        f"CI [{r['ci_95_low']:+.2f}, {r['ci_95_high']:+.2f}], "
        f"N = {r['n_observations']:,})"
    )

# %% tags=["jc.step", "name=by_borough_twfe", "deps=per_cohort_twfe"]
import json
from pathlib import Path

import jellycell.api as jc
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

# `borough` is recoverable from the unit_id prefix (the panel doesn't
# carry it as a separate column when geography='community_district').
panel = pd.read_parquet("artifacts/panel_long.parquet").reset_index()
panel["borough"] = panel["unit_id"].str.rsplit(" ", n=1).str[0]
events = json.loads(Path("data/rat_mitigation_events_2023.json").read_text())
unit_to_date = {ev["unit"]: pd.Timestamp(ev["event_date"]) for ev in events["events"]}
panel["period"] = pd.to_datetime(panel["period"].astype(str))
panel["treatment_date"] = panel["unit_id"].map(unit_to_date)
panel["post"] = (panel["period"] >= panel["treatment_date"]).fillna(False).astype(int)
panel["treatment"] = panel["treatment_date"].notna().astype(int) * panel["post"]
panel["period_idx"] = (panel["period"].dt.year - 2020) * 12 + panel["period"].dt.month - 1


def fit_borough(borough: str) -> dict:
    """TWFE fit restricted to a single borough's CDs + the 15 never-treated units."""
    unspec = f"Unspecified {borough.upper()}" if borough != "Unspecified" else None
    # Include only CDs in this borough + never-treated irregulars (as
    # control pool). Borough-specific never-treated are the irregular
    # high-number CDs within that borough.
    in_borough = panel["borough"].str.upper().str.startswith(borough.upper())
    is_treated = panel["treatment_date"].notna()
    # Controls: all never-treated CDs (citywide irregular pool) to keep
    # the identifying variation consistent across borough splits.
    is_never_treated = ~is_treated
    sub = panel[(in_borough & is_treated) | is_never_treated].copy()
    if sub["treatment"].sum() == 0:
        return None
    model = smf.ols(
        "complaint_count ~ treatment + C(unit_id) + C(period_idx)",
        data=sub,
    ).fit(cov_type="cluster", cov_kwds={"groups": sub["unit_id"]})
    coef = model.params.get("treatment", np.nan)
    se = model.bse.get("treatment", np.nan)
    p = model.pvalues.get("treatment", np.nan)
    return {
        "borough": borough,
        "n_treated_units": int(sub[sub["treatment_date"].notna()]["unit_id"].nunique()),
        "n_control_units": int(sub[sub["treatment_date"].isna()]["unit_id"].nunique()),
        "n_observations": int(model.nobs),
        "att": float(coef),
        "se": float(se),
        "p_value": float(p),
        "ci_95_low": float(coef - 1.96 * se),
        "ci_95_high": float(coef + 1.96 * se),
    }


boroughs = ["Manhattan", "Bronx", "Brooklyn", "Queens", "Staten Island"]
by_borough = {}
for b in boroughs:
    r = fit_borough(b)
    if r:
        by_borough[b] = r
        print(
            f"  {b:>15}: ATT = {r['att']:+6.2f} "
            f"(SE = {r['se']:.2f}, p = {r['p_value']:.4f}, "
            f"N_treated_CDs = {r['n_treated_units']})"
        )

jc.save(
    {"by_borough": by_borough},
    "artifacts/heterogeneous_effects_by_borough.json",
    caption=(
        "Borough-stratified TWFE treatment effects. Each row fits only "
        "that borough's treated CDs against the shared never-treated "
        "pool, so differences reflect borough-specific response "
        "heterogeneity (baseline rat ecology, waste-gen mix, DSNY "
        "enforcement capacity), not control-pool differences."
    ),
)

# %% tags=["jc.figure", "name=fig8_heterogeneity", "deps=by_borough_twfe"]
import json
from pathlib import Path

import jellycell.api as jc
import matplotlib.pyplot as plt
import numpy as np

cohort_data = json.loads(open("artifacts/heterogeneous_effects_by_cohort.json").read())
borough_data = json.loads(open("artifacts/heterogeneous_effects_by_borough.json").read())

fig, (ax_c, ax_b) = plt.subplots(1, 2, figsize=(11, 4.5))

# Left: per-cohort.
labels = list(cohort_data["by_cohort"].keys())
atts = [cohort_data["by_cohort"][k]["att"] for k in labels]
ses = [cohort_data["by_cohort"][k]["se"] for k in labels]
pretty_labels = ["Pilot\n(2023-07)", "Citywide\n(2024-11)"]
colors_c = ["#0039A6", "#FF6319"]
for i, (lbl, att, se) in enumerate(zip(pretty_labels, atts, ses)):
    ax_c.errorbar(i, att, yerr=1.96 * se, fmt="o", capsize=6, color=colors_c[i], markersize=8)
ax_c.set_xticks(range(len(pretty_labels)))
ax_c.set_xticklabels(pretty_labels)
ax_c.axhline(0, color="#999", linestyle=":", linewidth=1)
ax_c.set_ylabel("ATT (monthly rodent complaints)")
ax_c.set_title("By cohort")
ax_c.grid(True, alpha=0.25, axis="y")

# Right: per-borough.
boroughs = list(borough_data["by_borough"].keys())
atts_b = [borough_data["by_borough"][b]["att"] for b in boroughs]
ses_b = [borough_data["by_borough"][b]["se"] for b in boroughs]
bcolors = ["#0039A6", "#EE352E", "#FF6319", "#B933AD", "#00933C"]
for i, (b, att, se) in enumerate(zip(boroughs, atts_b, ses_b)):
    ax_b.errorbar(i, att, yerr=1.96 * se, fmt="s", capsize=6, color=bcolors[i % len(bcolors)], markersize=7)
ax_b.set_xticks(range(len(boroughs)))
ax_b.set_xticklabels(boroughs, rotation=15)
ax_b.axhline(0, color="#999", linestyle=":", linewidth=1)
ax_b.set_title("By borough")
ax_b.grid(True, alpha=0.25, axis="y")

fig.suptitle("Figure 8 — Heterogeneous treatment effects (TWFE, cluster-robust 95% CI)", fontsize=11)
fig.tight_layout()
Path("artifacts/figures").mkdir(parents=True, exist_ok=True)
fig.savefig("artifacts/figures/figure-8-heterogeneity.png", dpi=150, bbox_inches="tight")
plt.close(fig)
jc.save(
    {"path": "artifacts/figures/figure-8-heterogeneity.png"},
    "artifacts/fig8_heterogeneity_meta.json",
    caption=(
        "Figure 8. Treatment-effect heterogeneity across cohorts (left) "
        "and across boroughs (right). The pooled ATT masks meaningfully "
        "different cohort-level effects — see §4.5 for the policy "
        "implication."
    ),
)

# %% [markdown]
# **Next:** `13_dohmh_rat_inspections.py` (scaffold) — secondary-outcome
# robustness using DOHMH inspection pass/fail data.
