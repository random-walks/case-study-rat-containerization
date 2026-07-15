# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# %% [markdown]
# # 01 — Load and preprocess
#
# Fetches (or re-reads from cache) NYC 311 **Rodent** complaints for the
# 2020-01-01 → END window (see START/END below), aggregates them into a balanced
# community-district × month panel, and emits a
# `factor_factory.tidy.Panel` ready for staggered DiD estimation.
#
# **Treatment (two cohorts)**:
#
# 1. **Pilot** — MN 01-09 (nine lower-Manhattan community districts),
#    effective 2023-07-01. DSNY mandatory containerization for both
#    commercial and residential buildings on these corridors.
# 2. **Citywide rollout** — 50 additional standard community districts
#    across the remaining four boroughs + upper Manhattan, effective
#    2024-11-12. Citywide rule for residential 1–9-unit buildings.
#
# The 15 never-treated districts are airports/parks/cemeteries
# (district number ≥ 20) and five "Unspecified" geocoding-failure
# districts; they serve as the never-treated control group for
# Callaway-Sant'Anna. Staggered-robust estimators exploit the two-
# cohort variation so we are no longer vulnerable to the single-cohort
# pathology that made TWFE and BJS mechanically coincide in the
# 2023-only specification.
#
# First-run fetch is ~15 minutes; subsequent runs hit the local CSV
# cache under `data/cache/`. See `data/README.md` for provenance.

# %% tags=["jc.load", "name=rodent_records"]
import json
import re
from datetime import date
from pathlib import Path

import jellycell.api as jc
from nyc311.io import load_service_requests
from nyc311.pipeline import bulk_fetch

CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
START = "2020-01-01"
END = "2026-06-30"  # last complete month at the 2026-07 rebuild

# Fetch on first run; deterministic filenames so subsequent runs skip.
# We pull in two slices so older 2020-2024 cache files can be reused:
# slice 1 = pre-rollout baseline + 2023 pilot (2020-01 → 2024-12)
# slice 2 = 2024 citywide rollout post-period (2025-01 → END)
print(f"bulk_fetch(Rodent, {START} → 2024-12-31) to {CACHE_DIR}...")
paths_2020 = bulk_fetch(
    complaint_types=("Rodent",),
    start_date="2020-01-01",
    end_date="2024-12-31",
    cache_dir=CACHE_DIR,
)
print(f"  {len(paths_2020)} borough files for 2020-2024 slice")

print(f"bulk_fetch(Rodent, 2025-01-01 → {END}) to {CACHE_DIR}...")
paths_2025 = bulk_fetch(
    complaint_types=("Rodent",),
    start_date="2025-01-01",
    end_date=END,
    cache_dir=CACHE_DIR,
)
print(f"  {len(paths_2025)} borough files for 2025-2026 slice")

# Load all cached Rodent CSVs — both slices, any window.
date_re = re.compile(r"_(\d{4})-\d{2}-\d{2}_(\d{4})-\d{2}-\d{2}_")
records = []
for p in sorted(CACHE_DIR.glob("*_rodent_*.csv")):
    m = date_re.search(p.name)
    if not m:
        continue
    records.extend(load_service_requests(p))
print(f"  {len(records):,} rodent complaint records loaded (all slices)")

summary = {
    "window_start": START,
    "window_end": END,
    "n_records": len(records),
    "n_borough_files": len(paths_2020) + len(paths_2025),
    "slices": ["2020-01-01..2024-12-31", "2025-01-01.." + END],
}
jc.save(
    summary,
    "artifacts/record_summary.json",
    caption=f"Loaded {len(records):,} NYC 311 Rodent records, {START} → {END}",
)

# %% tags=["jc.step", "name=panel", "deps=rodent_records"]
import json
from datetime import date
from pathlib import Path

import jellycell.api as jc
from nyc311.io import load_service_requests
from nyc311.temporal import TreatmentEvent, build_complaint_panel

# Reload records (cell cache independence — #10 workaround).
import re

date_re = re.compile(r"_(\d{4})-\d{2}-\d{2}_(\d{4})-\d{2}-\d{2}_")
records = []
for p in sorted(Path("data/cache").glob("*_rodent_*.csv")):
    if date_re.search(p.name):
        records.extend(load_service_requests(p))

# Hand-curated treatment event file with two cohorts.
events_path = Path("data/rat_mitigation_events_2023.json")
event_spec = json.loads(events_path.read_text())

# Split the events by cohort and build one TreatmentEvent per cohort.
# Staggered-robust estimators (CS, SA, BJS) derive per-unit cohort from
# panel.treatment_events; the earliest anchor across events wins per unit.
cohort_units: dict[str, list[str]] = {"pilot_2023": [], "citywide_2024": []}
for ev in event_spec["events"]:
    cohort_units[ev["cohort"]].append(ev["unit"])

pilot_units = tuple(sorted(cohort_units["pilot_2023"]))
rollout_units = tuple(sorted(cohort_units["citywide_2024"]))
PILOT_DATE = date(2023, 7, 1)
ROLLOUT_DATE = date(2024, 11, 12)

pilot_event = TreatmentEvent(
    name="nyc_containerization_pilot_2023",
    description="Lower-Manhattan pilot: MN 01-09, effective 2023-07-01.",
    treated_units=pilot_units,
    treatment_date=PILOT_DATE,
    geography="community_district",
)
rollout_event = TreatmentEvent(
    name="nyc_containerization_citywide_2024",
    description="Citywide residential 1–9-unit rollout, effective 2024-11-12.",
    treated_units=rollout_units,
    treatment_date=ROLLOUT_DATE,
    geography="community_district",
)

panel_ds = build_complaint_panel(
    records,
    geography="community_district",
    freq="ME",
    treatment_events=(pilot_event, rollout_event),
)

# Persist as parquet so downstream notebooks can skip the build.
df = panel_ds.to_dataframe()
Path("artifacts").mkdir(exist_ok=True)
df.to_parquet("artifacts/panel_long.parquet")

never_treated_units = sorted(
    set(panel_ds.unit_ids) - set(pilot_units) - set(rollout_units)
)

summary = {
    "geography": "community_district",
    "frequency": "ME",
    "n_units": len(panel_ds.unit_ids),
    "n_periods": len(panel_ds.periods),
    "n_observations": len(df),
    "total_complaints": int(df["complaint_count"].sum()),
    "cohort_1_pilot": {
        "treatment_date": PILOT_DATE.isoformat(),
        "n_units": len(pilot_units),
        "units": list(pilot_units),
    },
    "cohort_2_citywide": {
        "treatment_date": ROLLOUT_DATE.isoformat(),
        "n_units": len(rollout_units),
        "units": list(rollout_units),
    },
    "never_treated": {
        "n_units": len(never_treated_units),
        "units": never_treated_units,
    },
    "window_start": (
        df.index.get_level_values("period").min().isoformat()
        if hasattr(df.index.get_level_values("period").min(), "isoformat")
        else str(df.index.get_level_values("period").min())
    ),
    "window_end": (
        df.index.get_level_values("period").max().isoformat()
        if hasattr(df.index.get_level_values("period").max(), "isoformat")
        else str(df.index.get_level_values("period").max())
    ),
}
jc.save(
    summary,
    "artifacts/panel_summary.json",
    caption=(
        f"Balanced staggered panel: {summary['n_units']} districts × "
        f"{summary['n_periods']} months, 2 treatment cohorts "
        f"({len(pilot_units)} pilot + {len(rollout_units)} citywide-rollout + "
        f"{len(never_treated_units)} never-treated controls)."
    ),
)
print(summary)

# %% tags=["jc.step", "name=ff_panel", "deps=panel"]
import json
from datetime import date
from pathlib import Path

import jellycell.api as jc
from nyc311.io import load_service_requests
from nyc311.temporal import TreatmentEvent, build_complaint_panel

import re

date_re = re.compile(r"_(\d{4})-\d{2}-\d{2}_(\d{4})-\d{2}-\d{2}_")
records = []
for p in sorted(Path("data/cache").glob("*_rodent_*.csv")):
    if date_re.search(p.name):
        records.extend(load_service_requests(p))

event_spec = json.loads(Path("data/rat_mitigation_events_2023.json").read_text())
cohort_units: dict[str, list[str]] = {"pilot_2023": [], "citywide_2024": []}
for ev in event_spec["events"]:
    cohort_units[ev["cohort"]].append(ev["unit"])
pilot_units = tuple(sorted(cohort_units["pilot_2023"]))
rollout_units = tuple(sorted(cohort_units["citywide_2024"]))

pilot_event = TreatmentEvent(
    name="nyc_containerization_pilot_2023",
    description="Lower-Manhattan pilot: MN 01-09, effective 2023-07-01.",
    treated_units=pilot_units,
    treatment_date=date(2023, 7, 1),
    geography="community_district",
)
rollout_event = TreatmentEvent(
    name="nyc_containerization_citywide_2024",
    description="Citywide residential 1–9-unit rollout, effective 2024-11-12.",
    treated_units=rollout_units,
    treatment_date=date(2024, 11, 12),
    geography="community_district",
)
panel_ds = build_complaint_panel(
    records,
    geography="community_district",
    freq="ME",
    treatment_events=(pilot_event, rollout_event),
)

# Convert nyc311 PanelDataset → factor_factory.tidy.Panel for engine use.
ff_panel = panel_ds.to_factor_factory_panel()
ff_panel.to_parquet("artifacts/ff_panel.parquet")
print("factor_factory Panel:")
print(f"  dimension     = {ff_panel.dimension}")
print(f"  geography     = {ff_panel.geography}")
print(f"  freq          = {ff_panel.freq}")
print(f"  n_units       = {len(ff_panel.unit_ids)}")
print(f"  n_periods     = {len(ff_panel.periods)}")
print(f"  outcome_col   = {ff_panel.outcome_col}")
print(f"  n_events      = {len(ff_panel.treatment_events)}")
for ev in ff_panel.treatment_events:
    print(f"    · {ev.name} @ {ev.treatment_date} ({len(ev.treated_units)} units)")

jc.save(
    {
        "dimension": ff_panel.dimension,
        "geography": ff_panel.geography,
        "freq": str(ff_panel.freq),
        "n_units": len(ff_panel.unit_ids),
        "n_periods": len(ff_panel.periods),
        "outcome_col": ff_panel.outcome_col,
        "treatment_events": [
            {
                "name": e.name,
                "date": e.treatment_date.isoformat() if e.treatment_date else None,
                "n_treated": len(e.treated_units),
            }
            for e in ff_panel.treatment_events
        ],
    },
    "artifacts/ff_panel_summary.json",
    caption="factor_factory.tidy.Panel with 2 cohorts — input to staggered DiD in notebook 03",
)

# %% [markdown]
# **Next:** `02_balance_and_pretrends.py` — covariate balance + the
# parallel-trends visual for both cohorts.
