# Appendix B — Data construction decisions

Every data-construction decision in this paper was made to fit the
NYC 311 Socrata endpoint, the NYC DSNY policy schedule, and the
factor-factory `Panel` contract. This appendix documents the
decisions that affect the identification strategy or the
interpretation of the ATT, so a city staffer replicating the work
can audit each choice independently.

## B.1 Geography: why community district (CD)

**Alternatives considered.** Census tract (~2,300 in NYC), census
block group (~7,000), ZIP code (~180), borough (5), police
precinct (~77).

**Why CD.** The 311 Socrata endpoint attaches a `community_board`
string directly to every complaint; we do not have to geocode
latitude/longitude against tract polygons, which would introduce
geocoding-failure noise and a nontrivial dependency on
`nyc-geo-toolkit`. The containerization rule applies at the
building level, but the *policy-decision unit* is the community
district — DSNY organizes enforcement and compliance reporting at
the CD level, not at the tract or block level. Matching the
identification strategy's geographic unit to the policy-decision
unit avoids an unnecessary aggregation step.

**What this costs.** CDs are politically-drawn boundaries spanning
~100k residents each, so within-CD heterogeneity in residential vs.
commercial mix, baseline rat ecology, and built-environment
characteristics is substantial. A building-level or block-level
analysis would give sharper identification; we note the trade-off
in §5.3 of the main manuscript and flag building-level replication
(via DOB permit + DOF valuation data) as future work.

## B.2 Time window: 2020-01-01 through 2026-06-30

**Choice of start date.** 2020-01-01 captures roughly three years
of pre-pilot data (2020-01 through 2023-06), which is the maximum
reasonable pre-period to balance against the 36-month post-window
for the pilot cohort. Going further back (2018–2019) would
introduce pre-COVID level differences that the CD × month fixed
effects can absorb but which make the pre-trend visual in Figure 1
harder to interpret.

**Choice of end date.** 2026-06-30 is the most recent quarter
available at the time of manuscript finalization. The citywide
cohort needs as much post-window as we can give it; the 20-month
post-window in the current panel is thin but workable. A follow-up
paper with two more years of data would substantially tighten the
citywide-cohort CIs.

**Why we combined the 2020-2024 and 2025-2026 fetches.** The
Socrata `bulk_fetch` utility issues independent per-borough calls
per date range; we fetched in two slices (2020–2024 ten months
ago, 2025–2026 for this revision) because the 2025 records were
still being ingested by NYC Open Data during the original run. The
notebook 01 pipeline concatenates both slices, deduplicates on
`complaint_id`, and emits a single balanced CD × month panel.

## B.3 Frequency: why monthly

**Alternatives considered.** Daily, weekly, monthly, quarterly.

**Why monthly.** The containerization rule's enforcement is monthly
(DSNY cites, processes, and follows up on a monthly cycle; the
compliance KPIs DSNY publishes are monthly aggregates). Monthly
aggregation also keeps the panel size manageable (5,772 cells) and
the CD-level monthly complaint mean large enough (51.1 complaints
per CD-month averaged across pre-treatment treated units, and
meaningful variance even in the lowest-volume CDs) to support
large-sample inference.

Daily or weekly aggregation would introduce substantial
day-of-week seasonality (Monday complaints are higher than Sunday
complaints, and the weekday-weekend mix drifts with month-of-year)
without improving identification; quarterly aggregation would cost
us event-study granularity without buying anything.

## B.4 Treatment-schedule spec (`rat_mitigation_events_2023.json`)

The spec maps every community district to an event date (if
treated) or leaves it absent (if never-treated). The schedule has
three cohorts in total:

**Cohort 1 — Pilot, 2023-07-01**. Nine lower-Manhattan CDs:
MN 01–09. Source: [NYC DSNY (2023)](../../MANUSCRIPT.md#ref-nyc2023)
press release dated 2023-06-15; rule effective 2023-07-01.

**Cohort 2 — Citywide residential 1–9 units, 2024-11-12**. Fifty
remaining "standard" CDs: BX 01–12, BK 01–18, MN 10–12, QN 01–14,
SI 01–03. Source: [NYC DSNY (2024)](../../MANUSCRIPT.md#ref-nyc2024)
agency policy brief dated 2024-10-01; 16 RCNY Chapter 1 rule
effective 2024-11-12. This is the first date on which residential
buildings citywide were required to containerize; subsequent phases
applied to larger building categories but are either outside our
panel window or partially covered at the margin.

**Never-treated — 15 "irregular" CDs**. Airports (JFK = QN 82,
LGA = QN 81), parks and islands (Floyd Bennett Field = QN 84,
Rikers Island, Randall's Island = MN 64, Prall's Island = SI 95),
cemeteries (Green-Wood = BK 55), BoE-only districts (BX 26–28), and
Unspecified geocoding-failure rows (one per borough, five total).
These CDs are irregular by construction —
the rule is not applicable to non-residential / non-commercial land
use. Treating them as never-treated is defensible rather than
arbitrary.

## B.5 Outcome: `complaint_count`

The `complaint_count` column in the `PanelDataset` is the raw
count of 311 Rodent service requests with `created_date` in the
cell's month. No normalization by population or land area.

**Why not per-capita?** The CD × month fixed effects absorb any
time-invariant population differences. Per-capita scaling would
introduce division by a noisy ACS population estimate and would
not change the within-CD identifying variation. The 311 pipeline
in this paper is designed around raw counts specifically.

**Why not `complaints_per_1000_residents`?** Same reasoning; plus
the "per 1000 residents" transform is undefined for the 15
never-treated irregular CDs (airports have zero residents), and
dropping those CDs removes the control pool.

## B.6 Reporting-propensity adjustment: none, and why

We do NOT adjust the outcome for reporting propensity (e.g., by
normalizing rat complaints by total 311 complaints in the cell).
Two reasons:

1. The CD fixed effects absorb time-invariant reporting
   differences.
2. The time fixed effects absorb citywide drift in reporting
   propensity (e.g., if NYC residents file more of every type of
   complaint in 2024 than in 2020, the $\gamma_t$ terms capture
   that).

What the fixed effects *cannot* absorb is a reporting-propensity
change that correlates with treatment — if containerization makes
residents feel the city is responsive and they file more
complaints, that's a negative bias against finding an effect. We
discuss this in §5.3 of the main manuscript.

## B.7 The 377,950 → 232,447 sample-size correction

An earlier draft of this paper reported 377,950 total Rodent
complaints; this draft reports 232,447. The discrepancy is a cache-
loading bug that crept into notebook 01 across two iterations:

1. The `bulk_fetch` utility caches Socrata fetches by
   `{borough}_{topic}_{start}_{end}_{page_size}.csv`. An early fetch
   had been done for the 2020–2021 slice *separately* (different
   end-date in the filename); a later fetch for the 2020–2024 slice
   overlaid the same borough-topic but with a wider window.
2. Notebook 01's record-loading loop globbed `*_rodent_*.csv`
   and concatenated everything, double-counting the overlapping
   2020–2021 period.
3. The result was a sample size inflated by roughly the
   2020–2021 contribution — 377,950 observed vs. the true 232,447.

The fix was to purge the stale 2020–2021 cache files (they're
redundant given the 2020–2024 superset) and to add a deduplication
pass in the cache-loader. The record count in the current paper is
the deduplicated figure.

**This has negligible effect on the ATT estimates themselves**
because duplicated observations uniformly inflate both treated and
control cells, so the DiD coefficient is largely unchanged. What
changed are the panel-summary statistics (total complaints,
per-CD-month means) and — by extension — the reporting-propensity
discussion in §5.3.

## B.8 What's in `data/cache/` and what isn't

**Committed to git**: `data/rat_mitigation_events_2023.json`
(the treatment schedule) and `data/README.md` (this appendix's
precursor).

**Gitignored**: `data/cache/*.csv` (raw Socrata responses), the
`.jellycell/cache/` directory (jellycell's manifest store), and
`site/` (the jellycell-rendered HTML catalogue). The raw CSV cache
would add ~60 MB to the repo and is trivially reconstructable via
the `nyc311.pipeline.bulk_fetch()` call in notebook 01's first cell.

A reader attempting to reproduce the analysis starts from `uv sync`
followed by `for nb in notebooks/[0-9]*.py; do uv run jellycell run
"$nb"; done`, which runs all 14 notebooks in order and fetches the
underlying data from NYC Open Data on first pass (~10–15 minutes
over Socrata) and from the local cache on subsequent runs (~30
seconds).
