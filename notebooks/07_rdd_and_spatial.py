# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# %% [markdown]
# # 07 — RDD and spatial
#
# Two auxiliary analyses:
#
# 1. **Sharp RDD on pre-period complaint rate** — a cross-sectional
#    probe of whether CDs clustered just above the median pre-period
#    complaint rate among Manhattan CDs responded differently from
#    those just below. We do *not* claim this is the primary
#    identification (there is no policy-assigned running variable); it
#    is a discontinuity-based sensitivity check reported alongside the
#    DiD headline.
# 2. **Moran's I on the treatment effect** — per-CD post-minus-pre
#    change in complaint rate, mapped onto community-district
#    centroids (derived from the latitude/longitude columns on the
#    underlying service-request records). Tests whether the treatment
#    effect is spatially clustered, i.e., whether neighboring
#    treated-area CDs experienced correlated outcomes.

# %% tags=["jc.step", "name=rdd_density_sensitivity"]
import json
from pathlib import Path

import jellycell.api as jc
import numpy as np
import pandas as pd
from factor_factory.engines.rdd import estimate as rdd_estimate
from factor_factory.tidy import Panel

panel = Panel.from_parquet("artifacts/ff_panel.parquet")
df = panel.to_dataframe().reset_index()
df["period"] = pd.to_datetime(df["period"].astype(str))

# Compute pre-period mean rate per CD → use as running variable.
pre = df[df["period"] < pd.Timestamp("2023-07-01")]
pre_mean = pre.groupby("unit_id")["complaint_count"].mean().rename("pre_mean_rate")
cutoff = float(pre_mean.median())

post = df[df["period"] >= pd.Timestamp("2023-07-01")]
post_mean = post.groupby("unit_id")["complaint_count"].mean().rename("post_mean_rate")
xsec = pd.concat([pre_mean, post_mean], axis=1).dropna().reset_index()
xsec["period"] = pd.Timestamp("2024-01-01")

# Build a degenerate one-period Panel for the RDD engine.
xsec_panel_df = xsec.set_index(["unit_id", "period"])[["post_mean_rate", "pre_mean_rate"]]

# RDD engine expects a Panel — construct via Panel.from_records-like flow
# by manually round-tripping through the ff Panel builder.
from factor_factory.tidy import Panel as FfPanel, PanelMetadata, Provenance
# Simpler: run rdrobust directly.
from rdrobust import rdrobust

# Sharp RDD: outcome = post_mean_rate, running = pre_mean_rate, cutoff = median.
rd = rdrobust(
    y=xsec["post_mean_rate"].to_numpy(),
    x=xsec["pre_mean_rate"].to_numpy(),
    c=cutoff,
    p=1, kernel="triangular", bwselect="mserd",
)
# rdrobust returns a complex object; extract headline.
atte = float(rd.coef.iloc[0, 0])  # conventional
se = float(rd.se.iloc[0, 0])
pval = float(rd.pv.iloc[0, 0])
bw = float(rd.bws.iloc[0, 0])
ci_low = float(rd.ci.iloc[0, 0]); ci_high = float(rd.ci.iloc[0, 1])
n_eff_left = int(rd.N_h[0]); n_eff_right = int(rd.N_h[1])

# Bandwidth sensitivity.
sens = []
for mult, label in ((0.5, "h/2"), (1.0, "h"), (2.0, "2h")):
    rd_h = rdrobust(
        y=xsec["post_mean_rate"].to_numpy(),
        x=xsec["pre_mean_rate"].to_numpy(),
        c=cutoff,
        h=bw * mult, p=1, kernel="triangular",
    )
    sens.append({
        "bandwidth_label": label,
        "bandwidth": float(bw * mult),
        "att": float(rd_h.coef.iloc[0, 0]),
        "se": float(rd_h.se.iloc[0, 0]),
        "p_value": float(rd_h.pv.iloc[0, 0]),
    })

payload = {
    "running_variable": "pre_mean_complaint_rate",
    "cutoff": cutoff,
    "design": "sharp",
    "optimal_bandwidth_mserd": bw,
    "att_conventional": atte,
    "se": se,
    "p_value": pval,
    "ci_95_low": ci_low,
    "ci_95_high": ci_high,
    "n_effective_left": n_eff_left,
    "n_effective_right": n_eff_right,
    "bandwidth_sensitivity": sens,
    "caveat": (
        "No policy-assigned running variable exists. This RDD is a "
        "discontinuity-based sensitivity check — not a primary "
        "identification. Interpret magnitude with caution."
    ),
}
jc.save(payload, "artifacts/rdd_density_sensitivity.json",
        caption="Cross-sectional sharp RDD on pre-period complaint rate; sensitivity check only.")
print(json.dumps(payload, indent=2))

# %% tags=["jc.step", "name=cd_centroids"]
import json
import re
from pathlib import Path

import jellycell.api as jc
import numpy as np
import pandas as pd

from nyc311.io import load_service_requests

# Derive a centroid per CD by averaging lat/lon of the service requests
# attributed to that CD (using the already-cached records).
date_re = re.compile(r"_(\d{4})-\d{2}-\d{2}_(\d{4})-\d{2}-\d{2}_")
records = []
for p in sorted(Path("data/cache").glob("*_rodent_*.csv")):
    if date_re.search(p.name):
        records.extend(load_service_requests(p))

rows = [
    {"unit_id": r.community_district, "lat": r.latitude, "lon": r.longitude}
    for r in records
    if r.community_district and r.latitude is not None and r.longitude is not None
]
df_pts = pd.DataFrame(rows).dropna()
centroids = (
    df_pts.groupby("unit_id")[["lat", "lon"]]
    .median()
    .reset_index()
    .sort_values("unit_id")
)
centroids.to_csv("artifacts/cd_centroids.csv", index=False)
jc.save(centroids.to_dict(orient="records"), "artifacts/cd_centroids.json",
        caption=f"Community-district centroids (median of complaint lat/lon), N = {len(centroids)}.")
print(f"centroids computed for {len(centroids)} community districts")

# %% tags=["jc.step", "name=spatial_morans_i"]
import json
from pathlib import Path

import jellycell.api as jc
import numpy as np
import pandas as pd

panel = pd.read_parquet("artifacts/panel_long.parquet").reset_index()
events = json.loads(open("data/rat_mitigation_events_2023.json").read())
TREATED = sorted({e["unit"] for e in events["events"]})
panel["period"] = pd.to_datetime(panel["period"].astype(str))

pre = panel[panel["period"] < pd.Timestamp("2023-07-01")].groupby("unit_id")["complaint_count"].mean()
post = panel[panel["period"] >= pd.Timestamp("2023-07-01")].groupby("unit_id")["complaint_count"].mean()
effect = (post - pre).rename("effect").reset_index()

centroids = pd.read_csv("artifacts/cd_centroids.csv")
merged = effect.merge(centroids, on="unit_id").dropna()

# Spatial weights: inverse-distance in km, cutoff 10 km.
from math import radians, sin, cos, asin, sqrt

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = radians(lat2 - lat1); dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * asin(sqrt(a))

n = len(merged)
W = np.zeros((n, n))
CUTOFF_KM = 10.0
for i in range(n):
    for j in range(n):
        if i == j: continue
        d = haversine_km(merged.iloc[i]["lat"], merged.iloc[i]["lon"],
                         merged.iloc[j]["lat"], merged.iloc[j]["lon"])
        if 0 < d <= CUTOFF_KM:
            W[i, j] = 1.0 / d
# Row-standardize.
row_sums = W.sum(axis=1, keepdims=True)
row_sums[row_sums == 0] = 1.0
Wr = W / row_sums

x = merged["effect"].to_numpy()
x_dev = x - x.mean()
# Moran's I.
numer = (Wr * np.outer(x_dev, x_dev)).sum()
denom = (x_dev ** 2).sum()
S0 = W.sum()
n_units = n
I = (n_units / S0) * numer / denom if S0 > 0 else np.nan

# Permutation-based p-value.
rng = np.random.default_rng(42)
perms = 999
I_perm = np.empty(perms)
for k in range(perms):
    xp = rng.permutation(x)
    xpd = xp - xp.mean()
    I_perm[k] = (n_units / S0) * (Wr * np.outer(xpd, xpd)).sum() / (xpd ** 2).sum()
p_perm = float((np.abs(I_perm) >= abs(I)).mean())

payload = {
    "morans_I": float(I),
    "expectation_under_null": float(-1 / (n - 1)),
    "permutation_p_value": p_perm,
    "n_permutations": perms,
    "n_units": int(n),
    "distance_cutoff_km": CUTOFF_KM,
    "weight_scheme": "inverse_distance_row_standardized",
    "interpretation": (
        "Moran's *I* measures spatial autocorrelation of the "
        "post-minus-pre complaint-rate change across community-district "
        "centroids. A statistically significant positive *I* indicates "
        "clustered treatment responses (neighbors affected similarly)."
    ),
}
jc.save(payload, "artifacts/spatial_morans_i.json",
        caption="Moran's I on the per-CD post-minus-pre complaint-rate change.")
print(json.dumps(payload, indent=2))

# %% tags=["jc.step", "name=lisa_clusters", "deps=spatial_morans_i"]
import json
from pathlib import Path

import jellycell.api as jc
import numpy as np
import pandas as pd

panel = pd.read_parquet("artifacts/panel_long.parquet").reset_index()
events = json.loads(open("data/rat_mitigation_events_2023.json").read())
TREATED = sorted({e["unit"] for e in events["events"]})
panel["period"] = pd.to_datetime(panel["period"].astype(str))
pre = panel[panel["period"] < pd.Timestamp("2023-07-01")].groupby("unit_id")["complaint_count"].mean()
post = panel[panel["period"] >= pd.Timestamp("2023-07-01")].groupby("unit_id")["complaint_count"].mean()
effect = (post - pre).rename("effect").reset_index()
centroids = pd.read_csv("artifacts/cd_centroids.csv")
merged = effect.merge(centroids, on="unit_id").dropna().reset_index(drop=True)

from math import radians, sin, cos, asin, sqrt
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = radians(lat2 - lat1); dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * asin(sqrt(a))
n = len(merged); W = np.zeros((n, n))
for i in range(n):
    for j in range(n):
        if i == j: continue
        d = haversine_km(merged.iloc[i]["lat"], merged.iloc[i]["lon"],
                         merged.iloc[j]["lat"], merged.iloc[j]["lon"])
        if 0 < d <= 10.0:
            W[i, j] = 1.0 / d
rs = W.sum(axis=1, keepdims=True); rs[rs == 0] = 1.0
Wr = W / rs

x = merged["effect"].to_numpy()
x_z = (x - x.mean()) / x.std(ddof=1)
lag_z = Wr @ x_z
I_local = x_z * lag_z

# Permutation p per unit (simplified; 499 perms for speed).
rng = np.random.default_rng(42)
perms = 499
p_perm = np.empty(n)
for i in range(n):
    neighbors_idx = np.where(Wr[i] > 0)[0]
    if len(neighbors_idx) == 0:
        p_perm[i] = 1.0; continue
    null = []
    for _ in range(perms):
        samp = rng.choice(np.delete(x_z, i), size=len(neighbors_idx), replace=False)
        null.append(x_z[i] * samp.mean() * (Wr[i, neighbors_idx].sum() / Wr[i, neighbors_idx].sum()))
    null = np.asarray(null)
    p_perm[i] = float((np.abs(null) >= abs(I_local[i])).mean())

def classify(zi, lz, p):
    if p > 0.05: return "ns"
    if zi > 0 and lz > 0: return "HH"
    if zi < 0 and lz < 0: return "LL"
    if zi > 0 and lz < 0: return "HL"
    if zi < 0 and lz > 0: return "LH"
    return "ns"

merged["I_local"] = I_local
merged["lag_z"] = lag_z
merged["z"] = x_z
merged["p_perm"] = p_perm
merged["cluster"] = [classify(x_z[i], lag_z[i], p_perm[i]) for i in range(n)]
merged["is_treated"] = merged["unit_id"].isin(TREATED)
merged.to_csv("artifacts/lisa_clusters.csv", index=False)

cluster_counts = merged["cluster"].value_counts().to_dict()
treated_clusters = merged[merged["is_treated"]]["cluster"].value_counts().to_dict()
payload = {
    "cluster_counts_all": cluster_counts,
    "cluster_counts_treated": treated_clusters,
    "n_units": int(n),
    "n_treated": int(merged["is_treated"].sum()),
}
jc.save(payload, "artifacts/lisa_clusters.json",
        caption="LISA cluster classification on treatment-effect surface (10km distance band).")
print(json.dumps(payload, indent=2))

# %% tags=["jc.figure", "name=fig4_spatial_effect"]
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

m = pd.read_csv("artifacts/lisa_clusters.csv")
palette = {"HH": "#c62828", "LL": "#1565c0", "HL": "#ef9a9a", "LH": "#90caf9", "ns": "#cfcfcf"}
fig, ax = plt.subplots(figsize=(8, 9))
for cls, color in palette.items():
    sub = m[m["cluster"] == cls]
    ax.scatter(sub["lon"], sub["lat"], c=color, s=100,
               label=f"{cls} (n={len(sub)})", edgecolor="black", linewidth=0.3)
# Mark treated units with a ring.
t = m[m["is_treated"]]
ax.scatter(t["lon"], t["lat"], facecolors="none", edgecolor="gold",
           s=250, linewidth=2.0, label=f"Treated ({len(t)})")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_title("Figure 4. Spatial pattern of post-minus-pre complaint change, NYC CDs")
ax.legend(loc="lower left", frameon=True, fontsize=9)
ax.set_aspect("equal", adjustable="datalim")
fig.tight_layout()
Path("artifacts/figures").mkdir(parents=True, exist_ok=True)
fig.savefig("artifacts/figures/figure-4-spatial-clusters.png", dpi=150)
plt.close(fig)

from IPython.display import Image
Image("artifacts/figures/figure-4-spatial-clusters.png")

# %% [markdown]
# **Next:** `08_extended_robustness.py` — MDE + Benjamini-Hochberg on
# the full robustness matrix.
