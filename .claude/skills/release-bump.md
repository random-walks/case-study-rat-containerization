---
name: release-bump
description: Version-bump + regenerate-artifacts workflow when an upstream dep (factor-factory, nyc311, jellycell) ships a minor/major. Apply when bumping a range pin in pyproject.toml that could shift numbers in committed tearsheets.
---

# Release bump workflow

Every upstream bump is a tiny, mechanical PR against this repo. The goal:
bump pin → resync → rerun the study → commit refreshed artifacts →
document any numeric drift in the bump commit message (see "Commit
shape" below).

## Bump types

### Patch bump (e.g., jellycell 1.4.0 → 1.4.1)

Bug fixes only; no API change. Expected outcome: identical artifacts.

```bash
# In pyproject.toml: bump the pin
# "jellycell[server]>=1.4.0,<2" → "jellycell[server]>=1.4.1,<2"
uv sync
for nb in notebooks/[0-9]*.py; do
  uv run jellycell run "$nb"
  uv run jellycell export tearsheet "$nb"   # rewrites manuscripts/tearsheets/<stem>.md
done

git diff manuscripts/ artifacts/
# expected: empty diff if bump was truly patch-level
```

`jellycell render` only writes the gitignored HTML catalogue under
`site/` — it never rewrites the committed tearsheets. Skipping the
`export tearsheet` step is how tearsheets silently go stale while the
diff looks clean.

If the diff is non-empty and non-trivial (beyond timestamps), the bump is
really a minor — follow the minor path below.

### Minor bump (e.g., factor-factory 1.0.2 → 1.1.0)

New features, possibly engine math changes. Expected outcome: numbers may
shift in the last 1-2 decimal places.

```bash
# Bump pin, sync
uv sync

# Rerun the whole study, in notebook order
for nb in notebooks/[0-9]*.py; do
  uv run jellycell run "$nb"
  uv run jellycell export tearsheet "$nb"
done
uv run jellycell lint

# Review diffs
git diff manuscripts/FINDINGS.md
# Expected: small numeric shifts

# Note the drift for the bump commit message
```

Record the known differences in the bump commit's body (illustrative example — see "Commit shape" below for where this goes):

```markdown
Dependencies:
- factor-factory bumped 1.0.2 → 1.1.0

Known differences from the previous run:
- ATT point estimate shifted -0.012 → -0.013 due to factor-factory's improved CS bootstrap variance estimator (closes [factor-factory#47](https://github.com/random-walks/factor-factory/pull/47)). Sign and significance unchanged.
- All other committed tearsheets byte-identical.
```

### Major bump (e.g., factor-factory 1.x → 2.0)

Breaking changes. Follow the upstream CHANGELOG migration notes.

1. Read upstream `docs/MIGRATION.md` first.
2. Branch off: `git checkout -b bump-factor-factory-2`.
3. Update imports + API calls per migration guide.
4. Rerun the study (`for nb in notebooks/[0-9]*.py; do uv run jellycell run "$nb"; uv run jellycell export tearsheet "$nb"; done`); numbers may shift materially.
5. Update `AUDIT.md` with the new method refs.
6. Write a full migration section in the bump commit message body.

## The byte-identical-diff invariant

After any bump + re-render, the diff to `manuscripts/` should be either:

1. **Empty** (patch bump, no code change) — ideal
2. **Numeric-only** (minor bump) — acceptable, document
3. **Structural** (major bump, API change) — requires a full migration write-up in the commit message + hand review

Never commit an artifact diff without explaining it.

## Commit shape

One commit per bump:

```
bump: factor-factory 1.0.2 → 1.1.0

Reran and rerendered the study. Numeric shift in the ATT
(-0.012 → -0.013); sign and significance unchanged across all specs.
```

Not one commit per regenerated file. If the bump touches 40 files,
`git add -A` is fine IF you've reviewed the diff.

## After the bump lands — refresh the live post

If the bump changed anything under `manuscripts/` or `artifacts/`, the
published post at blaiseoss.com is now STALE — it never updates on its
own. From the workspace root:

```bash
./scripts/sync-case-study.sh rat    # regenerate + commit the site post
./scripts/sync-case-study.sh --check    # verify nothing else drifted
```

Then push this repo and blaise-website (Vercel deploys on push).

## When to invoke this skill

- User says "bump factor-factory" / "jellycell just released X" / "nyc311 shipped 1.1".
- Security advisory on a pinned dep.
- Quarterly dep-refresh cycle.

## When NOT to invoke this skill

- Adding a new dep (that's `feat:`, not `bump:`).
- Internal refactor that touches pyproject.toml for non-version reasons.
