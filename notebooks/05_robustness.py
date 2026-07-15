# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# %% [markdown]
# # 05 — Robustness
#
# Five robustness probes:
# 1. **Placebo treatment date**: shift t_0 earlier by 12 months. Null effect
#    is reassuring; a significant "effect" before the real rollout would
#    argue for anticipation or shared trend.
# 2. **Log-transformed outcome**: OLS on log(complaints+1). Addresses
#    right-skewed count heteroskedasticity (§04 diagnostic).
# 3. **Sample restriction — drop COVID period**: rerun on 2022-01 onward
#    only, to check that 2020 lockdown anomalies are not driving the
#    headline.
# 4. **Alternative control group — Manhattan-only slice**: run DiD on
#    Manhattan units only, with the true per-cohort onsets (thin control
#    pool after 2024-11 — see MANUSCRIPT §4.5).
# 5. **Phase-in guard**: truncate the panel before 2025-06-01 so DSNY's
#    2025–26 medium/large-building phase-ins (which partially treat the
#    control pool) cannot drive the headline.

# %% tags=["jc.step", "name=placebo_did"]
import json
from datetime import date
from pathlib import Path

import jellycell.api as jc
from factor_factory.engines.did import estimate as did_estimate
from factor_factory.tidy import TreatmentEvent

from nyc311.io import load_service_requests
from nyc311.temporal import build_complaint_panel
import re

date_re = re.compile(r"_(\d{4})-\d{2}-\d{2}_(\d{4})-\d{2}-\d{2}_")
records = []
for p in sorted(Path("data/cache").glob("*_rodent_*.csv")):
    if date_re.search(p.name):
        records.extend(load_service_requests(p))

events = json.loads(Path("data/rat_mitigation_events_2023.json").read_text())
TREATED = tuple(sorted({e["unit"] for e in events["events"]}))

# Placebo: pretend the pilot began 2022-07-01 (12 months early), and
# only use data 2020-01 → 2023-06 so the "real" treatment is absent
# from the sample.
from nyc311.temporal._models import TreatmentEvent as Nyc311TE
placebo_event = Nyc311TE(
    name="placebo_2022_07_01",
    description="Placebo — 12 months before real pilot; effect should be null.",
    treated_units=TREATED,
    treatment_date=date(2022, 7, 1),
    geography="community_district",
)
placebo_records = [r for r in records if r.created_date < date(2023, 7, 1)]
placebo_ds = build_complaint_panel(
    placebo_records, geography="community_district", freq="ME",
    treatment_events=(placebo_event,),
)
placebo_panel = placebo_ds.to_factor_factory_panel()

placebo_results = did_estimate(
    placebo_panel, methods=("twfe", "cs", "sa", "bjs"),
    outcome="complaint_count", cluster="unit_id",
)
placebo_payload = {
    r.method: {
        "att": float(r.att), "se": float(r.se), "p_value": float(r.p_value),
        "ci_95": [float(r.ci_95[0]), float(r.ci_95[1])], "n": int(r.n),
    }
    for r in placebo_results
}
jc.save(placebo_payload, "artifacts/placebo_did.json",
        caption="Placebo DiD: pretend treatment is 2022-07-01 (12 months early). Null expected.")
print("Placebo (2022-07-01):")
for r in placebo_results:
    print(f"  {r.method:<6} att={r.att:+8.3f} se={r.se:6.3f} p={r.p_value:.4g}")

# %% tags=["jc.step", "name=log_outcome_did"]
import json
from pathlib import Path

import jellycell.api as jc
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

panel = pd.read_parquet("artifacts/panel_long.parquet").reset_index()
events = json.loads(open("data/rat_mitigation_events_2023.json").read())
TREATED = sorted({e["unit"] for e in events["events"]})
panel["period"] = pd.to_datetime(panel["period"].astype(str))
panel["treated_unit"] = panel["unit_id"].isin(TREATED).astype(int)
panel["post"] = (panel["period"] >= pd.Timestamp("2023-07-01")).astype(int)
panel["treatment"] = panel["treated_unit"] * panel["post"]
panel["period_idx"] = (panel["period"].dt.year - 2020) * 12 + panel["period"].dt.month - 1
panel["log_complaints"] = np.log1p(panel["complaint_count"])

fit = smf.ols(
    "log_complaints ~ treatment + C(unit_id) + C(period_idx)",
    data=panel,
).fit(cov_type="cluster", cov_kwds={"groups": panel["unit_id"]})
payload = {
    "coef_treatment_log": float(fit.params.get("treatment", np.nan)),
    "se": float(fit.bse.get("treatment", np.nan)),
    "p_value": float(fit.pvalues.get("treatment", np.nan)),
    "ci_95": [float(fit.conf_int().loc["treatment", 0]),
              float(fit.conf_int().loc["treatment", 1])],
    "r_squared": float(fit.rsquared),
    "pct_change_point_est": float(100 * (np.exp(fit.params.get("treatment", 0)) - 1)),
    "interpretation": "exp(coef) - 1 is the fractional change in expected complaints per CD per month.",
}
jc.save(payload, "artifacts/log_outcome_did.json",
        caption="Log-outcome TWFE DiD: addresses right-skewed count variance.")
print(json.dumps(payload, indent=2))

# %% tags=["jc.step", "name=post_covid_did"]
import json
from pathlib import Path

import jellycell.api as jc
from factor_factory.engines.did import estimate as did_estimate
from factor_factory.tidy import Panel

panel = Panel.from_parquet("artifacts/ff_panel.parquet")
df = panel.to_dataframe().reset_index()
df["period"] = pd.to_datetime(df["period"].astype(str)) if "period" in df else df["period"]

# Restrict to 2022-01 onward (post-COVID normalization).
# Rebuild the ff Panel from the restricted records — simplest path.
import pandas as pd
import re
from nyc311.io import load_service_requests
from nyc311.temporal import build_complaint_panel
from nyc311.temporal._models import TreatmentEvent as Nyc311TE
from datetime import date

date_re = re.compile(r"_(\d{4})-\d{2}-\d{2}_(\d{4})-\d{2}-\d{2}_")
records = []
for p in sorted(Path("data/cache").glob("*_rodent_*.csv")):
    if date_re.search(p.name):
        records.extend(load_service_requests(p))

post_covid_records = [r for r in records if r.created_date >= date(2022, 1, 1)]

# Preserve the REAL staggered assignment (two cohorts, per notebook 01).
# The pilot-era version of this probe marked all 59 treated units at the
# pilot date, which treated the citywide cohort ~16 months early.
events = json.loads(Path("data/rat_mitigation_events_2023.json").read_text())
by_cohort: dict[str, list[str]] = {}
for ev in events["events"]:
    by_cohort.setdefault(ev["cohort"], []).append(ev["unit"])
pilot_event = Nyc311TE(
    name="pilot_2023_post_covid",
    description="2023-07-01 lower-Manhattan pilot; post-COVID sample.",
    treated_units=tuple(sorted(by_cohort["pilot_2023"])),
    treatment_date=date(2023, 7, 1), geography="community_district",
)
rollout_event = Nyc311TE(
    name="citywide_2024_post_covid",
    description="2024-11-12 citywide rollout; post-COVID sample.",
    treated_units=tuple(sorted(by_cohort["citywide_2024"])),
    treatment_date=date(2024, 11, 12), geography="community_district",
)
ds_pc = build_complaint_panel(
    post_covid_records, geography="community_district", freq="ME",
    treatment_events=(pilot_event, rollout_event),
)
ff_pc = ds_pc.to_factor_factory_panel()
res = did_estimate(
    ff_pc, methods=("twfe", "cs", "sa", "bjs"),
    outcome="complaint_count", cluster="unit_id",
)
payload = {r.method: {
    "att": float(r.att), "se": float(r.se), "p_value": float(r.p_value),
    "ci_95": [float(r.ci_95[0]), float(r.ci_95[1])], "n": int(r.n),
} for r in res}
jc.save(payload, "artifacts/post_covid_did.json",
        caption="Sample restricted to 2022-01 → 2024-12 (excludes COVID lockdown shock).")
print("2022-01 onward subsample:")
for r in res:
    print(f"  {r.method:<6} att={r.att:+8.3f} se={r.se:6.3f} p={r.p_value:.4g}  N={r.n}")

# %% tags=["jc.step", "name=manhattan_only_did"]
import json
from pathlib import Path
import re
from datetime import date

import jellycell.api as jc
from factor_factory.engines.did import estimate as did_estimate
from nyc311.io import load_service_requests
from nyc311.temporal import build_complaint_panel
from nyc311.temporal._models import TreatmentEvent as Nyc311TE

date_re = re.compile(r"_(\d{4})-\d{2}-\d{2}_(\d{4})-\d{2}-\d{2}_")
records = []
for p in sorted(Path("data/cache").glob("*_rodent_*.csv")):
    if date_re.search(p.name):
        records.extend(load_service_requests(p))

# Keep only Manhattan records; drops non-MN controls.
mn_records = [r for r in records if r.borough and r.borough.upper().startswith("MANHATTAN")]

events = json.loads(Path("data/rat_mitigation_events_2023.json").read_text())
TREATED = tuple(sorted({e["unit"] for e in events["events"]}))
# NOTE: kept for continuity with the 2023-only paper, now with the REAL
# per-cohort onsets (MN 01–09 at the pilot date, MN 10–12 at the citywide
# date). Even so, once MN 10–12 flip in 2024-11 the never-treated pool is
# just the irregular MN catch-alls — MANUSCRIPT §4.5 tells the reader to
# lean on the other probes; the synthetic-control analysis (notebook 13)
# is the real replacement.
mn_by_cohort: dict[str, list[str]] = {}
for ev in events["events"]:
    if ev["unit"].startswith("MANHATTAN"):
        mn_by_cohort.setdefault(ev["cohort"], []).append(ev["unit"])
mn_events = []
if mn_by_cohort.get("pilot_2023"):
    mn_events.append(Nyc311TE(
        name="pilot_2023_mn_only",
        description="Lower-Manhattan pilot cohort (MN-only probe).",
        treated_units=tuple(sorted(mn_by_cohort["pilot_2023"])),
        treatment_date=date(2023, 7, 1), geography="community_district",
    ))
if mn_by_cohort.get("citywide_2024"):
    mn_events.append(Nyc311TE(
        name="citywide_2024_mn_only",
        description="Citywide-rollout cohort, Manhattan slice (MN-only probe).",
        treated_units=tuple(sorted(mn_by_cohort["citywide_2024"])),
        treatment_date=date(2024, 11, 12), geography="community_district",
    ))
ds_mn = build_complaint_panel(
    mn_records, geography="community_district", freq="ME",
    treatment_events=tuple(mn_events),
)
ff_mn = ds_mn.to_factor_factory_panel()
res = did_estimate(
    ff_mn, methods=("twfe", "cs", "sa", "bjs"),
    outcome="complaint_count", cluster="unit_id",
)
payload = {r.method: {
    "att": float(r.att), "se": float(r.se), "p_value": float(r.p_value),
    "ci_95": [float(r.ci_95[0]), float(r.ci_95[1])], "n": int(r.n),
} for r in res}
jc.save(payload, "artifacts/manhattan_only_did.json",
        caption="Manhattan-only probe (kept for continuity; thin control pool under staggering — see MANUSCRIPT §4.5).")
print("Manhattan-only controls:")
for r in res:
    print(f"  {r.method:<6} att={r.att:+8.3f} se={r.se:6.3f} p={r.p_value:.4g}  N={r.n}")

# %% tags=["jc.step", "name=phase_in_guard_did"]
import json
from datetime import date
from pathlib import Path
import re

import jellycell.api as jc
from factor_factory.engines.did import estimate as did_estimate
from nyc311.io import load_service_requests
from nyc311.temporal import build_complaint_panel
from nyc311.temporal._models import TreatmentEvent as Nyc311TE

# Phase-in guard: DSNY folded medium (10–30 unit) and larger buildings
# into containerization over 2025–2026, partially treating the
# "never-treated" pool and deepening treatment in the citywide cohort
# late in the window. Truncate the panel before 2025-06-01 (the first
# large-building milestone) and re-estimate — if the headline moves
# materially, the late window is contaminated.
date_re = re.compile(r"_(\d{4})-\d{2}-\d{2}_(\d{4})-\d{2}-\d{2}_")
records = []
for p in sorted(Path("data/cache").glob("*_rodent_*.csv")):
    if date_re.search(p.name):
        records.extend(load_service_requests(p))
guard_records = [r for r in records if r.created_date < date(2025, 6, 1)]

events = json.loads(Path("data/rat_mitigation_events_2023.json").read_text())
by_cohort: dict[str, list[str]] = {}
for ev in events["events"]:
    by_cohort.setdefault(ev["cohort"], []).append(ev["unit"])
guard_events = (
    Nyc311TE(
        name="pilot_2023_phase_in_guard",
        description="Pilot cohort; panel truncated before the 2025-06 phase-ins.",
        treated_units=tuple(sorted(by_cohort["pilot_2023"])),
        treatment_date=date(2023, 7, 1), geography="community_district",
    ),
    Nyc311TE(
        name="citywide_2024_phase_in_guard",
        description="Citywide cohort; panel truncated before the 2025-06 phase-ins.",
        treated_units=tuple(sorted(by_cohort["citywide_2024"])),
        treatment_date=date(2024, 11, 12), geography="community_district",
    ),
)
ds_guard = build_complaint_panel(
    guard_records, geography="community_district", freq="ME",
    treatment_events=guard_events,
)
ff_guard = ds_guard.to_factor_factory_panel()
res = did_estimate(
    ff_guard, methods=("twfe", "cs", "sa", "bjs"),
    outcome="complaint_count", cluster="unit_id",
)
payload = {r.method: {
    "att": float(r.att), "se": float(r.se), "p_value": float(r.p_value),
    "ci_95": [float(r.ci_95[0]), float(r.ci_95[1])], "n": int(r.n),
} for r in res}
jc.save(payload, "artifacts/phase_in_guard_did.json",
        caption="Phase-in guard: panel truncated before 2025-06-01 (pre-dates the medium/large-building phase-ins).")
print("Phase-in guard (window < 2025-06):")
for r in res:
    print(f"  {r.method:<6} att={r.att:+8.3f} se={r.se:6.3f} p={r.p_value:.4g}  N={r.n}")

# %% [markdown]
# **Next:** `06_synthesis.py` — reconcile the above, emit the findings
# tearsheet, write the diagnostic checklist.
