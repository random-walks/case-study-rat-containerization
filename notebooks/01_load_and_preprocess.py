# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# %% [markdown]
# # 01 — Load and preprocess
#
# Fetches (or re-reads from cache) NYC 311 **Rodent** complaints for the
# 2020-01-01 → 2024-12-31 window, aggregates them into a balanced
# community-district × month panel, and emits a
# `factor_factory.tidy.Panel` ready for DiD estimation.
#
# **Treatment**: NYC Department of Sanitation mandatory-containerization
# pilot launched 2023-07-01 in lower Manhattan community districts MN 01-09.
# Control: the remaining ~50 community districts across the five boroughs.
#
# First-run fetch takes ~10–15 minutes; subsequent runs hit the local CSV
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
END = "2024-12-31"

# Fetch on first run; deterministic filenames so subsequent runs skip.
print(f"bulk_fetch(Rodent, {START} → {END}) to {CACHE_DIR}...")
paths = bulk_fetch(
    complaint_types=("Rodent",),
    start_date=START,
    end_date=END,
    cache_dir=CACHE_DIR,
)
print(f"  {len(paths)} borough files on disk")

# Load all cached Rodent CSVs.
date_re = re.compile(r"_(\d{4})-\d{2}-\d{2}_(\d{4})-\d{2}-\d{2}_")
records = []
for p in sorted(CACHE_DIR.glob("*_rodent_*.csv")):
    m = date_re.search(p.name)
    if not m:
        continue
    records.extend(load_service_requests(p))
print(f"  {len(records):,} rodent complaint records loaded")

summary = {
    "window_start": START,
    "window_end": END,
    "n_records": len(records),
    "n_borough_files": len(paths),
}
jc.save(summary, "artifacts/record_summary.json",
        caption=f"Loaded {len(records):,} NYC 311 Rodent records, {START} → {END}")

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

# Hand-curated treatment event file.
events_path = Path("data/rat_mitigation_events_2023.json")
event_spec = json.loads(events_path.read_text())
TREATED_UNITS = tuple(sorted({e["unit"] for e in event_spec["events"]}))
TREATMENT_DATE = date(2023, 7, 1)

treatment = TreatmentEvent(
    name="nyc_rat_containerization_2023_pilot",
    description=event_spec["description"],
    treated_units=TREATED_UNITS,
    treatment_date=TREATMENT_DATE,
    geography="community_district",
)

panel_ds = build_complaint_panel(
    records,
    geography="community_district",
    freq="ME",
    treatment_events=(treatment,),
)

# Persist as parquet so downstream notebooks can skip the build.
df = panel_ds.to_dataframe()
Path("artifacts").mkdir(exist_ok=True)
df.to_parquet("artifacts/panel_long.parquet")

summary = {
    "geography": "community_district",
    "frequency": "ME",
    "n_units": len(panel_ds.unit_ids),
    "n_periods": len(panel_ds.periods),
    "n_observations": len(df),
    "total_complaints": int(df["complaint_count"].sum()),
    "treated_units": list(TREATED_UNITS),
    "n_treated_units": len(TREATED_UNITS),
    "treatment_date": TREATMENT_DATE.isoformat(),
    "window_start": df.index.get_level_values("period").min().isoformat() if hasattr(df.index.get_level_values("period").min(), "isoformat") else str(df.index.get_level_values("period").min()),
    "window_end": df.index.get_level_values("period").max().isoformat() if hasattr(df.index.get_level_values("period").max(), "isoformat") else str(df.index.get_level_values("period").max()),
}
jc.save(summary, "artifacts/panel_summary.json",
        caption=f"Balanced panel: {summary['n_units']} districts × {summary['n_periods']} months "
                f"({summary['n_treated_units']} treated, t_0={summary['treatment_date']})")
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
TREATED_UNITS = tuple(sorted({e["unit"] for e in event_spec["events"]}))
TREATMENT_DATE = date(2023, 7, 1)
treatment = TreatmentEvent(
    name="nyc_rat_containerization_2023_pilot",
    description=event_spec["description"],
    treated_units=TREATED_UNITS,
    treatment_date=TREATMENT_DATE,
    geography="community_district",
)
panel_ds = build_complaint_panel(
    records, geography="community_district", freq="ME",
    treatment_events=(treatment,),
)

# Convert nyc311 PanelDataset → factor_factory.tidy.Panel for engine use.
ff_panel = panel_ds.to_factor_factory_panel()
ff_panel.to_parquet("artifacts/ff_panel.parquet")
print("factor_factory Panel:")
print(f"  dimension   = {ff_panel.dimension}")
print(f"  geography   = {ff_panel.geography}")
print(f"  freq        = {ff_panel.freq}")
print(f"  n_units     = {len(ff_panel.unit_ids)}")
print(f"  n_periods   = {len(ff_panel.periods)}")
print(f"  outcome_col = {ff_panel.outcome_col}")

jc.save(
    {
        "dimension": ff_panel.dimension,
        "geography": ff_panel.geography,
        "freq": str(ff_panel.freq),
        "n_units": len(ff_panel.unit_ids),
        "n_periods": len(ff_panel.periods),
        "outcome_col": ff_panel.outcome_col,
        "treatment_events": [e.name for e in ff_panel.treatment_events],
    },
    "artifacts/ff_panel_summary.json",
    caption="factor_factory.tidy.Panel — input to DiD engines in notebook 03",
)

# %% [markdown]
# **Next:** `02_balance_and_pretrends.py` — covariate balance + the
# parallel-trends visual.
