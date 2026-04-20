# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# %% [markdown]
# # 03 — Main effects (four-estimator DiD)
#
# Runs TWFE, Callaway-Sant'Anna (CS), Sun-Abraham (SA), and
# Borusyak-Jaravel-Spiess (BJS) on the community-district × month panel.
# Staggered-robust estimators (CS / SA / BJS) should agree with TWFE when
# adoption is a single cohort (which ours is: all nine treated CDs flip
# on 2023-07-01). Cross-estimator sign agreement is the primary
# invariant; magnitude within ±20% across methods is the secondary
# invariant.

# %% tags=["jc.step", "name=did_results"]
from pathlib import Path

import jellycell.api as jc
from factor_factory.engines.did import estimate as did_estimate
from factor_factory.tidy import Panel

panel = Panel.from_parquet("artifacts/ff_panel.parquet")
print(f"panel: {len(panel.unit_ids)} units × {len(panel.periods)} periods, outcome={panel.outcome_col}")

METHODS = ("twfe", "cs", "sa", "bjs")
results = did_estimate(
    panel,
    methods=METHODS,
    outcome="complaint_count",
    cluster="unit_id",
)

print()
print(f"{'method':<6} {'ATT':>10} {'SE':>10} {'p':>12} {'95% CI':>22}   N")
print("-" * 72)
for r in results:
    print(f"{r.method:<6} {r.att:>+10.3f} {r.se:>10.3f} {r.p_value:>12.4g} "
          f"[{r.ci_95[0]:>+8.3f}, {r.ci_95[1]:>+8.3f}]  {r.n}")

payload = {
    r.method: {
        "att": float(r.att),
        "se": float(r.se),
        "p_value": float(r.p_value),
        "ci_95_low": float(r.ci_95[0]),
        "ci_95_high": float(r.ci_95[1]),
        "n": int(r.n),
        "method": r.method,
    }
    for r in results
}
jc.save(payload, "artifacts/did_results.json",
        caption="Four-estimator DiD on NYC rat-containerization pilot (2023-07-01, 9 treated CDs).")

# %% tags=["jc.table", "name=main_results"]
import json

import jellycell.api as jc
import pandas as pd

data = json.loads(open("artifacts/did_results.json").read())
rows = []
for method, r in data.items():
    rows.append(
        (
            r["method"],
            round(r["att"], 3),
            round(r["se"], 3),
            f"[{r['ci_95_low']:+.2f}, {r['ci_95_high']:+.2f}]",
            f"{r['p_value']:.4g}" if r["p_value"] >= 1e-10 else "<1e-10",
            int(r["n"]),
        )
    )
df = pd.DataFrame(rows, columns=["method", "ATT", "SE", "95% CI", "p", "N"])
df["p"] = df["p"].astype(str)  # #13 workaround
jc.table(
    df,
    name="main_results",
    caption="Table 2. Four DiD estimators of the containerization-pilot effect.",
    notes=(
        "ATT reported in monthly Rodent-complaint units (lower = fewer complaints). "
        "Cluster-robust SEs at the community-district level. "
        "Treated N = 9 CDs × 60 months = 540; Control N = 65 CDs × 60 months = 3,900."
    ),
)
print(df.to_string(index=False))

# %% tags=["jc.step", "name=cross_estimator_check", "deps=did_results"]
import json

import jellycell.api as jc

data = json.loads(open("artifacts/did_results.json").read())
atts = {m: v["att"] for m, v in data.items()}
signs = {m: (v > 0) for m, v in atts.items()}
same_sign = len(set(signs.values())) == 1
baseline = abs(atts["twfe"])
spread_pct = {m: 100 * (v - atts["twfe"]) / baseline for m, v in atts.items()} if baseline > 0 else {}

cross = {
    "atts": atts,
    "signs": signs,
    "same_sign": same_sign,
    "spread_pct_vs_twfe": spread_pct,
    "invariant_sign_agreement": same_sign,
    "invariant_magnitude_within_20pct_of_twfe": all(abs(v) <= 20 for v in spread_pct.values()),
}
jc.save(cross, "artifacts/cross_estimator_check.json",
        caption="Sign + magnitude agreement check across four DiD estimators.")
print(json.dumps(cross, indent=2))

# %% [markdown]
# **Next:** `04_diagnostics.py` — event study, parallel-trends F-test,
# residual checks, cluster-SE sensitivity.
