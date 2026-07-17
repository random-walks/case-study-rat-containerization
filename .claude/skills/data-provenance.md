---
name: data-provenance
description: Every vendored data file needs a `<file>.meta.json` sidecar documenting source, vintage, derivation, and how-to-regenerate. Apply when adding a new data file to `data/` or reviewing a vendored CSV/parquet for reproducibility.
---

# Data provenance sidecars

Every file under `data/` that's committed to git (not in
`data/cache/` which is fetched) needs a `<file>.meta.json` sidecar.

## Why

Future-you opens `data/demographics.csv`, sees 47 columns of ACS codes, and
has no idea if it's B17020 or B17024. Provenance sidecars make that
unambiguous in machine- and human-readable form.

## The schema

```json
{
  "path": "data/demographics.csv",
  "source": {
    "publisher": "U.S. Census Bureau",
    "dataset": "American Community Survey 5-year estimates",
    "tables": ["B17020", "B18101", "B01001"],
    "url": "https://api.census.gov/data/2023/acs/acs5"
  },
  "vintage": "2023 5-year estimates (survey period 2019-2023)",
  "spatial_resolution": "census tract, NYC (5 boroughs)",
  "row_count": 2317,
  "derivation": "Fetched directly from the Census API (see url above) — nyc311 has no ACS-fetching helper. Columns renamed by hand to this repo's convention. Merged with 2020 tract boundaries from nyc-geo-toolkit.",
  "regenerate": "uv run python scripts/refresh_demographics.py",
  "fetched_at": "2026-04-09",
  "checksum_sha256": "<optional — run shasum -a 256 on the file>",
  "license": "Public domain (U.S. government work)"
}
```

## When the file is fetched live (not vendored)

If the file lives under `data/cache/` (gitignored), no sidecar needed —
the regenerate recipe lives in the notebook that fetches:

```python
# %% tags=["jc.load", "name=rodent_raw"]
import jellycell.api as jc
from nyc311.io import load_service_requests
from nyc311.pipeline import bulk_fetch

paths = bulk_fetch(
    complaint_types=("Rodent",),
    start_date="2020-01-01",
    end_date="2024-12-31",
    cache_dir="data/cache/",  # per-borough CSVs; each gets a .meta.json sidecar
)  # network on first run; skips boroughs already cached on subsequent runs
records = [r for p in paths for r in load_service_requests(p)]
jc.save({"n_records": len(records)}, "artifacts/rodent_raw_summary.json",
        caption=f"Fetched {len(records):,} rodent complaints 2020-2024")
```

## When the file is *small enough* to vendor (< 5 MB, unlikely to change)

Commit the file + the sidecar. Example: a hand-curated list of mitigation
events:

```
data/
├── rat_mitigation_events_2023.json       ← 14 KB, hand-curated
└── rat_mitigation_events_2023.json.meta.json
```

## When the file is *large and stable* (> 5 MB, stable vintage)

LFS-track it (see `.gitattributes`) AND write a sidecar. Example:
pre-rendered figures, committed parquet snapshots.

```
artifacts/
├── treatment_panel.parquet           ← LFS, 45 MB
└── treatment_panel.parquet.meta.json
```

## Minimal sidecar for small curated files

```json
{
  "path": "data/rat_mitigation_events_2023.json",
  "source": "Hand-curated from NYC Council press releases, 2023-2024",
  "derivation": "See scripts/curate_events.py; cross-referenced to the NYC Rat Portal dashboard",
  "regenerate": "Re-curate — not fully automated; see notebook 01"
}
```

## Verification

Add to `uv run jellycell lint` a check that every `data/**` non-cache file
has a corresponding `.meta.json`. A skeleton:

```python
# scripts/check_provenance.py
import pathlib, sys
root = pathlib.Path("data")
missing = []
for f in root.rglob("*"):
    if f.is_file() and not f.name.endswith(".meta.json") and f.suffix not in (".gitkeep", ".md"):
        if "cache/" in str(f):
            continue
        if not f.with_suffix(f.suffix + ".meta.json").exists():
            missing.append(str(f))
if missing:
    print("missing .meta.json sidecars:")
    for m in missing: print(" -", m)
    sys.exit(1)
```

## When to invoke this skill

- Adding a new data file to `data/` (not `data/cache/`).
- Reviewing a PR that introduces vendored data.
- Auditing this case study for provenance gaps.
