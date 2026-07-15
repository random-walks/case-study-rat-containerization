---
name: committed-tearsheets
description: Stable template_overrides pattern so committed tearsheets regenerate byte-identically. Apply when setting up the manuscripts/ dir or reviewing why `jellycell render` produces git-noisy diffs.
---

# Committed tearsheets, byte-identical regen

This case study ships the following **committed** files (repo root):

```
manuscripts/
├── FINDINGS.md              ← auto-generated, committed
├── tearsheets/
│   ├── 01_load.md           ← auto-generated per-notebook, committed
│   ├── 02_balance.md
│   └── …
└── MANUSCRIPT.md            ← hand-authored paper, committed
artifacts/
├── *.json                    ← engine results, committed
├── *.parquet                 ← data, LFS-tracked
└── figures/*.png             ← plots, LFS-tracked
```

## The stable-override pattern

**Important**: jellycell 1.3.5 exposes `jc.save`, `jc.load`, `jc.table`,
`jc.figure` — there is NO `jellycell.tearsheets.findings()` Python function.
Per-notebook tearsheet rendering happens via the `jellycell export tearsheet`
CLI (invoked by `uv run jellycell render`).

For the committed `manuscripts/FINDINGS.md` (summary across the whole
study), use `_helpers.reporting.emit_findings_markdown()`:

```python
from _helpers.reporting import emit_findings_markdown

emit_findings_markdown(
    project="case-study-rat-containerization",
    results={
        "twfe": {"att": -15.29, "se": 2.35, "ci_95": [-19.90, -10.69], "p": "<.001"},
        "cs":   {"att": -12.20, "se": 1.88, "ci_95": [-15.89,  -8.51], "p": "<.001"},
        "sa":   {"att": -12.20, "se": 1.88, "ci_95": [-15.89,  -8.51], "p": "<.001"},
        "bjs":  {"att": -15.29, "se": 2.35, "ci_95": [-19.90, -10.69], "p": "<.001"},
    },
    out_path="manuscripts/FINDINGS.md",
    # Pinned stable invariants — bump only per release, never per run:
    author="Blaise Albis-Burdige",
    author_url="https://blaiseab.com",
    month_year="April 2026",
    version="2.0.0",
    summary="Four-estimator DiD on 2020-2024 nyc311 Rodent panel. Pre-trends rejected; headline framed as upper bound.",
)
```

**Rule**: every field that would be nondeterministic → pinned to a stable literal. The result is a `FINDINGS.md` whose git diff between runs is empty unless the underlying `results` numbers changed.

Per-notebook tearsheets (`manuscripts/tearsheets/*.md`) are exported via
the CLI, which is byte-stable by construction (no timestamps in the template):

```bash
uv run jellycell export tearsheet notebooks/03_main_effects.py \
    --output manuscripts/tearsheets/03_main_effects.md
```

## Canonical overrides dict

```python
STABLE_OVERRIDES = {
    "project": "case-study-rat-containerization",
    "generated_at": "stable",
    "hostname": "showcase-runner",  # historical value, intentional — baked into committed tearsheets; changing it dirties every regen
    "author": "Blaise Albis-Burdige",
    "author_url": "https://blaiseab.com",
    "month_year": "April 2026",   # bump per release, not per run
    "version": "2.0.0",
}
```

Keep one `STABLE_OVERRIDES` constant at the top of
`manuscripts/_render_all.py` or `06_synthesis.py`.

## Byte-identical regen check

Part of `uv run jellycell lint` should be:

```bash
cp manuscripts/FINDINGS.md /tmp/before.md
uv run jellycell render
diff -u /tmp/before.md manuscripts/FINDINGS.md
# empty diff expected
```

If the diff isn't empty, find the non-stable override and pin it. Common
culprits: `datetime.now()`, `socket.gethostname()`, `uuid.uuid4()`,
`random.seed(None)`, floating-point last-digit drift from `numpy`
(set `np.random.seed(42)` at the top of every notebook).

## Floating-point determinism

Stable overrides aren't enough — the *underlying numbers* also need to be
deterministic. Seed every random number generator at the top of every
notebook:

```python
import numpy as np
import random

np.random.seed(42)
random.seed(42)
```

For bootstrap / permutation tests:

```python
from factor_factory.engines.diagnostics import bootstrap_ci

ci = bootstrap_ci(panel, statistic=lambda p: p.mean(), n_boot=1000, seed=42)
```

For parallel execution (some engines use `joblib`):

```python
result = did_estimate(panel, ..., n_jobs=1)  # serialized = reproducible
```

## LFS-tracked binaries — separate concern

Figures, parquet, feather, geojson are LFS-tracked (see `.gitattributes`).
LFS hashes the full file, so committing a figure that rendered
deterministically produces the same LFS pointer. Seed your plots:

```python
import matplotlib.pyplot as plt
plt.rcParams["svg.hashsalt"] = "showcase"   # stable SVG IDs (historical salt value, intentional — keep as-is)
# or for PNG: matplotlib is already deterministic if data + style are fixed
```

## Tearsheets ≠ the paper

- `FINDINGS.md` and `tearsheets/*.md` = auto-generated, byte-identical, committed.
- `MANUSCRIPT.md` = hand-authored paper prose (see `paper-cadence` skill), never templated.
- `AUDIT.md` = pragmatic self-critique, hand-authored, bullet-list voice.

Do not hand-edit `FINDINGS.md` — edits get overwritten on next render. Put
prose in `MANUSCRIPT.md`; put table/number generation logic in the notebook
that emits the `artifacts/*.json` the tearsheet reads.

## When to invoke this skill

- Setting up the `manuscripts/` dir.
- Seeing git noise in `FINDINGS.md` after `uv run jellycell render` with no real changes.
- Reviewing a PR that edits `FINDINGS.md` — reject hand edits, redirect to notebook changes.

## When NOT to invoke this skill

- `README.md` or `AUDIT.md` — both are hand-authored, no templating involved.
- `MANUSCRIPT.md` — hand-authored, follows `paper-cadence` skill instead.
