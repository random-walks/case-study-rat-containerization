# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# %% [markdown]
# # 07 — Proper RDD (rdrobust) + spatial-lag DiD
#
# Three diagnostics, now using **canonical industry-standard tooling**
# wherever it works:
#
# 1. **`rdrobust`** (Calonico-Cattaneo-Farrell-Titiunik, NSF SES-1357561,
>    SES-1459931, SES-1947805, SES-2019432) — MSE-optimal bandwidth
>    selection (`bwselect='mserd'`), bias-corrected robust confidence
>    intervals, sweeps across kernels and polynomial orders.
> 2. **Manual chi-square density continuity test** at the cutoff (the
>    canonical `rddensity` package is broken on pandas ≥ 2.0 — see
>    [`UPSTREAM_ISSUES.md#008`](../../UPSTREAM_ISSUES.md)).
> 3. **Spatial-lag DiD** via `nyc311.stats.spatial_lag_model` —
>    accounts for spillover from treated CDs to neighboring untreated.
#
# Citations: Calonico, Cattaneo & Titiunik 2014 *Econometrica*; Calonico,
# Cattaneo & Titiunik 2015 *JASA*; Calonico, Cattaneo, Farrell & Titiunik
# 2019 *Review of Economics and Statistics*.

# %% tags=["jc.load", "name=geometry"]
import sys
import math
from pathlib import Path
import jellycell.api as jc
from shapely.geometry import shape
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import TREATED_UNITS
from nyc311.geographies import load_nyc_boundaries

collection = load_nyc_boundaries(layer="community_district")
centroids: dict[str, tuple[float, float]] = {}
for f in collection.features:
    name = f.geography_value
    if name is None or f.geometry is None:
        continue
    centroids[str(name)] = (shape(f.geometry).centroid.x, shape(f.geometry).centroid.y)
treated_set = set(TREATED_UNITS)
treated_centroids = [centroids[u] for u in treated_set if u in centroids]
zone_center = (
    sum(c[0] for c in treated_centroids) / len(treated_centroids),
    sum(c[1] for c in treated_centroids) / len(treated_centroids),
)
print(f"  {len(centroids)} CD centroids loaded")
print(f"  treatment-zone center: {zone_center}")
jc.save(
    {"n_centroids": len(centroids), "n_treated": len(treated_centroids), "zone_center": list(zone_center)},
    "artifacts/rdd_geometry.json",
    caption="RDD geometry setup — centroids + treatment-zone center",
)


def _haversine_km(p1, p2):
    lon1, lat1 = math.radians(p1[0]), math.radians(p1[1])
    lon2, lat2 = math.radians(p2[0]), math.radians(p2[1])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(a))

# %% tags=["jc.step", "name=rdrobust_main", "deps=geometry"]
import sys
import math
from pathlib import Path
import jellycell.api as jc
import numpy as np
import pandas as pd
from shapely.geometry import shape
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import TREATED_UNITS, load_or_build_panel, add_treatment_indicator
from nyc311.geographies import load_nyc_boundaries

# Recompute geometry (cells run independently after cache restore)
collection = load_nyc_boundaries(layer="community_district")
centroids = {}
for f in collection.features:
    if f.geography_value and f.geometry:
        centroids[str(f.geography_value)] = (shape(f.geometry).centroid.x, shape(f.geometry).centroid.y)
treated_set = set(TREATED_UNITS)
treated_centroids = [centroids[u] for u in treated_set if u in centroids]
zone_center = (
    sum(c[0] for c in treated_centroids) / len(treated_centroids),
    sum(c[1] for c in treated_centroids) / len(treated_centroids),
)


def _haversine_km(p1, p2):
    lon1, lat1 = math.radians(p1[0]), math.radians(p1[1])
    lon2, lat2 = math.radians(p2[0]), math.radians(p2[1])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(a))


# Build RDD inputs at CD level: signed distance to treatment-zone center
# (negative inside treated zone, positive outside) + post-treatment mean.
panel = add_treatment_indicator(load_or_build_panel())
post = panel[panel.index.get_level_values("period").astype(str) >= "2024-06"]
post_means = post.groupby("unit_id")["complaint_count"].mean()

rows = []
for uid, mean_post in post_means.items():
    if uid not in centroids:
        continue
    d_km = _haversine_km(centroids[uid], zone_center)
    sign = -1.0 if uid in treated_set else +1.0
    rows.append({"unit_id": uid, "running_var_km": sign * d_km, "outcome": float(mean_post), "treated": uid in treated_set})

rdd_df = pd.DataFrame(rows).sort_values("running_var_km").reset_index(drop=True)
y = rdd_df["outcome"].to_numpy()
x = rdd_df["running_var_km"].to_numpy()
print(f"  {len(rdd_df)} CDs in RDD; running-var range: [{x.min():.2f}, {x.max():.2f}] km")

# Canonical: rdrobust with MSE-optimal bandwidth, triangular kernel,
# polynomial p=1, robust bias-corrected CI (the default).
from rdrobust import rdrobust

main_grid = []
for kernel in ("tri", "epa", "uni"):
    for p_order in (1, 2):
        try:
            r = rdrobust(y, x, c=0.0, p=p_order, kernel=kernel, bwselect="mserd", level=95)
            # rdrobust result: r.coef / r.se / r.pv / r.ci are DataFrames
            # with rows ["Conventional", "Bias-Corrected", "Robust"].
            est = float(r.coef.loc["Conventional"].iloc[0])
            est_rb = float(r.coef.loc["Robust"].iloc[0])
            se_rb = float(r.se.loc["Robust"].iloc[0])
            pv_rb = float(r.pv.loc["Robust"].iloc[0])
            ci_lo = float(r.ci.loc["Robust"].iloc[0])
            ci_hi = float(r.ci.loc["Robust"].iloc[1]) if len(r.ci.loc["Robust"]) > 1 else float(r.ci.loc["Robust"].iloc[0])
            h_left = float(r.bws.iloc[0, 0])
            h_right = float(r.bws.iloc[0, 1])
            main_grid.append({
                "kernel": kernel,
                "poly_order": p_order,
                "bwselect": "mserd",
                "h_left_km": round(h_left, 3),
                "h_right_km": round(h_right, 3),
                "tau_conv": round(est, 3),
                "tau_robust": round(est_rb, 3),
                "se_robust": round(se_rb, 3),
                "p_robust": round(pv_rb, 4),
                "ci_robust_lo": round(ci_lo, 3),
                "ci_robust_hi": round(ci_hi, 3),
                "n_eff_left": int(r.N_h[0]),
                "n_eff_right": int(r.N_h[1]),
            })
        except Exception as e:
            main_grid.append({
                "kernel": kernel,
                "poly_order": p_order,
                "error": f"{type(e).__name__}: {str(e)[:60]}",
            })

main_df = pd.DataFrame(main_grid).astype(str)
jc.table(
    main_df,
    name="rdrobust_sweep",
    caption="rdrobust: kernel × polynomial-order sweep, MSE-optimal bandwidth, robust bias-corrected inference",
)
print(main_df.to_string(index=False))
jc.save(
    {"n_units": len(rdd_df), "running_var_km_range": [float(x.min()), float(x.max())], "package": "rdrobust>=1.3"},
    "artifacts/rdrobust_setup.json",
    caption="rdrobust setup summary",
)

# %% tags=["jc.step", "name=density_continuity", "deps=geometry"]
import sys
import math
from pathlib import Path
import jellycell.api as jc
import numpy as np
import pandas as pd
import scipy.stats as sps
from shapely.geometry import shape
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import TREATED_UNITS
from nyc311.geographies import load_nyc_boundaries

# Manual density continuity test — substitute for rddensity
# (which is broken on pandas 2.x, see UPSTREAM_ISSUES.md #008).
# Chi-square test on density of CDs immediately above vs. below the
# cutoff. Simpler than Cattaneo-Jansson-Ma 2018 but gives a defensible
# pass/fail at our small N (= number of CDs).
collection = load_nyc_boundaries(layer="community_district")
centroids = {}
for f in collection.features:
    if f.geography_value and f.geometry:
        centroids[str(f.geography_value)] = (shape(f.geometry).centroid.x, shape(f.geometry).centroid.y)
treated_set = set(TREATED_UNITS)
treated_centroids = [centroids[u] for u in treated_set if u in centroids]
zone_center = (
    sum(c[0] for c in treated_centroids) / len(treated_centroids),
    sum(c[1] for c in treated_centroids) / len(treated_centroids),
)


def _haversine_km(p1, p2):
    lon1, lat1 = math.radians(p1[0]), math.radians(p1[1])
    lon2, lat2 = math.radians(p2[0]), math.radians(p2[1])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(a))


distances = np.array([
    (-1.0 if uid in treated_set else +1.0) * _haversine_km(centroids[uid], zone_center)
    for uid in centroids
])

# Sweep across windows to see density-continuity behavior at multiple scales
density_rows = []
for window_km in (3.0, 5.0, 10.0, 15.0):
    left = int(((distances >= -window_km) & (distances < 0)).sum())
    right = int(((distances >= 0) & (distances <= window_km)).sum())
    total = left + right
    if total == 0:
        continue
    chi2, p = sps.chisquare([left, right], f_exp=[total / 2, total / 2])
    density_rows.append({
        "window_km": window_km,
        "left_count": left,
        "right_count": right,
        "chi2": round(float(chi2), 3),
        "p_value": round(float(p), 4),
        "density_continuous": bool(p > 0.05),
    })
density_df = pd.DataFrame(density_rows)
jc.table(
    density_df,
    name="density_continuity",
    caption="Manual chi-square density continuity at the cutoff (rddensity substitute pending UPSTREAM_ISSUES.md #008)",
)
print(density_df.to_string(index=False))

# Headline: did the smallest-window test pass or fail?
worst = min(density_rows, key=lambda r: r["p_value"])
jc.save(
    {
        **worst,
        "interpretation": (
            "PASS — running-variable density is continuous at the cutoff at all tested windows"
            if all(r["density_continuous"] for r in density_rows) else
            f"FAIL — density discontinuity flagged at window {worst['window_km']} km (p = {worst['p_value']}). "
            "In our setting this reflects the geographic clustering of treated CDs (peninsula geometry), "
            "not literal manipulation of the running variable. Treat the RDD as complementary to DiD evidence, "
            "not a standalone identification strategy."
        ),
        "note": "Hand-rolled — see UPSTREAM_ISSUES.md #008 for the path to swapping in canonical rddensity once it supports pandas ≥ 2.",
    },
    "artifacts/density_continuity.json",
    caption="Density continuity test summary",
)

# %% tags=["jc.figure", "name=rdrobust_plot"]
import sys
import math
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shapely.geometry import shape
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import TREATED_UNITS, load_or_build_panel, add_treatment_indicator
from nyc311.geographies import load_nyc_boundaries

collection = load_nyc_boundaries(layer="community_district")
centroids = {}
for f in collection.features:
    if f.geography_value and f.geometry:
        centroids[str(f.geography_value)] = (shape(f.geometry).centroid.x, shape(f.geometry).centroid.y)
treated_set = set(TREATED_UNITS)
treated_centroids = [centroids[u] for u in treated_set if u in centroids]
zone_center = (
    sum(c[0] for c in treated_centroids) / len(treated_centroids),
    sum(c[1] for c in treated_centroids) / len(treated_centroids),
)


def _haversine_km(p1, p2):
    lon1, lat1 = math.radians(p1[0]), math.radians(p1[1])
    lon2, lat2 = math.radians(p2[0]), math.radians(p2[1])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(a))


panel = add_treatment_indicator(load_or_build_panel())
post = panel[panel.index.get_level_values("period").astype(str) >= "2024-06"]
post_means = post.groupby("unit_id")["complaint_count"].mean()

xy = []
for uid, m in post_means.items():
    if uid not in centroids:
        continue
    d = (-1.0 if uid in treated_set else +1.0) * _haversine_km(centroids[uid], zone_center)
    xy.append((d, float(m), uid in treated_set))
xy = np.array([(r[0], r[1]) for r in xy])
treated_mask = np.array([r[2] for r in [(d, m, t) for uid, m in post_means.items() if uid in centroids for d, t in [(_haversine_km(centroids[uid], zone_center) * (-1 if uid in treated_set else 1), uid in treated_set)]]])

# Recompute treated mask from xy ordering
treated_mask = np.array([
    uid in treated_set
    for uid in post_means.index if uid in centroids
])

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

# Left panel: scatter with rdrobust-style local-poly fits on each side
ax1.scatter(xy[~treated_mask, 0], xy[~treated_mask, 1], s=30, color="#1f77b4", alpha=0.7, label="Control")
ax1.scatter(xy[treated_mask, 0], xy[treated_mask, 1], s=40, color="#d62728", alpha=0.8, label="Treated")
ax1.axvline(0, color="grey", linestyle="--", alpha=0.7)
left_pts = xy[xy[:, 0] < 0]
right_pts = xy[xy[:, 0] >= 0]
for pts, color in ((left_pts, "#d62728"), (right_pts, "#1f77b4")):
    if len(pts) >= 3:
        coeffs = np.polyfit(pts[:, 0], pts[:, 1], deg=1)
        x_plot = np.linspace(pts[:, 0].min(), pts[:, 0].max(), 50)
        ax1.plot(x_plot, np.polyval(coeffs, x_plot), color=color, linewidth=2, alpha=0.6)
ax1.set_xlabel("Signed distance to treatment-zone center (km)")
ax1.set_ylabel("Mean post-treatment complaints (Jun–Dec 2024)")
ax1.set_title("RDD scatter — local-linear fit each side")
ax1.legend(loc="upper right", fontsize=9)
ax1.grid(alpha=0.3)

# Right panel: density histogram of running variable
all_distances = np.array(xy[:, 0])
bins = np.linspace(all_distances.min(), all_distances.max(), 20)
ax2.hist(all_distances[all_distances < 0], bins=bins, alpha=0.6, color="#d62728", label="Left of cutoff")
ax2.hist(all_distances[all_distances >= 0], bins=bins, alpha=0.6, color="#1f77b4", label="Right of cutoff")
ax2.axvline(0, color="grey", linestyle="--", alpha=0.7)
ax2.set_xlabel("Signed distance to treatment-zone center (km)")
ax2.set_ylabel("CD count")
ax2.set_title("Running-variable density (manipulation diagnostic)")
ax2.legend(loc="upper right", fontsize=9)
ax2.grid(alpha=0.3)

fig.tight_layout()
fig.savefig("artifacts/rdrobust_plot.png", dpi=110, bbox_inches="tight")
plt.show()

# %% tags=["jc.step", "name=spatial_lag_did", "deps=geometry"]
import sys
import math
from pathlib import Path
import jellycell.api as jc
from shapely.geometry import shape
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import TREATED_UNITS, load_or_build_panel_dataset
from nyc311.geographies import load_nyc_boundaries
from nyc311.stats import spatial_lag_model

collection = load_nyc_boundaries(layer="community_district")
centroids = {}
for f in collection.features:
    if f.geography_value and f.geometry:
        centroids[str(f.geography_value)] = (shape(f.geometry).centroid.x, shape(f.geometry).centroid.y)


def _haversine_m(p1, p2):
    lon1, lat1 = math.radians(p1[0]), math.radians(p1[1])
    lon2, lat2 = math.radians(p2[0]), math.radians(p2[1])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(a))


ds = load_or_build_panel_dataset(multi_year=False)
panel_units = sorted({obs.unit_id for obs in ds.observations})
shared = sorted(set(panel_units) & set(centroids))
weights = {}
for ai in shared:
    row = {}
    for aj in shared:
        if ai == aj:
            continue
        if _haversine_m(centroids[ai], centroids[aj]) <= 3000:
            row[aj] = 1.0
    if row:
        total = sum(row.values())
        row = {k: v / total for k, v in row.items()}
    weights[ai] = row

print(f"  built distance weights for {len(shared)} CDs (3 km row-standardized)")
try:
    sl = spatial_lag_model(
        panel=ds,
        weights=weights,
        outcome="complaint_count",
        regressors=("treatment",),
    )
    spatial_summary = {
        "rho": round(float(sl.rho), 4),
        "rho_p": round(float(sl.rho_p_value), 4),
        "treatment_coef": round(float(sl.coefficients.get("treatment", 0)), 3),
        "treatment_p": round(float(sl.p_values.get("treatment", 1)), 4),
        "n_observations": int(sl.n_observations),
        "interpretation": (
            f"Spatial lag rho = {sl.rho:.3f} (p = {sl.rho_p_value:.4f}). "
            + (
                "Significant residual spatial autocorrelation — neighbor effects matter; "
                "the SAR-corrected treatment coefficient is the credible one."
                if sl.rho_p_value < 0.05 else
                "No significant residual spatial dependence — naive TWFE ATT is unbiased by spillover."
            )
        ),
    }
    jc.save(spatial_summary, "artifacts/spatial_lag_did.json", caption="Spatial-lag DiD: TWFE + spatial autoregressive residuals (3 km neighborhoods)")
    for k, v in spatial_summary.items():
        print(f"  {k}: {v}")
except Exception as e:
    fail = {"error": f"{type(e).__name__}: {e}"}
    jc.save(fail, "artifacts/spatial_lag_did.json", caption="Spatial-lag DiD — failed")
    print(f"  spatial_lag_model failed: {e}")

# %% [markdown]
# **Continue to** [`08_extended_robustness.py`](08_extended_robustness.py)
# — power analysis, multi-year parallel-trends, reporting-bias EM, BH correction.
