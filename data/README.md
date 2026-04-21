# Data

## Cache (gitignored)

`data/cache/` holds per-borough NYC 311 Rodent-complaint CSVs fetched via
`nyc311.pipeline.bulk_fetch`. On first run, notebook `01_load_and_preprocess.py`
triggers the fetch (Jan 2020 – Dec 2024, five boroughs, ~10–15 min over the
network). Each `.csv` ships with a `.meta.json` sidecar recording row count,
SHA-256 checksum, fetch timestamp, and the filter parameters used.

Subsequent runs short-circuit: the CSVs already on disk are re-read and no
network calls are made.

## Hand-curated

- `rat_mitigation_events_2023.json` — the containerization-policy rollout
  dates. Sourced from NYC Department of Sanitation press releases and the
  NYC 311 service-request system changelog. Fields: `unit` (community
  district), `event_date` (ISO-8601), `kind` (`"pilot" | "rollout"`),
  `description`.
- `demographics.csv` (not yet committed; optional) — per-district
  population + income covariates from the U.S. Census Bureau American
  Community Survey 5-year table (2019–2023).

## Source

NYC Open Data Socrata dataset `erm2-nwe9` (311 Service Requests from
2010 to Present), filtered to `complaint_type = "Rodent"`.
