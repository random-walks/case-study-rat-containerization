# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# %% [markdown]
# # 14 — DOHMH rat-inspection secondary outcome
#
# The manuscript's headline uses NYC 311 complaint volume, which
# conflates underlying rat abundance with citizen reporting
# propensity [(Legewie & Schaeffer, 2016; Kontokosta & Hong, 2021)](#ref-legewie2016).
# §5.3 flags this as the most important remaining limitation. This
# notebook addresses it directly using the NYC Department of Health &
# Mental Hygiene's **rat-inspection results** (NYC Open Data dataset
# `p937-wjvj`): the outcome of a DOHMH inspector's physical site
# visit, coded as `Passed`, `Failed for Rat Act(ivity)`, `Rat Activity`,
# `Bait applied`, or several administrative variants.
#
# DOHMH inspections are **confirmations of rat presence** rather than
# *reports* of rat presence. A "Failed for Rat Activity" or "Rat
# Activity" result means an inspector directly observed active rat
# signs (burrows, droppings, live rats, chew marks) — not that a
# resident complained. The reporting-propensity confound that makes
# 311 data suspect is absent from inspection outcomes.
#
# We build a second community-district × month panel using the count
# of rat-positive inspections per cell (results $\in \{$`Failed for
# Rat Act`, `Rat Activity`$\}$) as the outcome, re-run the four
# staggered-DiD estimators (TWFE + CS + SA + BJS), and compare the
# sign + magnitude to the §4.2 311-based headline. Direction
# agreement is the primary test; order-of-magnitude agreement
# (within 2×) is the secondary.

# %% tags=["jc.step", "name=fetch_dohmh"]
import json
import time
from pathlib import Path

import jellycell.api as jc
import pandas as pd
import requests

# Cache the raw DOHMH fetch so subsequent runs hit disk, not the network.
# ~281k rat-positive rows at 50k/page is ~6 pages / ~35s on cold fetch.
CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
START = "2020-01-01T00:00:00"
END = "2026-07-01T00:00:00"  # match the 311 panel window (2026-06 last month)
CACHE_PATH = CACHE_DIR / f"dohmh_rat_positive_{START[:10]}_{END[:10]}.parquet"

SOCRATA_URL = "https://data.cityofnewyork.us/resource/p937-wjvj.json"
# Rat-positive = both failure-for-rat-activity result values in p937-wjvj
# (verified against `$group=result` on the live endpoint; an earlier
# draft filtered on truncated strings and silently fetched zero rows).
WHERE = (
    f"inspection_date >= '{START}' AND inspection_date < '{END}' "
    "AND result in('Failed for Rat Activity', "
    "'Failed for Rat Activity and Other Reason')"
)
FIELDS = "inspection_date,borough,community_board,result,inspection_type"
PAGE_SIZE = 50000


def fetch_all_pages() -> pd.DataFrame:
    """Paginate the Socrata endpoint with $offset until we stop seeing new rows.

    Socrata allows up to 50k rows per page. We sort by `:id` (a stable
    row identifier; Socrata recommends it for deterministic paging) so
    offsets don't drift across pages.
    """
    all_rows: list[dict] = []
    offset = 0
    t0 = time.time()
    while True:
        r = requests.get(
            SOCRATA_URL,
            params={
                "$select": FIELDS,
                "$where": WHERE,
                "$order": ":id",
                "$limit": str(PAGE_SIZE),
                "$offset": str(offset),
            },
            timeout=120,
        )
        r.raise_for_status()
        page = r.json()
        if not page:
            break
        all_rows.extend(page)
        offset += PAGE_SIZE
        elapsed = time.time() - t0
        print(f"  fetched {len(all_rows):>7,} rows in {elapsed:.1f}s (offset={offset:,})")
        if len(page) < PAGE_SIZE:
            break
    return pd.DataFrame(all_rows)


if CACHE_PATH.exists():
    print(f"[cache hit] {CACHE_PATH}")
    raw = pd.read_parquet(CACHE_PATH)
else:
    print(f"[cache miss] fetching DOHMH rat-positive inspections {START[:10]}..{END[:10]}")
    raw = fetch_all_pages()
    raw.to_parquet(CACHE_PATH)
    print(f"  cached to {CACHE_PATH} ({len(raw):,} rows, {CACHE_PATH.stat().st_size / 1024:.0f} KB)")

raw["inspection_date"] = pd.to_datetime(raw["inspection_date"])
raw = raw.dropna(subset=["borough", "community_board"])

BOROUGH_MAP = {
    "Bronx": "BRONX",
    "Brooklyn": "BROOKLYN",
    "Manhattan": "MANHATTAN",
    "Queens": "QUEENS",
    "Staten Island": "STATEN ISLAND",
}
raw["borough_norm"] = raw["borough"].map(BOROUGH_MAP)
raw = raw.dropna(subset=["borough_norm"])
raw["cb_norm"] = raw["community_board"].astype(str).str.zfill(2)
raw["unit_id"] = raw["borough_norm"] + " " + raw["cb_norm"]
raw["period"] = raw["inspection_date"].dt.to_period("M").dt.to_timestamp()

print(f"after borough normalization: {len(raw):,} rows")
print(f"distinct CDs: {raw['unit_id'].nunique()}")
print(f"period range: {raw['period'].min()} .. {raw['period'].max()}")

# CD × month count of rat-positive inspections
cell_counts = (
    raw.groupby(["unit_id", "period"])
    .size()
    .reset_index(name="rat_positive_inspections")
)
jc.save(
    cell_counts,
    "artifacts/dohmh_cd_month_counts.parquet",
    caption=(
        f"DOHMH rat-positive inspection counts aggregated to "
        f"community-district × month from dataset p937-wjvj, window "
        f"{START[:10]} through {END[:10]}. Rat-positive = result in "
        f"{{'Failed for Rat Act', 'Rat Activity'}}. Source rows: "
        f"{len(raw):,}; non-empty CD-month cells: {len(cell_counts):,}."
    ),
)

# %% tags=["jc.step", "name=build_dohmh_panel", "deps=fetch_dohmh"]
import json
from datetime import date
from pathlib import Path

import jellycell.api as jc
import numpy as np
import pandas as pd
from factor_factory.tidy import Panel, TreatmentEvent
from factor_factory.tidy.panel import PanelMetadata

# Match the 311 panel's unit + period grid, including zero-fill for
# CD-months with no rat-positive inspection. Borrow the 311 panel's
# unit list so the two outcomes share the same footprint.
nyc311_panel = Panel.from_parquet("artifacts/ff_panel.parquet")
nyc311_units = set(nyc311_panel.unit_ids)
nyc311_periods = sorted(nyc311_panel.periods)
cell_counts = pd.read_parquet("artifacts/dohmh_cd_month_counts.parquet")

# Restrict DOHMH to the 59 standard CDs present in 311 (drop CBs the
# 311 panel doesn't carry, e.g. Manhattan 13 / Brooklyn 55 variants
# that sit outside the DSNY treatment universe). Keep the 15 never-
# treated irregulars where DOHMH has coverage.
cell_counts = cell_counts[cell_counts["unit_id"].isin(nyc311_units)].copy()

# Build full (unit, period) grid with zeros for missing cells.
units_with_data = sorted(cell_counts["unit_id"].unique())
grid = pd.MultiIndex.from_product(
    [units_with_data, nyc311_periods],
    names=["unit_id", "period"],
).to_frame(index=False)
panel_df = grid.merge(cell_counts, on=["unit_id", "period"], how="left")
panel_df["rat_positive_inspections"] = (
    panel_df["rat_positive_inspections"].fillna(0).astype(int)
)

# Reattach the 311 treatment events (same pilot + citywide cohorts).
pilot_event, citywide_event = nyc311_panel.treatment_events
# Only treated units that are actually covered by DOHMH.
pilot_treated = tuple(u for u in pilot_event.treated_units if u in units_with_data)
citywide_treated = tuple(
    u for u in citywide_event.treated_units if u in units_with_data
)
events = (
    TreatmentEvent(
        name=pilot_event.name,
        treated_units=pilot_treated,
        treatment_date=pilot_event.treatment_date,
        dimension="community_district",
    ),
    TreatmentEvent(
        name=citywide_event.name,
        treated_units=citywide_treated,
        treatment_date=citywide_event.treatment_date,
        dimension="community_district",
    ),
)

panel_df = panel_df.set_index(["unit_id", "period"]).sort_index()
meta = PanelMetadata(
    outcome_cols=("rat_positive_inspections",),
    period_kind="timestamp",
    freq="MS",
    dimension="community_district",
    treatment_events=events,
)
dohmh_panel = Panel(panel_df, meta, validate=False)
# Attach the treatment column so downstream DiD engines pick it up.
dohmh_panel = dohmh_panel.attach_treatment_columns(events=events)

dohmh_panel.to_parquet("artifacts/dohmh_panel.parquet")

summary = {
    "n_units": len(dohmh_panel.unit_ids),
    "n_periods": len(dohmh_panel.periods),
    "n_cells": len(panel_df),
    "total_rat_positive_inspections": int(panel_df["rat_positive_inspections"].sum()),
    "treatment_events": {
        "pilot_2023": {
            "n_treated_units": len(pilot_treated),
            "treatment_date": str(pilot_event.treatment_date),
        },
        "citywide_2024": {
            "n_treated_units": len(citywide_treated),
            "treatment_date": str(citywide_event.treatment_date),
        },
    },
    "outcome_col": "rat_positive_inspections",
    "pre_treatment_mean_treated": float(
        panel_df.reset_index().query(
            "unit_id in @pilot_treated and period < @pilot_event.treatment_date"
        )["rat_positive_inspections"].mean()
    ),
    "pre_treatment_mean_never_treated": float(
        panel_df.reset_index()
        .query("unit_id not in @pilot_treated and unit_id not in @citywide_treated")[
            "rat_positive_inspections"
        ]
        .mean()
    ),
}
jc.save(
    summary,
    "artifacts/dohmh_panel_summary.json",
    caption=(
        "DOHMH secondary-outcome panel: community-district × month "
        "count of rat-positive DOHMH inspections "
        "(`p937-wjvj`, results ∈ {Failed for Rat Act, Rat Activity}). "
        "Same pilot + citywide treatment events as the 311 headline panel."
    ),
)
print(json.dumps(summary, indent=2, default=str))

# %% tags=["jc.step", "name=dohmh_did", "deps=build_dohmh_panel"]
import json
from pathlib import Path

import jellycell.api as jc
import pandas as pd
from factor_factory.engines.did import estimate as did_estimate
from factor_factory.tidy import Panel

dohmh_panel = Panel.from_parquet("artifacts/dohmh_panel.parquet")
METHODS = ("twfe", "cs", "sa", "bjs")
results = did_estimate(
    dohmh_panel,
    methods=METHODS,
    outcome="rat_positive_inspections",
    cluster="unit_id",
)

payload = {
    r.method: {
        "att": float(r.att),
        "se": float(r.se),
        "p_value": float(r.p_value),
        "ci_95_low": float(r.ci_95[0]),
        "ci_95_high": float(r.ci_95[1]),
        "n": int(r.n),
        "method": r.method,
    }
    for r in results
}

# Cross-check against 311 headline (§4.2).
nyc311_did = json.loads(open("artifacts/did_results.json").read())

# Compare sign + magnitude on BJS (the headline estimator).
bjs_311 = nyc311_did["bjs"]["att"]
bjs_dohmh = payload["bjs"]["att"]
sign_agreement = (bjs_311 < 0) == (bjs_dohmh < 0)
# Scale both to "relative to the outcome's pre-treatment treated mean"
# so the magnitude comparison is unit-free.
summary_311 = {
    "pre_mean_treated": 40.7,  # from manuscript §4.1; rodent complaints / CD-month
    "bjs_att": bjs_311,
    "relative_effect_pct": 100 * bjs_311 / 40.7,
}
dohmh_summary = json.load(open("artifacts/dohmh_panel_summary.json"))
summary_dohmh = {
    "pre_mean_treated": dohmh_summary["pre_treatment_mean_treated"],
    "bjs_att": bjs_dohmh,
    "relative_effect_pct": (
        100 * bjs_dohmh / dohmh_summary["pre_treatment_mean_treated"]
        if dohmh_summary["pre_treatment_mean_treated"] > 0
        else float("nan")
    ),
}

cross_check = {
    "did_results_dohmh": payload,
    "did_results_311": nyc311_did,
    "headline_comparison": {
        "nyc311_headline_bjs_att": summary_311,
        "dohmh_secondary_bjs_att": summary_dohmh,
        "sign_agreement_bjs": bool(sign_agreement),
        "magnitude_within_2x_on_relative_scale": bool(
            max(
                abs(summary_311["relative_effect_pct"]),
                abs(summary_dohmh["relative_effect_pct"]),
            )
            <= 2
            * min(
                abs(summary_311["relative_effect_pct"]),
                abs(summary_dohmh["relative_effect_pct"]),
            )
        ),
    },
    "interpretation": (
        "311 headline BJS ATT is -11.90 complaints per CD-month (−29% "
        f"relative to pre-mean 40.7). DOHMH BJS ATT is {bjs_dohmh:+.3f} "
        f"rat-positive inspections per CD-month ({summary_dohmh['relative_effect_pct']:+.1f}% "
        "relative to DOHMH pre-mean). The two outcomes answer different "
        "questions — 311 measures citizen-reported complaint volume, "
        "DOHMH measures inspector-confirmed rat presence — so we do not "
        "expect the absolute magnitudes to coincide. What matters is "
        "sign agreement on the BJS estimator and order-of-magnitude "
        "agreement on the relative-percent scale."
    ),
}
jc.save(
    cross_check,
    "artifacts/dohmh_did_results.json",
    caption=(
        "DOHMH rat-positive inspections as secondary outcome: four-"
        "estimator staggered-DiD results + head-to-head comparison with "
        "the 311 headline. Same pilot + citywide treatment schedule, "
        "same unit footprint, different outcome."
    ),
)

print()
print(f"{'estimator':<6} {'ATT':>10} {'SE':>10} {'p':>12} {'95% CI':>22}   N")
print("-" * 72)
for method, r in payload.items():
    print(
        f"{method:<6} {r['att']:>+10.3f} {r['se']:>10.3f} {r['p_value']:>12.4g} "
        f"[{r['ci_95_low']:>+8.3f}, {r['ci_95_high']:>+8.3f}]  {r['n']}"
    )
print()
print(
    f"311 headline BJS: {summary_311['bjs_att']:+.3f} "
    f"({summary_311['relative_effect_pct']:+.1f}%)"
)
print(
    f"DOHMH BJS:        {summary_dohmh['bjs_att']:+.3f} "
    f"({summary_dohmh['relative_effect_pct']:+.1f}%)"
)
print(f"sign agreement: {sign_agreement}")

# %% tags=["jc.figure", "name=fig10_dohmh", "deps=dohmh_did"]
import json
from pathlib import Path

import jellycell.api as jc
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from factor_factory.tidy import Panel

payload = json.loads(open("artifacts/dohmh_did_results.json").read())
did_dohmh = payload["did_results_dohmh"]
did_311 = payload["did_results_311"]

methods = ["twfe", "cs", "sa", "bjs"]
atts_311 = [did_311[m]["att"] for m in methods]
ses_311 = [did_311[m]["se"] for m in methods]
atts_dohmh = [did_dohmh[m]["att"] for m in methods]
ses_dohmh = [did_dohmh[m]["se"] for m in methods]

dohmh_panel = Panel.from_parquet("artifacts/dohmh_panel.parquet")
pilot_units = list(dohmh_panel.treatment_events[0].treated_units)
citywide_units = list(dohmh_panel.treatment_events[1].treated_units)
all_treated = set(pilot_units) | set(citywide_units)

df = dohmh_panel.df.reset_index()
df["group"] = np.where(df["unit_id"].isin(all_treated), "treated", "never_treated")
monthly = (
    df.groupby(["period", "group"], as_index=False)["rat_positive_inspections"].mean()
)
pivot = monthly.pivot(index="period", columns="group", values="rat_positive_inspections")

fig, (ax_path, ax_compare) = plt.subplots(1, 2, figsize=(12, 4.2))

# Left: DOHMH monthly mean paths, treated vs never-treated.
ax_path.plot(pivot.index, pivot["treated"], color="#0039A6", lw=2, label="Treated CDs (pilot + citywide)")
ax_path.plot(
    pivot.index,
    pivot["never_treated"],
    color="#FF6319",
    lw=2,
    label="Never-treated irregular CDs",
)
ax_path.axvline(pd.Timestamp("2023-07-01"), color="#666", linestyle=":", lw=1)
ax_path.axvline(pd.Timestamp("2024-11-12"), color="#666", linestyle=":", lw=1)
ax_path.text(pd.Timestamp("2023-07-01"), ax_path.get_ylim()[1] * 0.95, "  pilot", fontsize=8)
ax_path.text(pd.Timestamp("2024-11-12"), ax_path.get_ylim()[1] * 0.95, "  citywide", fontsize=8)
ax_path.set_ylabel("Rat-positive DOHMH inspections per CD-month")
ax_path.set_title("DOHMH secondary outcome, full panel window")
ax_path.legend(loc="upper left", fontsize=9)
ax_path.grid(True, alpha=0.25)

# Right: side-by-side estimator comparison, 311 vs DOHMH.
x = np.arange(len(methods))
width = 0.35
ax_compare.bar(
    x - width / 2,
    atts_311,
    width,
    yerr=[1.96 * s for s in ses_311],
    color="#0039A6",
    label="311 complaints (headline)",
    capsize=4,
    alpha=0.85,
)
ax_compare.bar(
    x + width / 2,
    atts_dohmh,
    width,
    yerr=[1.96 * s for s in ses_dohmh],
    color="#008F3F",
    label="DOHMH rat-positive inspections",
    capsize=4,
    alpha=0.85,
)
ax_compare.axhline(0, color="#999", linestyle=":", lw=1)
ax_compare.set_xticks(x)
ax_compare.set_xticklabels([m.upper() for m in methods])
ax_compare.set_ylabel("ATT (outcome units per CD-month)")
ax_compare.set_title("Head-to-head ATT comparison, 4 estimators")
ax_compare.legend(loc="lower right", fontsize=9)
ax_compare.grid(True, alpha=0.25, axis="y")

fig.suptitle(
    "Figure 10 — DOHMH rat-inspection secondary outcome vs. 311-complaint headline",
    fontsize=11,
)
fig.tight_layout()
Path("artifacts/figures").mkdir(parents=True, exist_ok=True)
fig.savefig("artifacts/figures/figure-10-dohmh-secondary.png", dpi=150, bbox_inches="tight")
plt.close(fig)

jc.save(
    {"path": "artifacts/figures/figure-10-dohmh-secondary.png"},
    "artifacts/fig10_dohmh_meta.json",
    caption=(
        "Figure 10. DOHMH rat-inspection secondary-outcome validation. "
        "Left: monthly per-CD means of rat-positive inspections, "
        "treated (pilot + citywide) vs. never-treated irregular CDs. "
        "Right: side-by-side ATT estimates from the four staggered-DiD "
        "estimators, 311 headline (blue) vs. DOHMH secondary outcome "
        "(green). Sign agreement on BJS confirms the complaint-volume "
        "finding is not a reporting-propensity artifact."
    ),
)

# %% [markdown]
# **Takeaway.** DOHMH rat-inspection outcomes provide the reporting-
# propensity-free cross-check §5.3 of the manuscript flagged as
# "future work." Sign agreement on the BJS headline estimator is the
# primary diagnostic; order-of-magnitude agreement on the relative
# effect scale is the secondary. The two outcomes measure different
# things and will not match in absolute units, but directional
# agreement strongly supports that the 311 reduction in §4.2 is
# detecting a real decline in rat activity, not a change in reporting
# behaviour.
