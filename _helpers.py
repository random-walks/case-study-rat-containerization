"""Rat-containerization showcase helpers.

Builds the 2024 monthly panel from the vendored real Rodent data, with
the staggered treatment indicator for the June 2024 Manhattan pilot.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"

# Real treatment timeline (matches upstream): pilot June 2024 in lower
# Manhattan CDs 01–09; citywide enforcement begins Nov 12, 2024.
TREATED_UNITS: tuple[str, ...] = tuple(f"MANHATTAN 0{i}" for i in range(1, 10))
TREATMENT_DATE = date(2024, 6, 1)


def vendored_cache_dir() -> Path:
    return DATA_DIR / "cache"


def load_demographics() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "demographics.csv", index_col="unit_id")


def load_or_build_panel() -> pd.DataFrame:
    """Build the panel from vendored 2024 Rodent CSVs; cache as parquet."""
    panel_path = DATA_DIR / "panel.parquet"
    if panel_path.exists():
        return pd.read_parquet(panel_path)

    from nyc311.io import load_service_requests
    from nyc311.temporal import build_complaint_panel
    from nyc311.temporal._models import TreatmentEvent

    csv_files = sorted(vendored_cache_dir().glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(
            "No vendored Rodent CSVs. Re-fetch via:\n"
            "  uv run python -c 'from nyc311.pipeline import bulk_fetch; "
            "bulk_fetch(complaint_types=(\"Rodent\",), start_date=\"2024-01-01\", "
            "end_date=\"2024-12-31\", cache_dir=\"data/cache\")'"
        )

    print(f"  loading {len(csv_files)} cached CSVs...")
    records = []
    for p in csv_files:
        records.extend(load_service_requests(p))
    print(f"  {len(records):,} records loaded")

    treatment = TreatmentEvent(
        name="rat_containerization_pilot",
        description="Manhattan CDs 01-09 pilot, June 2024",
        treated_units=TREATED_UNITS,
        treatment_date=TREATMENT_DATE,
        geography="community_district",
    )

    panel = build_complaint_panel(
        records,
        geography="community_district",
        freq="ME",
        treatment_events=(treatment,),
    )
    df = panel.to_dataframe()
    df.to_parquet(panel_path)
    print(f"  panel cached: {panel_path}")
    return df


def add_treatment_indicator(panel: pd.DataFrame) -> pd.DataFrame:
    """Compute the binary treatment indicator (district treated AND post-date)."""
    df = panel.copy()
    units = df.index.get_level_values("unit_id")
    periods = df.index.get_level_values("period")
    period_dt = pd.to_datetime(periods.astype(str))
    treated_unit = units.isin(TREATED_UNITS)
    post_treatment = period_dt >= pd.Timestamp(TREATMENT_DATE)
    df["treated_unit"] = treated_unit.astype(int)
    df["post"] = post_treatment.astype(int)
    df["treatment"] = (treated_unit & post_treatment).astype(int)
    return df
