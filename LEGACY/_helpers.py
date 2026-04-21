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


def _load_records(start_year: int | None = None, end_year: int | None = None):
    """Load vendored Rodent records, optionally filtered by start year of file.

    Filename pattern: `<borough>_rodent_<YYYY-MM-DD>_<YYYY-MM-DD>_<chunk>.csv`
    where the borough may contain underscores (e.g. `staten_island`).
    """
    import re
    from nyc311.io import load_service_requests

    csv_files = sorted(vendored_cache_dir().glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError("No vendored Rodent CSVs in data/cache/.")
    date_re = re.compile(r"_(\d{4})-\d{2}-\d{2}_(\d{4})-\d{2}-\d{2}_")
    records = []
    for p in csv_files:
        m = date_re.search(p.name)
        if not m:
            continue  # skip files whose date range we can't parse
        file_start, file_end = int(m.group(1)), int(m.group(2))
        if start_year is not None and file_end < start_year:
            continue
        if end_year is not None and file_start > end_year:
            continue
        records.extend(load_service_requests(p))
    return records


def _build_panel_dataset(records, label: str):
    """Wrap build_complaint_panel + treatment event in one call."""
    from nyc311.temporal import build_complaint_panel
    from nyc311.temporal._models import TreatmentEvent

    treatment = TreatmentEvent(
        name=f"rat_containerization_{label}",
        description="Manhattan CDs 01-09 pilot, June 2024",
        treated_units=TREATED_UNITS,
        treatment_date=TREATMENT_DATE,
        geography="community_district",
    )
    return build_complaint_panel(
        records,
        geography="community_district",
        freq="ME",
        treatment_events=(treatment,),
    )


def load_or_build_panel() -> pd.DataFrame:
    """Build the 2024 panel from vendored Rodent CSVs; cache as parquet."""
    panel_path = DATA_DIR / "panel.parquet"
    if panel_path.exists():
        return pd.read_parquet(panel_path)

    print("  building 2024 panel from vendored CSVs...")
    records = _load_records(start_year=2024, end_year=2024)
    print(f"  {len(records):,} records loaded")
    panel = _build_panel_dataset(records, "2024")
    df = panel.to_dataframe()
    df.to_parquet(panel_path)
    print(f"  panel cached: {panel_path}")
    return df


def load_or_build_panel_dataset(*, multi_year: bool = False):
    """Return the raw PanelDataset (needed by spatial_lag_model + others)."""
    label = "multi_year" if multi_year else "2024"
    print(f"  building PanelDataset ({label})...")
    if multi_year:
        records = _load_records(start_year=2022, end_year=2024)
    else:
        records = _load_records(start_year=2024, end_year=2024)
    print(f"  {len(records):,} records loaded")
    return _build_panel_dataset(records, label)


def load_or_build_multi_year_panel() -> pd.DataFrame:
    """Build the 2022-2024 panel (for multi-year parallel-trends test)."""
    panel_path = DATA_DIR / "panel_multi_year.parquet"
    if panel_path.exists():
        return pd.read_parquet(panel_path)

    print("  building 2022-2024 panel from vendored CSVs...")
    records = _load_records(start_year=2022, end_year=2024)
    print(f"  {len(records):,} records loaded across 2022-2024")
    panel = _build_panel_dataset(records, "multi_year")
    df = panel.to_dataframe()
    df.to_parquet(panel_path)
    print(f"  multi-year panel cached: {panel_path}")
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
