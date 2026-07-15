---
name: release-bump
description: Version-bump + regenerate-artifacts workflow when an upstream dep (factor-factory, nyc311, subway-access, jellycell) ships a minor/major. Apply when bumping a range pin in pyproject.toml that could shift numbers in committed tearsheets.
---

# Release bump workflow

Every upstream bump is a tiny, mechanical PR against this repo. The goal:
bump pin → resync → rerun the study → commit refreshed artifacts →
document any numeric drift in CHANGELOG.

## Bump types

### Patch bump (e.g., jellycell 1.3.5 → 1.3.6)

Bug fixes only; no API change. Expected outcome: identical artifacts.

```bash
# In pyproject.toml: bump the pin
# "jellycell[server]>=1.3.5,<2" → "jellycell[server]>=1.3.6,<2"
uv sync
uv run jellycell render

git diff manuscripts/ artifacts/
# expected: empty diff if bump was truly patch-level
```

If the diff is non-empty and non-trivial (beyond timestamps), the bump is
really a minor — follow the minor path below.

### Minor bump (e.g., factor-factory 1.0.2 → 1.1.0)

New features, possibly engine math changes. Expected outcome: numbers may
shift in the last 1-2 decimal places.

```bash
# Bump pin, sync
uv sync

# Rerun the whole study
uv run jellycell run
uv run jellycell render
uv run jellycell lint

# Review diffs
git diff manuscripts/FINDINGS.md
# Expected: small numeric shifts

# Document in CHANGELOG
```

Add a CHANGELOG entry for this repo under `### Known differences from <prev-version>` (illustrative example):

```markdown
## [2.0.1] — 2026-05-DD

### Dependencies
- factor-factory bumped 1.0.2 → 1.1.0

### Known differences from 2.0.0
- ATT point estimate shifted -0.012 → -0.013 due to factor-factory's improved CS bootstrap variance estimator (closes [factor-factory#47](https://github.com/random-walks/factor-factory/pull/47)). Sign and significance unchanged.
- All other committed tearsheets byte-identical.
```

### Major bump (e.g., factor-factory 1.x → 2.0)

Breaking changes. Follow the upstream CHANGELOG migration notes.

1. Read upstream `docs/MIGRATION.md` first.
2. Branch off: `git checkout -b bump-factor-factory-2`.
3. Update imports + API calls per migration guide.
4. Rerun the study (`uv run jellycell run` + `uv run jellycell render`); numbers may shift materially.
5. Update `AUDIT.md` with the new method refs.
6. Update this repo's `CHANGELOG.md` with a full migration section.

## The byte-identical-diff invariant

After any bump + re-render, the diff to `manuscripts/` should be either:

1. **Empty** (patch bump, no code change) — ideal
2. **Numeric-only** (minor bump) — acceptable, document
3. **Structural** (major bump, API change) — requires CHANGELOG migration section + hand review

Never commit an artifact diff without explaining it.

## Commit shape

One commit per bump:

```
bump: factor-factory 1.0.2 → 1.1.0

Reran and rerendered the study. Numeric shift in the ATT
(-0.012 → -0.013) documented in CHANGELOG under "Known differences".
Sign and significance unchanged across all specs.
```

Not one commit per regenerated file. If the bump touches 40 files,
`git add -A` is fine IF you've reviewed the diff.

## When to invoke this skill

- User says "bump factor-factory" / "jellycell just released X" / "nyc311 shipped 1.1".
- Security advisory on a pinned dep.
- Quarterly dep-refresh cycle.

## When NOT to invoke this skill

- Adding a new dep (that's `feat:`, not `bump:`).
- Internal refactor that touches pyproject.toml for non-version reasons.
