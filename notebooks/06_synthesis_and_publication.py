# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# %% [markdown]
# # 06 — Synthesis + diagnostic checklist
#
# Reconciles the multi-estimator results from notebook 03 with the
# diagnostics from 04 and the robustness checks from 05. Produces the
# headline JSON + a pass/fail checklist for [`manuscripts/DIAGNOSTICS_CHECKLIST.md`](../manuscripts/DIAGNOSTICS_CHECKLIST.md).

# %% tags=["jc.load", "name=load_artifacts"]
import json
from pathlib import Path
import jellycell.api as jc

artifacts = Path("artifacts")

def _load(name):
    p = artifacts / name
    return json.loads(p.read_text()) if p.exists() else {}

panel_summary = _load("panel_summary.json")
balance = _load("balance_table.json")
twfe = _load("twfe_result.json")
sa = _load("staggered_did.json")
sc = _load("synthetic_control.json")
diag = _load("residual_diagnostics.json")
jk = _load("jackknife_summary.json")
boot = _load("bootstrap_ci.json")
placebo = _load("placebo_test.json")
seasonal = _load("seasonal_robust.json")
print(f"  loaded {sum(1 for x in [panel_summary, balance, twfe, sa, sc, diag, jk, boot, placebo, seasonal] if x)} / 10 artifact JSONs")

# %% tags=["jc.step", "name=results_table", "deps=load_artifacts"]
import json
from pathlib import Path
import jellycell.api as jc
import pandas as pd

artifacts = Path("artifacts")
def _load(name):
    p = artifacts / name
    return json.loads(p.read_text()) if p.exists() else {}

twfe = _load("twfe_result.json")
sa = _load("staggered_did.json")
sc = _load("synthetic_control.json")

rows = [
    {
        "estimator": "Two-way FE (TWFE)",
        "att": twfe.get("att"),
        "se": twfe.get("se"),
        "p_value": twfe.get("p_value"),
        "ci_lower": twfe.get("ci_lower"),
        "ci_upper": twfe.get("ci_upper"),
    },
    {
        "estimator": "Staggered DiD (Callaway-Sant'Anna)",
        "att": sa.get("att", "—"),
        "se": "—",
        "p_value": sa.get("p_value", "—"),
        "ci_lower": sa.get("ci_lower", "—"),
        "ci_upper": sa.get("ci_upper", "—"),
    },
    {
        "estimator": "Synthetic control (MN 03)",
        "att": sc.get("att", "—"),
        "se": "—",
        "p_value": "—",
        "ci_lower": "—",
        "ci_upper": "—",
    },
]
results_df = pd.DataFrame(rows).astype(str)
jc.table(results_df, name="main_results_summary", caption="Main results: ATT estimates across three estimators")
print(results_df.to_string(index=False))

# %% tags=["jc.step", "name=checklist", "deps=load_artifacts"]
import json
from pathlib import Path
import jellycell.api as jc
import pandas as pd

artifacts = Path("artifacts")
def _load(name):
    p = artifacts / name
    return json.loads(p.read_text()) if p.exists() else {}

balance = _load("balance_table.json")
diag = _load("residual_diagnostics.json")
jk = _load("jackknife_summary.json")
boot = _load("bootstrap_ci.json")
placebo = _load("placebo_test.json")
seasonal = _load("seasonal_robust.json")

# Build the diagnostic checklist
def _max_smd(b):
    if not b.get("covariates"):
        return None
    return max(abs(c.get("smd", 0)) for c in b["covariates"])

max_smd = _max_smd(balance) or 0
checks = [
    {
        "diagnostic": "Pre-treatment balance (max |SMD|)",
        "value": round(max_smd, 3),
        "threshold": "<0.5 acceptable, <0.1 ideal",
        "status": "PASS" if max_smd < 0.5 else "FAIL" if max_smd > 0.5 else "MARGINAL",
    },
    {
        "diagnostic": "Residual normality (Jarque-Bera p)",
        "value": diag.get("jarque_bera_p"),
        "threshold": ">0.05 supports normal residuals",
        "status": "PASS" if (diag.get("jarque_bera_p") or 0) > 0.05 else "FAIL",
    },
    {
        "diagnostic": "Jackknife stability (ATT range)",
        "value": jk.get("range"),
        "threshold": "small range = stable, no single unit drives ATT",
        "status": "MANUAL — see jackknife_summary.json",
    },
    {
        "diagnostic": "Bootstrap 95% CI",
        "value": f"[{boot.get('ci_2.5')}, {boot.get('ci_97.5')}]",
        "threshold": "compare to analytic CI",
        "status": "MANUAL — compare with TWFE analytic CI",
    },
    {
        "diagnostic": "Placebo test (pre-treatment)",
        "value": placebo.get("att"),
        "threshold": "ATT ≈ 0, p > 0.05 supports parallel trends",
        "status": placebo.get("interpretation", "MANUAL")[:6],
    },
    {
        "diagnostic": "Seasonal robustness (demeaned outcome)",
        "value": seasonal.get("att"),
        "threshold": "should be similar to raw TWFE if seasonal not driving result",
        "status": "MANUAL — compare with TWFE",
    },
]
checklist_df = pd.DataFrame(checks).astype(str)
jc.table(checklist_df, name="diagnostic_checklist", caption="Diagnostic checklist — pass/fail per assumption tested")
print(checklist_df.to_string(index=False))

# %% tags=["jc.step", "name=headline_findings", "deps=checklist"]
import json
from pathlib import Path
import jellycell.api as jc

artifacts = Path("artifacts")
def _load(name):
    p = artifacts / name
    return json.loads(p.read_text()) if p.exists() else {}

panel_summary = _load("panel_summary.json")
twfe = _load("twfe_result.json")
sa = _load("staggered_did.json")
sc = _load("synthetic_control.json")
boot = _load("bootstrap_ci.json")
placebo = _load("placebo_test.json")

findings = {
    "panel": f"{panel_summary.get('n_districts')} districts × {panel_summary.get('n_periods')} months ({panel_summary.get('total_complaints'):,} complaints)",
    "treatment": f"{panel_summary.get('treated_units')} treated units from {panel_summary.get('treatment_date')}",
    "twfe_att": twfe.get("att"),
    "twfe_ci": [twfe.get("ci_lower"), twfe.get("ci_upper")],
    "twfe_p": twfe.get("p_value"),
    "staggered_did_att": sa.get("att", "n/a"),
    "synthetic_control_att": sc.get("att", "n/a"),
    "bootstrap_ci_95": [boot.get("ci_2.5"), boot.get("ci_97.5")],
    "placebo_passes": placebo.get("passes", "n/a"),
    "interpretation": (
        f"TWFE ATT = {twfe.get('att')} per district-month (95% CI {twfe.get('ci_lower')}, {twfe.get('ci_upper')}). "
        "Reconcile with synthetic control + staggered DiD via the diagnostic checklist; if estimators diverge "
        "but pass diagnostics, treat as evidence of estimator-sensitive effect (not zero, not robust)."
    ),
}
jc.save(findings, "artifacts/headline_findings.json", caption="Headline findings — full pipeline")
print()
for k, v in findings.items():
    print(f"  {k}: {v}")

# %% [markdown]
# All artifacts feed [`manuscripts/MANUSCRIPT.md`](../manuscripts/MANUSCRIPT.md)
# (working-paper format) and [`manuscripts/DIAGNOSTICS_CHECKLIST.md`](../manuscripts/DIAGNOSTICS_CHECKLIST.md)
# (the pass/fail summary). Methodology + identification assumptions are in
# [`manuscripts/METHODOLOGY.md`](../manuscripts/METHODOLOGY.md).
