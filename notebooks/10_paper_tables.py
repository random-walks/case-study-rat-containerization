# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# %% [markdown]
# # 10 — Paper tables (consolidated)
#
# Five tables (T1–T5) reconciled from artifacts produced in §01–§08,
# emitted as committed markdown at `artifacts/paper_tables.md` and
# referenced by MANUSCRIPT.md.

# %% tags=["jc.step", "name=table_T1_descriptive"]
import json

import jellycell.api as jc
import pandas as pd

rec = json.loads(open("artifacts/reconciled_findings.json").read())
p = rec["panel"]
bal = rec["balance_pretreatment"]

t1_rows = [
    {"Variable": "Community districts", "Treated (9)": "9", "Control (65)": "65", "Total": str(p["n_units"])},
    {"Variable": "Months in window",    "Treated (9)": str(p["n_periods"]), "Control (65)": str(p["n_periods"]), "Total": str(p["n_periods"])},
    {"Variable": "CD-month observations", "Treated (9)": str(9 * p["n_periods"]), "Control (65)": str(65 * p["n_periods"]), "Total": f"{p['n_observations']:,}"},
    {"Variable": "Pre-treatment mean complaints/CD/month", "Treated (9)": f"{bal['pre_treated_mean']:.1f}", "Control (65)": f"{bal['pre_control_mean']:.1f}", "Total": "—"},
    {"Variable": "Total Rodent complaints in window", "Treated (9)": "—", "Control (65)": "—", "Total": f"{p['total_complaints']:,}"},
]
t1 = pd.DataFrame(t1_rows)
jc.table(t1, name="table_T1_descriptive",
         caption="Table 1. Descriptive statistics, 2020–2024 panel.")
print("T1:")
print(t1.to_string(index=False))

# %% tags=["jc.step", "name=table_T2_did_estimators"]
import json

import jellycell.api as jc
import pandas as pd

rec = json.loads(open("artifacts/reconciled_findings.json").read())
ce = rec["cross_estimator"]

rows = []
for m in ("twfe", "cs", "sa", "bjs"):
    r = ce[m]
    rows.append({
        "Estimator": m.upper(),
        "ATT": f"{r['att']:+.2f}",
        "SE":  f"{r['se']:.2f}",
        "p":   "<.001" if r["p_value"] < 0.001 else f"{r['p_value']:.3f}",
    })
t2 = pd.DataFrame(rows)
jc.table(t2, name="table_T2_did_estimators",
         caption="Table 2. Four DiD estimators of the containerization-pilot effect.")
print("T2:")
print(t2.to_string(index=False))

# %% tags=["jc.step", "name=table_T3_robustness"]
import json

import jellycell.api as jc
import pandas as pd

rec = json.loads(open("artifacts/reconciled_findings.json").read())
rob = rec["robustness"]

rows = [
    {"Check": "Placebo t₀ = 2022-07-01 (BJS)",
     "ATT / coef": f"{rob['placebo_att_bjs']:+.2f}",
     "p": "<.001" if rob["placebo_p_bjs"] < 0.001 else f"{rob['placebo_p_bjs']:.3f}",
     "Reading": "Non-significant at raw α; sign reversal vs. headline."},
    {"Check": "Log(1 + complaints) TWFE",
     "ATT / coef": f"{rob['log_outcome_coef']:+.3f} (≈{rob['log_outcome_pct_change']:+.1f}%)",
     "p": f"{rob['log_outcome_p']:.3f}",
     "Reading": "Same sign, smaller magnitude, non-significant."},
    {"Check": "Post-COVID (2022-01 →) (BJS)",
     "ATT / coef": f"{rob['post_covid_att_bjs']:+.2f}",
     "p": "<.001" if rob["post_covid_p_bjs"] < 0.001 else f"{rob['post_covid_p_bjs']:.3f}",
     "Reading": "Strengthens headline."},
    {"Check": "Manhattan-only controls (BJS)",
     "ATT / coef": f"{rob['manhattan_only_att_bjs']:+.2f}",
     "p": "<.001" if rob["manhattan_only_p_bjs"] < 0.001 else f"{rob['manhattan_only_p_bjs']:.3f}",
     "Reading": "Same sign, wide CI (N=6 controls)."},
]
t3 = pd.DataFrame(rows)
jc.table(t3, name="table_T3_robustness",
         caption="Table 3. Robustness checks — headline effect across four alternative specifications.")
print("T3:")
print(t3.to_string(index=False))

# %% tags=["jc.step", "name=table_T4_rdd_sensitivity"]
import json

import jellycell.api as jc
import pandas as pd

rdd = json.loads(open("artifacts/rdd_density_sensitivity.json").read())
rows = []
for s in rdd["bandwidth_sensitivity"]:
    rows.append({
        "Bandwidth": s["bandwidth_label"],
        "h (complaints/month)": f"{s['bandwidth']:.2f}",
        "ATT": f"{s['att']:+.2f}",
        "SE": f"{s['se']:.2f}",
        "p": f"{s['p_value']:.3f}",
    })
t4 = pd.DataFrame(rows)
jc.table(t4, name="table_T4_rdd_sensitivity",
         caption=("Table 4. RDD on pre-period complaint rate (cutoff = "
                  f"{rdd['cutoff']:.1f}) — bandwidth sensitivity."))
print("T4:")
print(t4.to_string(index=False))

# %% tags=["jc.step", "name=table_T5_diagnostic_checklist"]
import json

import jellycell.api as jc
import pandas as pd

rec = json.loads(open("artifacts/reconciled_findings.json").read())
bh = json.loads(open("artifacts/bh_correction.json").read())
mde = json.loads(open("artifacts/mde_analysis.json").read())
d = rec["diagnostics"]

rows = [
    {"Diagnostic": "Parallel-trends joint F", "Value": f"F = {d['pre_trends_F_stat']:.2f}", "p": "<.001", "Reading": "Reject flat pre-trends."},
    {"Diagnostic": "Breusch-Pagan", "Value": "see §4.2", "p": "<.001", "Reading": "Heteroskedastic residuals; cluster-robust SE mitigates."},
    {"Diagnostic": "TWFE R²", "Value": f"{d['r_squared']:.3f}", "p": "—", "Reading": "Within-panel variance largely absorbed."},
    {"Diagnostic": "MDE (α=.05, power=.80)", "Value": f"|d| = {mde['mde_cohens_d']:.2f} (~{mde['mde_natural_units']:.1f} complaints)", "p": "—",
     "Reading": "Conventional MDE floor exceeds observed |ATT|; see §5.3."},
    {"Diagnostic": "Benjamini-Hochberg survivors",
     "Value": f"{bh['n_surviving_bh']}/{bh['n_tests']} tests",
     "p": "BH 0.05",
     "Reading": "Main BJS + SA survive; placebo_sa also rejects (known small-cohort SA quirk)."},
]
t5 = pd.DataFrame(rows)
jc.table(t5, name="table_T5_diagnostic_checklist",
         caption="Table 5. Identification + statistical diagnostic checklist.")
print("T5:")
print(t5.to_string(index=False))

# %% tags=["jc.step", "name=paper_tables_md"]
from pathlib import Path

import jellycell.api as jc

# Also emit a single markdown file with all five tables for convenience.
out = Path("artifacts/paper_tables.md")
out.parent.mkdir(parents=True, exist_ok=True)

def df_to_md(df, caption):
    lines = [f"**{caption}**", ""]
    lines.append("| " + " | ".join(df.columns) + " |")
    lines.append("| " + " | ".join(["---"] * len(df.columns)) + " |")
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(v) for v in row) + " |")
    lines.append("")
    return "\n".join(lines)

# Reload frames from what we just emitted via jc.table (pandas round-trip).
import json, pandas as pd
rec = json.loads(open("artifacts/reconciled_findings.json").read())
rdd = json.loads(open("artifacts/rdd_density_sensitivity.json").read())
bh = json.loads(open("artifacts/bh_correction.json").read())
mde = json.loads(open("artifacts/mde_analysis.json").read())
bal = rec["balance_pretreatment"]

# Simpler: rebuild the five frames here, identical logic as above.
t1 = pd.DataFrame([
    {"Variable": "Community districts", "Treated (9)": "9", "Control (65)": "65", "Total": str(rec["panel"]["n_units"])},
    {"Variable": "Months in window", "Treated (9)": str(rec["panel"]["n_periods"]), "Control (65)": str(rec["panel"]["n_periods"]), "Total": str(rec["panel"]["n_periods"])},
    {"Variable": "CD-month observations", "Treated (9)": str(9 * rec["panel"]["n_periods"]), "Control (65)": str(65 * rec["panel"]["n_periods"]), "Total": f"{rec['panel']['n_observations']:,}"},
    {"Variable": "Pre-treatment mean complaints/CD/month", "Treated (9)": f"{bal['pre_treated_mean']:.1f}", "Control (65)": f"{bal['pre_control_mean']:.1f}", "Total": "—"},
    {"Variable": "Total Rodent complaints in window", "Treated (9)": "—", "Control (65)": "—", "Total": f"{rec['panel']['total_complaints']:,}"},
])

rows = []
for m in ("twfe", "cs", "sa", "bjs"):
    r = rec["cross_estimator"][m]
    rows.append({"Estimator": m.upper(), "ATT": f"{r['att']:+.2f}", "SE": f"{r['se']:.2f}",
                 "p": "<.001" if r["p_value"] < 0.001 else f"{r['p_value']:.3f}"})
t2 = pd.DataFrame(rows)

rob = rec["robustness"]
t3 = pd.DataFrame([
    {"Check": "Placebo t₀ = 2022-07-01 (BJS)", "ATT": f"{rob['placebo_att_bjs']:+.2f}", "p": "<.001" if rob['placebo_p_bjs'] < 0.001 else f"{rob['placebo_p_bjs']:.3f}", "Reading": "Non-significant at raw α; sign reversal vs. headline."},
    {"Check": "Log(1 + complaints) TWFE", "ATT": f"{rob['log_outcome_coef']:+.3f} ({rob['log_outcome_pct_change']:+.1f}%)", "p": f"{rob['log_outcome_p']:.3f}", "Reading": "Same sign; smaller magnitude."},
    {"Check": "Post-COVID (2022-01 →) (BJS)", "ATT": f"{rob['post_covid_att_bjs']:+.2f}", "p": "<.001" if rob['post_covid_p_bjs'] < 0.001 else f"{rob['post_covid_p_bjs']:.3f}", "Reading": "Strengthens headline."},
    {"Check": "Manhattan-only controls (BJS)", "ATT": f"{rob['manhattan_only_att_bjs']:+.2f}", "p": "<.001" if rob['manhattan_only_p_bjs'] < 0.001 else f"{rob['manhattan_only_p_bjs']:.3f}", "Reading": "Same sign, wide CI."},
])

t4 = pd.DataFrame([
    {"Bandwidth": s["bandwidth_label"], "h": f"{s['bandwidth']:.2f}", "ATT": f"{s['att']:+.2f}",
     "SE": f"{s['se']:.2f}", "p": f"{s['p_value']:.3f}"}
    for s in rdd["bandwidth_sensitivity"]
])

d = rec["diagnostics"]
t5 = pd.DataFrame([
    {"Diagnostic": "Parallel-trends F", "Value": f"F = {d['pre_trends_F_stat']:.2f}", "p": "<.001", "Reading": "Reject flat pre-trends."},
    {"Diagnostic": "Breusch-Pagan", "Value": "see §4.2", "p": "<.001", "Reading": "Heteroskedastic; cluster-robust SE."},
    {"Diagnostic": "TWFE R²", "Value": f"{d['r_squared']:.3f}", "p": "—", "Reading": "Within-panel variance absorbed."},
    {"Diagnostic": "MDE (α=.05, power=.80)", "Value": f"~{mde['mde_natural_units']:.1f} complaints (|d| ~ {mde['mde_cohens_d']:.2f})", "p": "—", "Reading": "Exceeds observed |ATT|; see §5.3."},
    {"Diagnostic": "BH survivors", "Value": f"{bh['n_surviving_bh']}/{bh['n_tests']}", "p": "BH 0.05", "Reading": "Main BJS + SA survive."},
])

content = "\n".join([
    df_to_md(t1, "Table 1. Descriptive statistics, 2020–2024 panel."),
    df_to_md(t2, "Table 2. Four DiD estimators of the containerization-pilot effect."),
    df_to_md(t3, "Table 3. Robustness checks."),
    df_to_md(t4, f"Table 4. RDD bandwidth sensitivity (cutoff = {rdd['cutoff']:.1f})."),
    df_to_md(t5, "Table 5. Identification + statistical diagnostic checklist."),
])
out.write_text(content)
jc.save({"path": str(out), "n_bytes": len(content)},
        "artifacts/paper_tables_meta.json",
        caption="Consolidated paper tables emitted as markdown.")
print(f"wrote {out} — {len(content)} bytes")

# %% [markdown]
# End of the analysis pipeline. See `manuscripts/MANUSCRIPT.md` for the
# hand-authored paper narrative, `manuscripts/FINDINGS.md` (auto-generated
# in §06) for the reconciled headline, and
# `manuscripts/DIAGNOSTICS_CHECKLIST.md` for the assumption ledger.
