# 01 — Load and preprocess

> **Tearsheet** for [`notebooks/01_load_and_preprocess.py`](../../notebooks/01_load_and_preprocess.py) · [HTML report](../../site/01_load_and_preprocess.html) · last run `2026-07-15T18:30:30+00:00`

Fetches (or re-reads from cache) NYC 311 **Rodent** complaints for the
2020-01-01 → END window (see START/END below), aggregates them into a balanced
community-district × month panel, and emits a
`factor_factory.tidy.Panel` ready for staggered DiD estimation.

**Treatment (two cohorts)**:

1. **Pilot** — MN 01-09 (nine lower-Manhattan community districts),
   effective 2023-07-01. DSNY mandatory containerization for both
   commercial and residential buildings on these corridors.
2. **Citywide rollout** — 50 additional standard community districts
   across the remaining four boroughs + upper Manhattan, effective
   2024-11-12. Citywide rule for residential 1–9-unit buildings.

The 15 never-treated districts are airports/parks/cemeteries
(district number ≥ 20) and five "Unspecified" geocoding-failure
districts; they serve as the never-treated control group for
Callaway-Sant'Anna. Staggered-robust estimators exploit the two-
cohort variation so we are no longer vulnerable to the single-cohort
pathology that made TWFE and BJS mechanically coincide in the
2023-only specification.

First-run fetch is ~15 minutes; subsequent runs hit the local CSV
cache under `data/cache/`. See `data/README.md` for provenance.

**Loaded 232,447 NYC 311 Rodent records, 2020-01-01 → 2026-06-30**

| field | value |
| --- | --- |
| `window_start` | 2020-01-01 |
| `window_end` | 2026-06-30 |
| `n_records` | `232447` |
| `n_borough_files` | `10` |
| `slices` | `['2020-01-01..2024-12-31', '2025-01-01..2026-06-30']` |


**Balanced staggered panel: 74 districts × 78 months, 2 treatment cohorts (9 pilot + 50 citywide-rollout + 15 never-treated controls).**

| field | value |
| --- | --- |
| `geography` | community_district |
| `frequency` | ME |
| `n_units` | `74` |
| `n_periods` | `78` |
| `n_observations` | `5772` |
| `total_complaints` | `232447` |
| `cohort_1_pilot.treatment_date` | 2023-07-01 |
| `cohort_1_pilot.n_units` | `9` |
| `cohort_1_pilot.units` | `[9 items]` |
| `cohort_2_citywide.treatment_date` | 2024-11-12 |
| `cohort_2_citywide.n_units` | `50` |
| `cohort_2_citywide.units` | `[50 items]` |
| `never_treated.n_units` | `15` |
| `never_treated.units` | `[15 items]` |
| `window_start` | 2020-01 |
| `window_end` | 2026-06 |


**Ff panel.parquet.meta**

| field | value |
| --- | --- |
| `outcome_cols` | `['complaint_count']` |
| `period_kind` | timestamp |
| `freq` | MS |
| `dimension` | community_district |
| `treatment_events` | `[{'name': 'nyc_containerization_pilot_2023', 'description': 'Lower-Manhattan pilot: MN 01-09, effective 2023-07-01.', 'treated_units': ['MANHATTAN 01', 'MANHATTAN 02', 'MANHATTAN 03', 'MANHATTAN 04', 'MANHATTAN 05', 'MANHATTAN 06', 'MANHATTAN 07', 'MANHATTAN 08', 'MANHATTAN 09'], 'treatment_date': '2023-07-01', 'period_value': None, 'dimension': 'community_district', 'kind': 'binary', 'intensity': None, 'arm': None, 'metadata': None}, {'name': 'nyc_containerization_citywide_2024', 'description': 'Citywide residential 1–9-unit rollout, effective 2024-11-12.', 'treated_units': ['BRONX 01', 'BRONX 02', 'BRONX 03', 'BRONX 04', 'BRONX 05', 'BRONX 06', 'BRONX 07', 'BRONX 08', 'BRONX 09', 'BRONX 10', 'BRONX 11', 'BRONX 12', 'BROOKLYN 01', 'BROOKLYN 02', 'BROOKLYN 03', 'BROOKLYN 04', 'BROOKLYN 05', 'BROOKLYN 06', 'BROOKLYN 07', 'BROOKLYN 08', 'BROOKLYN 09', 'BROOKLYN 10', 'BROOKLYN 11', 'BROOKLYN 12', 'BROOKLYN 13', 'BROOKLYN 14', 'BROOKLYN 15', 'BROOKLYN 16', 'BROOKLYN 17', 'BROOKLYN 18', 'MANHATTAN 10', 'MANHATTAN 11', 'MANHATTAN 12', 'QUEENS 01', 'QUEENS 02', 'QUEENS 03', 'QUEENS 04', 'QUEENS 05', 'QUEENS 06', 'QUEENS 07', 'QUEENS 08', 'QUEENS 09', 'QUEENS 10', 'QUEENS 11', 'QUEENS 12', 'QUEENS 13', 'QUEENS 14', 'STATEN ISLAND 01', 'STATEN ISLAND 02', 'STATEN ISLAND 03'], 'treatment_date': '2024-11-12', 'period_value': None, 'dimension': 'community_district', 'kind': 'binary', 'intensity': None, 'arm': None, 'metadata': None}]` |
| `weights_col` | `null` |
| `record_count` | `5772` |
| `provenance.data_source` | NYC Open Data — 311 Service Requests (Socrata erm2-nwe9) |
| `provenance.license` | CC0-1.0 |
| `provenance.ethics_note` | `null` |
| `provenance.citation` | https://opendata.cityofnewyork.us/ |
| `provenance.creator` | nyc311.temporal.PanelDataset |
| `provenance.dataset_version` | `null` |
| `provenance.created_at` | `null` |

**factor_factory.tidy.Panel with 2 cohorts — input to staggered DiD in notebook 03**

| field | value |
| --- | --- |
| `dimension` | community_district |
| `geography` | community_district |
| `freq` | MS |
| `n_units` | `74` |
| `n_periods` | `78` |
| `outcome_col` | complaint_count |
| `treatment_events` | `[{'name': 'nyc_containerization_pilot_2023', 'date': '2023-07-01', 'n_treated': 9}, {'name': 'nyc_containerization_citywide_2024', 'date': '2024-11-12', 'n_treated': 50}]` |


**Next:** `02_balance_and_pretrends.py` — covariate balance + the
parallel-trends visual for both cohorts.

---

*Auto-generated by `jellycell export tearsheet notebooks/01_load_and_preprocess.py`. Regenerating overwrites this file — for hand-authored writeups put a `.md` at the root of `manuscripts/` instead of under `tearsheets/`.*
