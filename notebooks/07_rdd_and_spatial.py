# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# %% [markdown]
# # 07 — Proper RDD + spatial-lag DiD
#
# Three diagnostics from the [`DIAGNOSTICS_CHECKLIST`](../manuscripts/DIAGNOSTICS_CHECKLIST.md)
# "NOT in this showcase" list, now ported in:
#
# 1. **Local-polynomial RDD** with bandwidth + polynomial sensitivity
#    (running variable: distance from CD centroid to nearest treated-zone centroid)
# 2. **McCrary-style density test** at the cutoff (manipulation check)
# 3. **Spatial-lag DiD** via `nyc311.stats.spatial_lag_model` —
>    accounts for spillover from treated CDs to neighboring untreated ones

# %% tags=["jc.load", "name=centroids"]
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
print(f"  treatment-zone center (mean of {len(treated_centroids)} treated centroids): {zone_center}")
jc.save(
    {"n_centroids": len(centroids), "n_treated": len(treated_centroids), "zone_center": list(zone_center)},
    "artifacts/rdd_geometry.json",
    caption="RDD geometry setup",
)


def _haversine_km(p1, p2):
    lon1, lat1 = math.radians(p1[0]), math.radians(p1[1])
    lon2, lat2 = math.radians(p2[0]), math.radians(p2[1])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(a))

# %% tags=["jc.step", "name=rdd_local_poly", "deps=centroids"]
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
from nyc311.stats import regression_discontinuity

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


# Build RD inputs at CD level: running variable = signed distance to zone center
# Negative inside treated zone, positive outside. Outcome = post-treatment mean complaints.
panel = add_treatment_indicator(load_or_build_panel())
post = panel[panel.index.get_level_values("period").astype(str) >= "2024-06"]
post_means = post.groupby("unit_id")["complaint_count"].mean()

rdd_rows = []
for uid, mean_post in post_means.items():
    if uid not in centroids:
        continue
    d_km = _haversine_km(centroids[uid], zone_center)
    sign = -1.0 if uid in treated_set else +1.0
    rdd_rows.append({"unit_id": uid, "running_var_km": sign * d_km, "outcome": float(mean_post), "treated": uid in treated_set})

rdd_df = pd.DataFrame(rdd_rows).sort_values("running_var_km").reset_index(drop=True)
running = rdd_df["running_var_km"].values
outcome = rdd_df["outcome"].values
print(f"  {len(rdd_df)} CDs in RDD; running var range: [{running.min():.2f}, {running.max():.2f}] km")

# Sensitivity: bandwidth × polynomial-order grid
sens_rows = []
for bw in (3.0, 5.0, 10.0, 15.0):
    for p_order in (1, 2):
        try:
            r = regression_discontinuity(
                running_variable=running,
                outcome=outcome,
                cutoff=0.0,
                bandwidth=bw,
                polynomial_order=p_order,
                kernel="triangular",
            )
            sens_rows.append({
                "bandwidth_km": bw,
                "poly_order": p_order,
                "treatment_effect": round(float(r.treatment_effect), 3),
                "ci_lower": round(float(r.ci_lower), 3),
                "ci_upper": round(float(r.ci_upper), 3),
                "p_value": round(float(r.p_value), 4),
                "n_eff_left": int(r.n_effective_left),
                "n_eff_right": int(r.n_effective_right),
            })
        except Exception as e:
            sens_rows.append({"bandwidth_km": bw, "poly_order": p_order, "error": str(e)[:40]})

sens_df = pd.DataFrame(sens_rows).astype(str)
jc.table(
    sens_df,
    name="rdd_sensitivity",
    caption="RDD sensitivity: treatment effect × bandwidth × polynomial order",
)
print(sens_df.to_string(index=False))
jc.save(
    {"running_var_range": [float(running.min()), float(running.max())], "n_units": len(rdd_df)},
    "artifacts/rdd_summary.json",
    caption="Local-polynomial RDD setup summary",
)

# %% tags=["jc.step", "name=mccrary_density", "deps=centroids"]
import sys
import math
from pathlib import Path
import jellycell.api as jc
import numpy as np
import pandas as pd
from shapely.geometry import shape
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import TREATED_UNITS
from nyc311.geographies import load_nyc_boundaries

# McCrary-style density test: compare density of CDs immediately above vs.
# immediately below the cutoff. Histogram-based Wald-test variant — simpler
# than Cattaneo-Jansson-Ma but works at this small N.
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

distances = []
for uid in centroids:
    sign = -1.0 if uid in treated_set else +1.0
    distances.append(sign * _haversine_km(centroids[uid], zone_center))

distances = np.array(distances)
# Bin into +/- 5 km windows around the cutoff and run a 2-sample t-test
# on bin counts. This is a simplified McCrary — not the full local-poly density
# discontinuity estimator (Cattaneo et al. 2018) but demonstrates the diagnostic.
window = 5.0
left = distances[(distances >= -window) & (distances < 0)]
right = distances[(distances >= 0) & (distances <= window)]
left_count = len(left)
right_count = len(right)
# Density ratio test: under null (no manipulation), the density should be
# continuous; counts should be similar after correcting for window width
total = left_count + right_count
import scipy.stats as sps
# Under continuity (null), expect equal split of the observed total
chisq, p_chi = sps.chisquare(
    [left_count, right_count],
    f_exp=[total / 2, total / 2],
) if total > 0 else (float("nan"), float("nan"))
mccrary = {
    "window_km": window,
    "left_count": int(left_count),
    "right_count": int(right_count),
    "expected_per_side": round(total / 2, 2),
    "chi2_stat": round(float(chisq), 3),
    "p_value": round(float(p_chi), 4),
    "passes": bool(p_chi > 0.05),
    "interpretation": (
        "PASS — running-variable density is continuous at the cutoff (no manipulation)"
        if p_chi > 0.05 else
        "FAIL — density discontinuity at cutoff suggests manipulation of the running variable"
    ),
}
jc.save(mccrary, "artifacts/mccrary_density.json", caption="McCrary-style density continuity test (chi-square variant)")
for k, v in mccrary.items():
    print(f"  {k}: {v}")

# %% tags=["jc.figure", "name=rdd_scatter"]
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

rows = []
for uid, mean_post in post_means.items():
    if uid not in centroids:
        continue
    d_km = _haversine_km(centroids[uid], zone_center)
    sign = -1.0 if uid in treated_set else +1.0
    rows.append((sign * d_km, float(mean_post), uid in treated_set))

xy = np.array([(r[0], r[1]) for r in rows])
treated_mask = np.array([r[2] for r in rows])

fig, ax = plt.subplots(figsize=(10, 5))
ax.scatter(xy[~treated_mask, 0], xy[~treated_mask, 1], s=30, color="#1f77b4", alpha=0.7, label="Control")
ax.scatter(xy[treated_mask, 0], xy[treated_mask, 1], s=40, color="#d62728", alpha=0.8, label="Treated")
ax.axvline(0, color="grey", linestyle="--", alpha=0.7, label="Cutoff (zone boundary)")

# Fit local polynomial (linear) on each side for visualization
left_mask = xy[:, 0] < 0
right_mask = xy[:, 0] >= 0
if left_mask.sum() > 1 and right_mask.sum() > 1:
    for mask, color in ((left_mask, "#d62728"), (right_mask, "#1f77b4")):
        x_side, y_side = xy[mask, 0], xy[mask, 1]
        order = np.argsort(x_side)
        coeffs = np.polyfit(x_side, y_side, deg=1)
        x_plot = np.linspace(x_side.min(), x_side.max(), 50)
        ax.plot(x_plot, np.polyval(coeffs, x_plot), color=color, linewidth=2, alpha=0.6)

ax.set_xlabel("Signed distance to treatment-zone center (km)")
ax.set_ylabel("Mean post-treatment complaints (Jun-Dec 2024)")
ax.set_title("RDD: post-treatment complaints vs. distance to treated zone")
ax.legend()
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig("artifacts/rdd_scatter.png", dpi=110, bbox_inches="tight")
plt.show()

# %% tags=["jc.step", "name=spatial_lag_did", "deps=centroids"]
import sys
import math
from pathlib import Path
import jellycell.api as jc
from shapely.geometry import shape
sys.path.insert(0, str(Path.cwd() / "showcase-rat-containerization"))
from _helpers import TREATED_UNITS, load_or_build_panel_dataset
from nyc311.geographies import load_nyc_boundaries
from nyc311.stats import spatial_lag_model

# Build distance weights (3 km threshold, row-standardized)
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

print(f"  built distance weights for {len(shared)} CDs")
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
            + ("Significant spatial autocorrelation in residuals — neighbor effects matter." if sl.rho_p_value < 0.05 else "No significant residual spatial dependence.")
        ),
    }
    jc.save(spatial_summary, "artifacts/spatial_lag_did.json", caption="Spatial-lag DiD: TWFE + spatial autoregressive residuals")
    for k, v in spatial_summary.items():
        print(f"  {k}: {v}")
except Exception as e:
    fail = {"error": f"{type(e).__name__}: {e}"}
    jc.save(fail, "artifacts/spatial_lag_did.json", caption="Spatial-lag DiD — failed")
    print(f"  spatial_lag_model failed: {e}")

# %% [markdown]
# **Continue to** [`08_extended_robustness.py`](08_extended_robustness.py)
# — power analysis, multi-year parallel-trends, reporting-bias EM, BH correction.
