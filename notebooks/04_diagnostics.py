# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# %% [markdown]
# # 04 — Diagnostics
#
# Event-study (leads + lags), pre-trend F-test, TWFE residual
# normality + heteroskedasticity checks. The event study is the
# single most important diagnostic for a DiD; flat pre-period leads
# are the parallel-trends "smell test" on top of the visual in §02.

# %% tags=["jc.step", "name=event_study"]
import json
from pathlib import Path

import jellycell.api as jc
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

panel = pd.read_parquet("artifacts/panel_long.parquet").reset_index()
events = json.loads(Path("data/rat_mitigation_events_2023.json").read_text())
TREATED = sorted({e["unit"] for e in events["events"]})
panel["period"] = pd.to_datetime(panel["period"].astype(str))
panel["treated_unit"] = panel["unit_id"].isin(TREATED).astype(int)
panel["period_idx"] = (panel["period"].dt.year - 2020) * 12 + panel["period"].dt.month - 1

TREATMENT_PERIOD_IDX = (2023 - 2020) * 12 + (7 - 1)  # 2023-07 → idx 42
panel["event_time"] = panel["period_idx"] - TREATMENT_PERIOD_IDX

# Event-time dummies for treated units; reference = event_time = -1.
# Restrict event_time to [-24, +18] for stability (drops 2020-H1 leads).
lo, hi = -24, 18
rows = []
for k in range(lo, hi + 1):
    if k == -1:
        continue
    mask = (panel["event_time"] == k) & (panel["treated_unit"] == 1)
    panel[f"d_k{k:+d}".replace("+", "p").replace("-", "m")] = mask.astype(int)

dummy_cols = [c for c in panel.columns if c.startswith("d_k")]

# Regression: y_it = alpha_i + alpha_t + sum_k gamma_k D_{i, t=t0+k} + eps
# Use fixed-effects via statsmodels' demean (absorb unit + period).
formula = f"complaint_count ~ {' + '.join(dummy_cols)} + C(unit_id) + C(period_idx)"
model = smf.ols(formula=formula, data=panel).fit(
    cov_type="cluster", cov_kwds={"groups": panel["unit_id"]}
)
coefs, ses, pvals = [], [], []
for c in dummy_cols:
    k = int(c[3:].replace("p", "+").replace("m", "-"))
    coefs.append((k, model.params.get(c, np.nan), model.bse.get(c, np.nan), model.pvalues.get(c, np.nan)))

es = pd.DataFrame(coefs, columns=["event_time", "coef", "se", "p"]).sort_values("event_time").reset_index(drop=True)
es["ci95_low"] = es["coef"] - 1.96 * es["se"]
es["ci95_high"] = es["coef"] + 1.96 * es["se"]
es.to_csv("artifacts/event_study.csv", index=False)

# Pre-trends F-test: joint test that leads (event_time ∈ [lo, -2]) are all zero.
pre_leads = [c for c in dummy_cols if int(c[3:].replace("p", "+").replace("m", "-")) < 0]
ftest = model.f_test(" = 0, ".join(pre_leads) + " = 0") if pre_leads else None
ftest_payload = None
if ftest is not None:
    ftest_payload = {
        "F_stat": float(ftest.fvalue),
        "p_value": float(ftest.pvalue),
        "df_num": int(ftest.df_num),
        "df_denom": int(ftest.df_denom),
        "interpretation": "fail_to_reject_flat_pretrends" if ftest.pvalue > 0.05 else "reject_flat_pretrends",
    }

payload = {
    "n_leads": sum(1 for c in dummy_cols if int(c[3:].replace("p", "+").replace("m", "-")) < 0),
    "n_lags": sum(1 for c in dummy_cols if int(c[3:].replace("p", "+").replace("m", "-")) >= 0),
    "pre_trends_F_test": ftest_payload,
    "event_study_coefs_preview": es.head(8).round(3).to_dict(orient="records"),
}
jc.save(payload, "artifacts/event_study_summary.json",
        caption="Event-study leads/lags + joint F-test that pre-period leads are zero.")
print(json.dumps(payload, indent=2, default=str))

# %% tags=["jc.figure", "name=fig2_event_study"]
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

es = pd.read_csv("artifacts/event_study.csv")
fig, ax = plt.subplots(figsize=(10, 5))
ax.errorbar(es["event_time"], es["coef"],
            yerr=1.96 * es["se"], fmt="o", color="#333",
            ecolor="#888", capsize=2, markersize=4, linewidth=1)
ax.axhline(0, color="red", linestyle="--", alpha=0.5)
ax.axvline(0, color="red", linestyle="--", alpha=0.5)
ax.set_xlabel("Months from treatment (0 = July 2023)")
ax.set_ylabel("Coefficient (monthly rodent complaints)")
ax.set_title("Figure 2. Event-study coefficients (TWFE, cluster-robust 95% CI)")
fig.tight_layout()
Path("artifacts/figures").mkdir(parents=True, exist_ok=True)
fig.savefig("artifacts/figures/figure-2-event-study.png", dpi=150)
plt.close(fig)

from IPython.display import Image
Image("artifacts/figures/figure-2-event-study.png")

# %% tags=["jc.step", "name=twfe_residuals"]
import json

import jellycell.api as jc
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats as sps

panel = pd.read_parquet("artifacts/panel_long.parquet").reset_index()
events = json.loads(open("data/rat_mitigation_events_2023.json").read())
TREATED = sorted({e["unit"] for e in events["events"]})
panel["period"] = pd.to_datetime(panel["period"].astype(str))
panel["treated_unit"] = panel["unit_id"].isin(TREATED).astype(int)
panel["post"] = (panel["period"] >= pd.Timestamp("2023-07-01")).astype(int)
panel["treatment"] = panel["treated_unit"] * panel["post"]
panel["period_idx"] = (panel["period"].dt.year - 2020) * 12 + panel["period"].dt.month - 1

ols = smf.ols("complaint_count ~ treatment + C(unit_id) + C(period_idx)", data=panel)
fit = ols.fit(cov_type="cluster", cov_kwds={"groups": panel["unit_id"]})
resid = fit.resid

# Breusch-Pagan (via statsmodels).
from statsmodels.stats.diagnostic import het_breuschpagan
bp_stat, bp_p, _, _ = het_breuschpagan(resid, ols.exog)
# Shapiro-Wilk on a random 5000 sample (Shapiro has a 5000-sample limit).
rng = np.random.default_rng(42)
sample = rng.choice(resid, size=min(5000, len(resid)), replace=False)
sw_stat, sw_p = sps.shapiro(sample)

payload = {
    "twfe_coef_treatment": float(fit.params.get("treatment", np.nan)),
    "twfe_se_treatment": float(fit.bse.get("treatment", np.nan)),
    "twfe_p_treatment": float(fit.pvalues.get("treatment", np.nan)),
    "r_squared": float(fit.rsquared),
    "n_obs": int(fit.nobs),
    "breusch_pagan": {
        "stat": float(bp_stat),
        "p_value": float(bp_p),
        "interpretation": "heteroskedastic" if bp_p < 0.05 else "homoskedastic",
    },
    "shapiro_wilk_on_sampled_residuals": {
        "stat": float(sw_stat),
        "p_value": float(sw_p),
        "sample_size": int(len(sample)),
        "interpretation": "non_normal" if sw_p < 0.05 else "normal",
    },
    "residuals_summary": {
        "mean": float(resid.mean()),
        "std": float(resid.std()),
        "min": float(resid.min()),
        "max": float(resid.max()),
    },
}
jc.save(payload, "artifacts/twfe_residual_diagnostics.json",
        caption="TWFE residual diagnostics — BP + SW + variance summary.")
print(json.dumps(payload, indent=2))

# %% tags=["jc.figure", "name=fig3_residual_qq"]
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats as sps
import json

panel = pd.read_parquet("artifacts/panel_long.parquet").reset_index()
events = json.loads(open("data/rat_mitigation_events_2023.json").read())
TREATED = sorted({e["unit"] for e in events["events"]})
panel["period"] = pd.to_datetime(panel["period"].astype(str))
panel["treated_unit"] = panel["unit_id"].isin(TREATED).astype(int)
panel["post"] = (panel["period"] >= pd.Timestamp("2023-07-01")).astype(int)
panel["treatment"] = panel["treated_unit"] * panel["post"]
panel["period_idx"] = (panel["period"].dt.year - 2020) * 12 + panel["period"].dt.month - 1
ols = smf.ols("complaint_count ~ treatment + C(unit_id) + C(period_idx)", data=panel)
fit = ols.fit(cov_type="cluster", cov_kwds={"groups": panel["unit_id"]})
resid = fit.resid

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
# Q-Q plot.
sps.probplot(resid, dist="norm", plot=ax1)
ax1.set_title("Q-Q plot of TWFE residuals")
# Residual vs. fitted.
ax2.scatter(fit.fittedvalues, resid, s=3, alpha=0.3, color="#333")
ax2.axhline(0, color="red", linestyle="--", alpha=0.5)
ax2.set_xlabel("Fitted value")
ax2.set_ylabel("Residual")
ax2.set_title("TWFE residuals vs. fitted")
fig.tight_layout()
Path("artifacts/figures").mkdir(parents=True, exist_ok=True)
fig.savefig("artifacts/figures/figure-3-residual-diagnostics.png", dpi=150)
plt.close(fig)

from IPython.display import Image
Image("artifacts/figures/figure-3-residual-diagnostics.png")

# %% [markdown]
# **Next:** `05_robustness.py` — placebo, subsample, alternative functional form.
