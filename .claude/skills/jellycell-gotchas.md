---
name: jellycell-gotchas
description: Historical jellycell 1.3.x gotchas — most fixed upstream by 1.3.5 / 1.4.0. Keep the inline-imports pattern (safer across versions) and the stable-overrides advice. Apply when authoring jupytext percent-format notebooks.
---

# jellycell gotchas (most now fixed)

All 7 of the original 1.3-era gotchas filed upstream have been **closed
and released**. Fixes landed in jellycell 1.3.5 (patch bumps for bugs) and
1.4.0 (new `jellycell.tearsheets` Python API + `deps=` docs fix).

| # | Issue | Fixed in | Notes |
|---|---|---|---|
| 10 | `jc.setup` cells get cached | 1.3.5 | Inline-imports pattern still recommended for simplicity |
| 11 | `jc.figure(path)` path-only | 1.3.5 | Native `jc.figure("path/to.png")` now works |
| 12 | export tearsheet path resolution | 1.3.5 | — |
| 13 | pyarrow not in default deps | 1.3.5 | Pulled by `[server]` extra |
| 14 | `jc.table` mixed-dtype crash | 1.3.5 | Still cast `<.001`-style columns to `str` to be safe |
| 15 | Export artifact filtering | 1.3.5 | — |
| 24 | Python `tearsheets.findings` API | 1.4.0 | Prefer `jellycell.tearsheets.findings()` over the `_helpers` fallback |
| 25 | `deps=a,b,c` rejected by nbformat | 1.4.0 | Use one `deps=<name>` tag per dep |

## 1. `jc.setup` cells get cached → re-run imports break ([#10](https://github.com/random-walks/jellycell/issues/10) — FIXED in 1.3.5)

**Symptom (historical)**: second run of a notebook fails with `NameError: 'pd' is not defined` even though the first cell imported pandas.

**Still-recommended pattern**: **inline imports in every cell that needs them**. Even though 1.3.5+ caches correctly, inline imports make notebooks maximally portable and keep per-cell dependencies explicit — exactly what the content-hash cache wants.

```python
# BAD — this will break on re-run if tagged jc.setup
# %% tags=["jc.setup"]
import pandas as pd
import jellycell.api as jc

# %% tags=["jc.load", "name=data"]
df = pd.read_parquet("data/cache/foo.parquet")  # NameError on re-run
```

```python
# GOOD — inline imports in every cell
# %% tags=["jc.load", "name=data"]
import pandas as pd
import jellycell.api as jc
df = pd.read_parquet("data/cache/foo.parquet")
jc.save(df, "artifacts/data.parquet", caption="Loaded panel")
```

## 2. `jc.figure(path)` rejects path-only args ([#11](https://github.com/random-walks/jellycell/issues/11) — FIXED in 1.3.5)

Native `jc.figure("path/to.png", caption="…")` now works in 1.3.5+. The `IPython.display.Image(path)` pattern still works as a fallback and is used in some committed notebooks; migrating is a refactor, not a bug fix. Use whichever reads cleanest.

```python
# %% tags=["jc.figure", "name=fig3_event_study"]
from IPython.display import Image
Image("artifacts/figures/figure-3-event-study.png")
```

## 3. `pyarrow` missing from default deps ([#13](https://github.com/random-walks/jellycell/issues/13))

**Symptom**: `ImportError: pyarrow is required for parquet support`.

**Workaround**: we pin `pyarrow>=18` in `[project.dependencies]` (not optional). Installed by default.

## 4. `jc.table` on mixed-dtype column crashes ([#14](https://github.com/random-walks/jellycell/issues/14))

**Symptom**: `ArrowTypeError: Expected bytes, got a 'float' object` when passing a DataFrame with a column like `["<.001", 0.034, 0.21]`.

**Workaround**: cast the p-value column to `str` before passing:

```python
df["p"] = df["p"].astype(str)  # avoid pyarrow mixed-type inference
jc.table(df, name="regression_results", caption="OLS with HC1 SE")
```

## 5. `jellycell.tearsheets` Python API ([#24](https://github.com/random-walks/jellycell/issues/24) — ADDED in 1.4.0)

1.4.0 adds three helpers — `jt.findings()`, `jt.methodology()`, `jt.audit()` — callable from inside a `jc.step`-tagged cell so the rendered manuscript lives in the cache graph.

```python
import jellycell.tearsheets as jt

jt.findings(
    results={"twfe": {"att": 0.2, "n_obs": 1234}, "cs": {...}},
    out_path="manuscripts/FINDINGS.md",
    project="case-study-rat-containerization",
    template_overrides={"author": "Blaise", "month_year": "April 2026"},
)
```

Stable `template_overrides` keep regenerations byte-identical. Prefer this over the local `_helpers.reporting.emit_findings_markdown` fallback for new notebooks.

## 6. `deps=a,b,c` rejected by nbformat ([#25](https://github.com/random-walks/jellycell/issues/25) — FIXED in 1.4.0)

Use one `deps=` tag per dependency (nbformat enforces `^[^,]+$` on each tag):

```python
# BAD — nbformat validation error
# %% tags=["jc.step", "deps=a,b,c"]

# GOOD — one deps tag per dep
# %% tags=["jc.step", "deps=a", "deps=b", "deps=c"]
```

1.4.0 ships a `deps-no-comma` lint rule that catches this automatically.

## 7. Nested `jellycell.toml` override not applied (no upstream issue on file)

**Symptom**: setting `project = "foo"` in a nested `jellycell.toml` doesn't override a parent config's `[tool.jellycell] project`.

**Workaround**: pass `--project <name>` on the CLI. Not an issue in this repo — a single root `jellycell.toml` sets `project = "case-study-rat-containerization"`, so plain `uv run jellycell run`/`render`/`lint`/`view` resolves correctly.

## Cache semantics — the rules that do work

- **Cache key** = content hash of (cell body + cell deps declared via `deps=` tag + upstream `jc.save`/`jc.table` artifact hashes). Change any dep → cell re-runs.
- **`jc.step` requires `deps=` to participate in the DAG**. Forgotten `deps=` → cell runs but isn't in the dependency graph; downstream cells won't invalidate.
- **`jc.save(obj, path, caption=…)` hashes the *object*, not the path**. Rewriting the same df with a different filename doesn't thrash the cache.
- **`jc.load("name=foo")` resolves the artifact by the declared name**, not by filename. Keep names stable across refactors.

## Tagging reference

```python
# %% tags=["jc.setup"]                        # DO NOT USE — see #1
# %% tags=["jc.load", "name=panel"]           # load/create data; no deps
# %% tags=["jc.step", "name=model", "deps=panel"]  # transform; declare deps
# %% tags=["jc.table", "name=results"]        # emits a rendered table
# %% tags=["jc.figure", "name=fig_event"]     # emits a rendered figure
```

## When to invoke this skill

- Starting a new notebook from scratch — before you type `# %% tags=`.
- Debugging a notebook that worked once and now fails.
- Porting a Jupyter `.ipynb` to jupytext percent format.

## Canonical notebook skeleton

```python
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

# %% [markdown]
# # N — Descriptive title

# %% tags=["jc.load", "name=panel"]
import jellycell.api as jc
from factor_factory.tidy import Panel

panel = Panel.from_parquet("data/cache/panel.parquet")
jc.save(panel, "artifacts/panel.parquet", caption="Analysis panel")

# %% tags=["jc.step", "name=twfe_result", "deps=panel"]
import pandas as pd
import jellycell.api as jc
from factor_factory.engines.did import estimate as did_estimate

result = did_estimate(panel, methods=("twfe", "cs", "sa", "bjs"))
jc.save(result, "artifacts/twfe_result.json", caption="Four-estimator DiD")

# %% tags=["jc.table", "name=main_results"]
import pandas as pd
import jellycell.api as jc

summary = pd.DataFrame([
    (r.method, r.att, r.se, r.ci_95[0], r.ci_95[1], str(r.p_value))
    for r in result
], columns=["method", "ATT", "SE", "CI_low", "CI_high", "p"])
summary["p"] = summary["p"].astype(str)  # #14 workaround
jc.table(summary, name="main_results", caption="Four DiD estimators agree on sign; magnitudes within 5%")
```
