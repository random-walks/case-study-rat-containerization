# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# %% [markdown]
# # 09 — Paper figures (v2)
#
# Produces the five figures for the publication-quality writeup in
# [`manuscripts/MANUSCRIPT_v2.md`](../manuscripts/MANUSCRIPT_v2.md):
#
# 1. **F1 — Treatment timeline.** Gantt-style chart with pilot + citywide enforcement + data window.
# 2. **F2 — Choropleth of ΔATT by CD.** Per-CD pre/post change in mean monthly complaints, treated zone outlined.
# 3. **F3 — Event study.** TWFE with month-from-treatment dummies on the 2022–2024 multi-year panel, with pointwise 95% CIs.
# 4. **F4 — SCM trajectory.** Manhattan 03 observed vs. weighted synthetic counterfactual.
# 5. **F5 — Robustness bar.** ATT point estimates across TWFE / C&S / SCM / jackknife / spatial-lag / RDD.
#
# Figures land under [`../artifacts/paper_v2/figures/`](../artifacts/paper_v2/figures/).
# The companion tables notebook is
# [`10_paper_tables.py`](10_paper_tables.py).

# %% tags=["jc.setup"]
from pathlib import Path

FIG_DIR = Path("artifacts/paper_v2/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)
print(f"  figures → {FIG_DIR}")

# %% tags=["jc.figure", "name=fig_timeline"]
from pathlib import Path

import jellycell.api as jc
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd

# F1 — Treatment timeline. Two rows (pilot + citywide), data window overlaid.
fig, ax = plt.subplots(figsize=(10, 3.2))

# Data window (Jan 2022 – Dec 2024) as a light band across both rows
data_window_start = pd.Timestamp("2022-01-01")
data_window_end = pd.Timestamp("2024-12-31")
ax.axvspan(data_window_start, data_window_end, color="#e7e7e7", alpha=0.6, zorder=0)

# Pilot bar: Manhattan CDs 01–09, Jun 2024 onward
pilot_start = pd.Timestamp("2024-06-01")
pilot_end = pd.Timestamp("2024-12-31")
ax.barh(
    y=1, width=(pilot_end - pilot_start).days, left=pilot_start,
    height=0.55, color="#d62728", alpha=0.85, edgecolor="black", linewidth=0.5,
    label="Pilot enforcement (Manhattan 01–09)",
)

# Citywide bar: all CDs, Nov 12 2024 onward
city_start = pd.Timestamp("2024-11-12")
city_end = pd.Timestamp("2024-12-31")
ax.barh(
    y=0, width=(city_end - city_start).days, left=city_start,
    height=0.55, color="#1f77b4", alpha=0.85, edgecolor="black", linewidth=0.5,
    label="Citywide enforcement (all CDs)",
)

# Annotations
ax.axvline(pilot_start, color="#7f0000", linestyle=":", alpha=0.6)
ax.text(pilot_start, 1.55, " Jun 1, 2024", color="#7f0000", fontsize=9, va="bottom")
ax.axvline(city_start, color="#1c3f60", linestyle=":", alpha=0.6)
ax.text(city_start, 0.55, " Nov 12, 2024", color="#1c3f60", fontsize=9, va="bottom")

ax.set_yticks([0, 1])
ax.set_yticklabels(["Citywide\n(68 CDs)", "Pilot\n(9 CDs)"])
ax.set_xlim(data_window_start - pd.Timedelta(days=30), data_window_end + pd.Timedelta(days=30))
ax.set_ylim(-0.6, 1.9)
ax.set_xlabel("Period")
ax.set_title("Figure 1 — Treatment timeline (data window 2022-01 → 2024-12)")

# Data-window legend patch
dw_patch = mpatches.Patch(color="#e7e7e7", alpha=0.6, label="Data window (2022-01 → 2024-12)")
handles, labels = ax.get_legend_handles_labels()
handles.append(dw_patch)
labels.append(dw_patch.get_label())
ax.legend(handles, labels, loc="upper left", fontsize=8, frameon=True)
ax.grid(axis="x", alpha=0.25)
fig.tight_layout()

out = "artifacts/paper_v2/figures/F1_timeline.png"
jc.figure(
    out,
    fig=fig,
    caption="Figure 1 — Treatment timeline",
    notes="Pilot enforcement (Manhattan CDs 01–09, Jun 2024) + citywide enforcement (all CDs, Nov 12 2024), "
          "with the 2022–2024 data window overlaid.",
    tags=["paper_v2", "figure", "F1"],
)
plt.show()

# %% tags=["jc.step", "name=fit_cs_v2"]
# Refit Callaway & Sant'Anna staggered DiD with the correct API
# (the v1 notebook 03 call uses stale kwargs). We write a v2 JSON so the
# original artifact is untouched.
import sys
from pathlib import Path

import jellycell.api as jc

sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import load_or_build_panel_dataset  # noqa: E402

from nyc311.stats import staggered_did  # noqa: E402

ds = load_or_build_panel_dataset(multi_year=False)
try:
    cs = staggered_did(ds, outcome="complaint_count")
    cs_summary = {
        "att": round(float(cs.aggregated_att), 3),
        "se": round(float(cs.aggregated_se), 3),
        "p_value": round(float(cs.aggregated_p_value), 4),
        "ci_lower": round(float(cs.aggregated_ci_lower), 3),
        "ci_upper": round(float(cs.aggregated_ci_upper), 3),
        "n_groups": int(cs.n_groups),
        "n_periods": int(cs.n_periods),
        "n_group_time_atts": len(cs.group_time_atts),
    }
    print(f"  C&S ATT = {cs_summary['att']:+.2f} (SE {cs_summary['se']:.2f}, "
          f"p {cs_summary['p_value']:.4f}, 95% CI [{cs_summary['ci_lower']:+.2f}, {cs_summary['ci_upper']:+.2f}])")
except Exception as e:
    cs_summary = {"error": f"{type(e).__name__}: {e}"}
    print(f"  staggered_did failed: {e}")

jc.save(
    cs_summary,
    "artifacts/paper_v2/staggered_did_v2.json",
    caption="Callaway & Sant'Anna staggered DiD (corrected signature)",
)

# %% tags=["jc.step", "name=fit_scm_v2"]
# Refit synthetic control with the correct API; persist the full
# observed / counterfactual / periods tuples so F4 can draw the
# trajectory without refitting.
import sys
from pathlib import Path

import jellycell.api as jc

sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import load_or_build_panel_dataset  # noqa: E402

from nyc311.stats import synthetic_control  # noqa: E402

ds = load_or_build_panel_dataset(multi_year=False)
try:
    sc = synthetic_control(ds, treated_unit="MANHATTAN 03", outcome="complaint_count")
    top_donors = sorted(sc.donor_weights.items(), key=lambda kv: kv[1], reverse=True)[:5]
    scm = {
        "treated_unit": sc.treated_unit,
        "att": round(float(sc.att), 3),
        "pre_treatment_mspe": round(float(sc.pre_treatment_mspe), 3),
        "placebo_p_value": sc.placebo_p_value,
        "n_donors": len(sc.donor_weights),
        "top_donors": [(uid, round(float(w), 4)) for uid, w in top_donors],
        "periods": list(sc.periods),
        "observed": [round(float(v), 3) for v in sc.observed],
        "counterfactual": [round(float(v), 3) for v in sc.counterfactual],
        "treatment_effect": [round(float(v), 3) for v in sc.treatment_effect],
    }
    print(f"  SCM ATT = {scm['att']:+.2f} (pre-MSPE {scm['pre_treatment_mspe']:.2f}, "
          f"top donors: {scm['top_donors']})")
except Exception as e:
    scm = {"error": f"{type(e).__name__}: {e}"}
    print(f"  synthetic_control failed: {e}")

jc.save(
    scm,
    "artifacts/paper_v2/scm_trajectory_v2.json",
    caption="Synthetic control trajectory (Manhattan 03 vs. weighted donor pool)",
)

# %% tags=["jc.step", "name=fit_event_study"]
# Event study via TWFE with month-from-treatment dummies on the 2022–2024
# panel. Reference period: τ = −1 (May 2024, immediately pre-pilot). We
# keep the treated dummies separately for each τ ∈ {−12..−2, 0..6} so
# we get per-lead/per-lag coefficients with 95% CIs.
import sys
from pathlib import Path

import jellycell.api as jc
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import TREATED_UNITS, add_treatment_indicator, load_or_build_multi_year_panel  # noqa: E402

panel = add_treatment_indicator(load_or_build_multi_year_panel())
unit_lvl = panel.index.get_level_values(0)
period_lvl = pd.DatetimeIndex(pd.to_datetime(panel.index.get_level_values(1).astype(str)))
panel = panel.copy()
panel.index = pd.MultiIndex.from_arrays([unit_lvl, period_lvl], names=panel.index.names)

# τ = months since June 2024 pilot start (negative = pre)
treatment_ts = pd.Timestamp("2024-06-01")
tau_months = ((period_lvl.year - treatment_ts.year) * 12 + (period_lvl.month - treatment_ts.month)).to_numpy()
treated_set = set(TREATED_UNITS)
is_treated_unit = np.fromiter((u in treated_set for u in unit_lvl), dtype=bool)

# Build τ-specific treated dummies for τ ∈ {−12..+6}, skipping τ = −1 (ref).
tau_range = [t for t in range(-12, 7) if t != -1]
for tau in tau_range:
    name = f"tau_{'m' if tau < 0 else 'p'}{abs(tau):02d}"
    panel[name] = ((tau_months == tau) & is_treated_unit).astype(int)

lead_lag_cols = [f"tau_{'m' if t < 0 else 'p'}{abs(t):02d}" for t in tau_range]

from linearmodels.panel import PanelOLS  # noqa: E402

y = panel["complaint_count"]
X = panel[lead_lag_cols]
fit = PanelOLS(y, X, entity_effects=True, time_effects=True).fit(
    cov_type="clustered", cluster_entity=True,
)

coefs = []
for tau, col in zip(tau_range, lead_lag_cols, strict=True):
    coefs.append({
        "tau": tau,
        "coef": round(float(fit.params[col]), 3),
        "se": round(float(fit.std_errors[col]), 3),
        "ci_lower": round(float(fit.conf_int().loc[col, "lower"]), 3),
        "ci_upper": round(float(fit.conf_int().loc[col, "upper"]), 3),
        "p_value": round(float(fit.pvalues[col]), 4),
    })
# Reference row (τ = −1, coefficient identically 0)
coefs.append({"tau": -1, "coef": 0.0, "se": 0.0, "ci_lower": 0.0, "ci_upper": 0.0, "p_value": None})
coefs = sorted(coefs, key=lambda r: r["tau"])

event_df = pd.DataFrame(coefs)
jc.save(
    event_df,
    "artifacts/paper_v2/event_study_coefs.parquet",
    caption="Event-study coefficients (TWFE with τ-dummies, ref τ=-1, clustered SE)",
)
print(event_df.to_string(index=False))

# %% tags=["jc.step", "name=compute_cd_deltas"]
# Per-CD pre/post change in mean monthly complaints, for the F2 choropleth.
import sys
from pathlib import Path

import jellycell.api as jc
import pandas as pd

sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import TREATED_UNITS, load_or_build_panel  # noqa: E402

panel = load_or_build_panel()
period_str = panel.index.get_level_values("period").astype(str)
pre = panel[period_str < "2024-06"]
post = panel[period_str >= "2024-06"]
pre_mean = pre.groupby(level=0)["complaint_count"].mean().rename("pre_mean")
post_mean = post.groupby(level=0)["complaint_count"].mean().rename("post_mean")
delta = (post_mean - pre_mean).rename("delta")

cd_df = pd.concat([pre_mean, post_mean, delta], axis=1).reset_index()
cd_df["treated"] = cd_df["unit_id"].isin(TREATED_UNITS).astype(int)
cd_df = cd_df.round(3)
jc.save(
    cd_df,
    "artifacts/paper_v2/cd_deltas.parquet",
    caption="Per-CD pre/post mean monthly complaint deltas (Jun 2024 cutoff)",
)
print(cd_df.sort_values("delta").head(5).to_string(index=False))
print("...")
print(cd_df.sort_values("delta").tail(5).to_string(index=False))

# %% tags=["jc.figure", "name=fig_choropleth", "deps=compute_cd_deltas"]
import sys
from pathlib import Path

import jellycell.api as jc
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.cm import ScalarMappable
from matplotlib.colors import TwoSlopeNorm
from shapely.geometry import shape

sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import TREATED_UNITS  # noqa: E402

from nyc311.geographies import load_nyc_boundaries  # noqa: E402

cd_df = pd.read_parquet("artifacts/paper_v2/cd_deltas.parquet").set_index("unit_id")
collection = load_nyc_boundaries(layer="community_district")

fig, ax = plt.subplots(figsize=(8.5, 9))
deltas = cd_df["delta"].to_numpy()
abs_max = float(max(abs(deltas.min()), abs(deltas.max())))
norm = TwoSlopeNorm(vmin=-abs_max, vcenter=0.0, vmax=abs_max)
cmap = plt.get_cmap("RdBu_r")

treated_set = set(TREATED_UNITS)
for feature in collection.features:
    uid = feature.geography_value
    if uid is None or feature.geometry is None:
        continue
    geom = shape(feature.geometry)
    row = cd_df.loc[uid] if uid in cd_df.index else None
    face = cmap(norm(float(row["delta"]))) if row is not None else "#dddddd"
    edge = "#111111" if uid in treated_set else "#666666"
    lw = 2.0 if uid in treated_set else 0.5
    if geom.geom_type == "Polygon":
        xs, ys = geom.exterior.xy
        ax.fill(xs, ys, color=face, edgecolor=edge, linewidth=lw)
    else:  # MultiPolygon
        for poly in geom.geoms:
            xs, ys = poly.exterior.xy
            ax.fill(xs, ys, color=face, edgecolor=edge, linewidth=lw)

ax.set_aspect("equal")
ax.set_xticks([])
ax.set_yticks([])
for spine in ax.spines.values():
    spine.set_visible(False)
ax.set_title("Figure 2 — Δ mean monthly complaints by community district\n(post − pre Jun 2024; treated zone outlined)")

sm = ScalarMappable(norm=norm, cmap=cmap)
sm.set_array(np.array([]))
cbar = fig.colorbar(sm, ax=ax, shrink=0.55, pad=0.02)
cbar.set_label("Δ complaints / district / month")
fig.tight_layout()

out = "artifacts/paper_v2/figures/F2_choropleth.png"
jc.figure(
    out,
    fig=fig,
    caption="Figure 2 — Per-CD Δ mean monthly complaints, pre vs. post Jun 2024 pilot",
    notes="Red = increase, blue = decrease. Treated CDs (Manhattan 01–09) outlined in black. "
          "CDs missing from the panel join are drawn in gray.",
    tags=["paper_v2", "figure", "F2"],
)
plt.show()

# %% tags=["jc.figure", "name=fig_event_study", "deps=fit_event_study"]
import jellycell.api as jc
import matplotlib.pyplot as plt
import pandas as pd

event_df = pd.read_parquet("artifacts/paper_v2/event_study_coefs.parquet").sort_values("tau")

fig, ax = plt.subplots(figsize=(10, 5))
taus = event_df["tau"].to_numpy()
coefs = event_df["coef"].to_numpy()
ci_lo = event_df["ci_lower"].to_numpy()
ci_hi = event_df["ci_upper"].to_numpy()

pre_mask = taus < 0
post_mask = taus >= 0

# Shade pre-treatment region
ax.axvspan(taus.min() - 0.5, -0.5, color="#eaeaea", alpha=0.6, zorder=0, label="Pre-treatment")
ax.axhline(0, color="black", linewidth=0.8)
ax.axvline(-0.5, color="#d62728", linestyle="--", alpha=0.6, label="Pilot (τ=0)")

# Coefficients + CIs
ax.vlines(taus[pre_mask], ci_lo[pre_mask], ci_hi[pre_mask], color="#1f77b4", alpha=0.85, linewidth=1.5)
ax.scatter(taus[pre_mask], coefs[pre_mask], color="#1f77b4", s=40, zorder=3, label="Pre leads")
ax.vlines(taus[post_mask], ci_lo[post_mask], ci_hi[post_mask], color="#d62728", alpha=0.85, linewidth=1.5)
ax.scatter(taus[post_mask], coefs[post_mask], color="#d62728", s=40, zorder=3, label="Post lags")

ax.set_xticks(range(int(taus.min()), int(taus.max()) + 1, 2))
ax.set_xlabel("Months from pilot (τ); τ=-1 is the reference period (May 2024)")
ax.set_ylabel("TWFE coefficient (complaints / district / month)")
ax.set_title("Figure 3 — Event study: leads (τ=-12 … -2) and lags (τ=0 … +6)")
ax.legend(loc="upper left", fontsize=9)
ax.grid(alpha=0.3)
fig.tight_layout()

out = "artifacts/paper_v2/figures/F3_event_study.png"
jc.figure(
    out,
    fig=fig,
    caption="Figure 3 — Event study with pre-treatment leads and post-treatment lags (TWFE, clustered SE)",
    notes="Reference period τ=-1 (May 2024). Whiskers: pointwise 95% analytic CI. "
          "Non-zero pre-treatment leads flag a parallel-trends concern; consistent with the multi-year pretrend test failure (p≈0.05).",
    tags=["paper_v2", "figure", "F3"],
)
plt.show()

# %% tags=["jc.figure", "name=fig_scm_trajectory", "deps=fit_scm_v2"]
import json
from pathlib import Path

import jellycell.api as jc
import matplotlib.pyplot as plt
import pandas as pd

scm = json.loads(Path("artifacts/paper_v2/scm_trajectory_v2.json").read_text())

fig, ax = plt.subplots(figsize=(10, 5))
if "error" in scm:
    ax.text(0.5, 0.5, f"SCM fit failed:\n{scm['error']}",
            ha="center", va="center", fontsize=10, transform=ax.transAxes)
    ax.set_axis_off()
else:
    periods = pd.to_datetime(scm["periods"])
    observed = scm["observed"]
    counterfactual = scm["counterfactual"]
    ax.plot(periods, observed, marker="o", color="#d62728", linewidth=2,
            label=f"Observed ({scm['treated_unit']})")
    ax.plot(periods, counterfactual, marker="s", color="#1f77b4", linewidth=2,
            linestyle="--", label="Synthetic counterfactual")
    ax.axvline(pd.Timestamp("2024-06-01"), color="grey", linestyle=":", alpha=0.8, label="Pilot start")
    ax.fill_between(
        periods, observed, counterfactual,
        where=periods >= pd.Timestamp("2024-06-01"),
        alpha=0.18, color="#888888", label="Treatment gap",
    )
    ax.set_xlabel("Period")
    ax.set_ylabel("Monthly complaints")
    ax.set_title(
        f"Figure 4 — Synthetic control: {scm['treated_unit']} vs. weighted donor pool "
        f"(ATT = {scm['att']:+.2f}, pre-MSPE = {scm['pre_treatment_mspe']:.2f})"
    )
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(alpha=0.3)
fig.tight_layout()

out = "artifacts/paper_v2/figures/F4_scm_trajectory.png"
jc.figure(
    out,
    fig=fig,
    caption="Figure 4 — Synthetic control trajectory for Manhattan 03",
    notes="Observed complaint counts (red) vs. the weighted donor counterfactual (blue). "
          "Shaded region marks the post-treatment gap.",
    tags=["paper_v2", "figure", "F4"],
)
plt.show()

# %% tags=["jc.figure", "name=fig_robustness_bar", "deps=fit_scm_v2"]
import json
from pathlib import Path

import jellycell.api as jc
import matplotlib.pyplot as plt
import pandas as pd

artifacts = Path("artifacts")

def _load(name):
    p = artifacts / name
    return json.loads(p.read_text()) if p.exists() else {}

twfe = _load("twfe_result.json")
cs = _load("paper_v2/staggered_did_v2.json")
scm = _load("paper_v2/scm_trajectory_v2.json")
spatial = _load("spatial_lag_did.json")
jk = _load("jackknife_summary.json")

# RDD: take the "triangular kernel, p=1" row — the canonical rdrobust default
rdr = pd.read_parquet("artifacts/rdrobust_sweep.parquet")
rdr["tau_robust_num"] = pd.to_numeric(rdr["tau_robust"], errors="coerce")
rdr["ci_lo_num"] = pd.to_numeric(rdr["ci_robust_lo"], errors="coerce")
rdr["ci_hi_num"] = pd.to_numeric(rdr["ci_robust_hi"], errors="coerce")
rdr_default = rdr.query("kernel == 'tri' and poly_order == '1'").iloc[0]
rdd_att = float(rdr_default["tau_robust_num"])
rdd_ci = (float(rdr_default["ci_lo_num"]), float(rdr_default["ci_hi_num"]))

rows = []
rows.append({"estimator": "TWFE", "att": float(twfe.get("att", 0)),
             "ci_lo": float(twfe.get("ci_lower", 0)), "ci_hi": float(twfe.get("ci_upper", 0))})
if "att" in cs and not isinstance(cs.get("att"), str):
    rows.append({"estimator": "C&S (staggered)",
                 "att": float(cs["att"]),
                 "ci_lo": float(cs["ci_lower"]), "ci_hi": float(cs["ci_upper"])})
if "att" in scm and not isinstance(scm.get("att"), str):
    # SCM has no analytic CI; we leave whiskers as 0 and flag this in the caption.
    rows.append({"estimator": "SCM (MN 03)", "att": float(scm["att"]), "ci_lo": float(scm["att"]),
                 "ci_hi": float(scm["att"])})
rows.append({"estimator": "Jackknife low", "att": float(jk.get("min_att", 0)),
             "ci_lo": float(jk.get("min_att", 0)), "ci_hi": float(jk.get("min_att", 0))})
rows.append({"estimator": "Jackknife median", "att": float(jk.get("median_att", 0)),
             "ci_lo": float(jk.get("median_att", 0)), "ci_hi": float(jk.get("median_att", 0))})
rows.append({"estimator": "Jackknife high", "att": float(jk.get("max_att", 0)),
             "ci_lo": float(jk.get("max_att", 0)), "ci_hi": float(jk.get("max_att", 0))})
rows.append({"estimator": "Spatial-lag", "att": float(spatial.get("treatment_coef", 0)),
             "ci_lo": float(spatial.get("treatment_coef", 0)),
             "ci_hi": float(spatial.get("treatment_coef", 0))})
rows.append({"estimator": "RDD (tri, p=1)", "att": rdd_att, "ci_lo": rdd_ci[0], "ci_hi": rdd_ci[1]})

robust_df = pd.DataFrame(rows)
jc.save(robust_df, "artifacts/paper_v2/robustness_bar.parquet",
        caption="Robustness bar — per-estimator ATT point estimates + (where available) 95% CIs")

fig, ax = plt.subplots(figsize=(10, 5))
y_pos = list(range(len(robust_df)))
ax.barh(y_pos, robust_df["att"], color="#4c78a8", alpha=0.75, edgecolor="black", linewidth=0.5)

# Whiskers only where CI is meaningful (non-degenerate)
for i, row in robust_df.iterrows():
    if row["ci_lo"] != row["ci_hi"]:
        ax.plot([row["ci_lo"], row["ci_hi"]], [i, i], color="black", linewidth=1.5)
        ax.plot([row["ci_lo"], row["ci_lo"]], [i - 0.15, i + 0.15], color="black", linewidth=1.5)
        ax.plot([row["ci_hi"], row["ci_hi"]], [i - 0.15, i + 0.15], color="black", linewidth=1.5)

ax.axvline(0, color="#d62728", linewidth=1, linestyle="--", alpha=0.7)
ax.set_yticks(y_pos)
ax.set_yticklabels(robust_df["estimator"])
ax.set_xlabel("ATT estimate (complaints / district / month)")
ax.set_title("Figure 5 — Robustness: ATT across estimators")
ax.grid(axis="x", alpha=0.3)
ax.invert_yaxis()
fig.tight_layout()

out = "artifacts/paper_v2/figures/F5_robustness.png"
jc.figure(
    out,
    fig=fig,
    caption="Figure 5 — ATT point estimates across estimators and subsamples",
    notes="Whiskers: 95% CI where available. Jackknife low/median/high are point estimates only. "
          "SCM's placebo p-value (not plotted) is in scm_trajectory_v2.json.",
    tags=["paper_v2", "figure", "F5"],
)
plt.show()

# %% [markdown]
# **Continue to** [`10_paper_tables.py`](10_paper_tables.py)
# — publication-grade tables (descriptive stats, main results, HTE,
# RDD sensitivity, diagnostic checklist).
