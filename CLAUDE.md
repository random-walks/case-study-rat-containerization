# CLAUDE.md — case-study-rat-containerization

One node of the blaise-oss ecosystem, developed from the
`blaise-dev-workspace` meta-repo (checked out at
`repos/published-case-studies/case-study-rat-containerization/`).
Rules here win over workspace-level rules.

## What this repo is

The standalone home of the NYC rat-containerization case study —
extracted from `blaise-website` `packages/python-showcase/` with full
history (2026-07). A jellycell/uv project: plain-text notebooks under
`notebooks/`, hand-authored paper at `manuscripts/MANUSCRIPT.md`,
committed results under `artifacts/`.

- Stack: Python 3.12, uv (never pip), jellycell, factor-factory, nyc311.
- Run: `uv sync && uv run jellycell run` (first run refetches ~60 MB of
  Socrata CSVs into `data/cache/`, ~10–15 min; needs network).
- Render/lint/view: `uv run jellycell render|lint|view`.

## Publishing contract

`manuscripts/MANUSCRIPT.md` is the source of truth for the published
post at https://blaiseoss.com/posts/rat-containerization. The site MDX
is GENERATED — never edit it there. To publish a revision:

1. Land the change here (manuscript, notebooks, regenerated artifacts).
2. From the workspace root: `./scripts/sync-case-study.sh rat`
   (two cross-referenced commits: this repo first, then blaise-website).

Write citations as plain APA text — the sync script is the only linker
(anchors `#ref-lastname<year>`, no hyphen) and validates every anchor.
Don't hard-wrap hyphenated words across lines (renders with a stray
space). `FINDINGS.md`, `DIAGNOSTICS_CHECKLIST.md`, tearsheets, and
`artifacts/` are regenerated — never hand-edit them.
