# Data

## Cache (gitignored)

`data/cache/` holds per-borough NYC 311 Rodent-complaint CSVs fetched via
`nyc311.pipeline.bulk_fetch`. On first run, notebook `01_load_and_preprocess.py`
triggers the fetch (Jan 2020 – Jun 2026, five boroughs, ~10–15 min over the
network). The fetch runs as two windows per borough —
`2020-01-01`→`2024-12-31` and `2025-01-01`→`2026-06-30` — so the older
2020–2024 slices are reused across rebuilds. Each `.csv` ships with a
`.meta.json` sidecar recording row count, SHA-256 checksum, fetch timestamp,
and the filter parameters used.

`data/cache/` also holds the DOHMH rat-inspection cache
`dohmh_rat_positive_<start>_<end>.parquet` (e.g.
`dohmh_rat_positive_2020-01-01_2026-07-01.parquet`), fetched once by notebook
`14_dohmh_secondary_outcome.py` and re-read from disk thereafter. These parquet
files carry no `.meta.json` sidecar — their provenance lives in the notebook's
fetch step.

Subsequent runs short-circuit: the CSVs and parquet already on disk are re-read
and no network calls are made.

## Hand-curated

- `rat_mitigation_events_2023.json` — the containerization-policy rollout
  dates. Sourced from NYC Department of Sanitation press releases and the
  NYC 311 service-request system changelog. Fields: `unit` (community
  district), `event_date` (ISO-8601), `kind` (`"pilot" | "rollout"`),
  `description`.
- `demographics.csv` (not yet committed; optional) — per-district
  population + income covariates from the U.S. Census Bureau American
  Community Survey 5-year table (2019–2023).

## Sources

### 311 Rodent complaints (primary outcome)

NYC Open Data Socrata dataset `erm2-nwe9` (311 Service Requests from
2010 to Present), filtered to `complaint_type = "Rodent"`.

### DOHMH rat inspections (secondary outcome, §4.9)

NYC Open Data Socrata dataset `p937-wjvj` (DOHMH Rodent Inspection
results), filtered to the rat-positive outcomes
`result in ("Failed for Rat Activity", "Failed for Rat Activity and Other
Reason")`. Fetched by notebook `14_dohmh_secondary_outcome.py` as the
inspector-confirmed robustness check on the 311-complaint headline.
