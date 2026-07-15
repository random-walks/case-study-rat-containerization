---
name: paper-cadence
description: Academic paper cadence for manuscripts — APA in-text citations, italicized test statistics, structured sections, precise p-value reporting. Apply when authoring MANUSCRIPT.md, CASESTUDY.md, or any Findings document that's meant to read like real research.
---

# Academic paper cadence

This skill codifies the voice used in the canonical
[`subway-access` CASESTUDY](https://github.com/random-walks/subway-access/blob/main/examples/accessibility-change-over-time/CASESTUDY.md)
which is the reference implementation for this case study's manuscript.
This repo's `manuscripts/MANUSCRIPT.md` follows the same cadence.

## Non-negotiables

### Structure (numbered sections)

```
# Title: Subtitle Posed as a Question or Statement of Scope
**By [Author](url)** | role, affiliation
*Month Year*
---
## Abstract (one dense paragraph, ≤350 words, quantitative)
*Keywords:* 5–8, comma-separated, lowercase
## 1. Introduction
## 2. Background
  ### 2.1 Study Area
  ### 2.2 Policy / Institutional Context
  ### 2.3 Related Literature
## 3. Data and Methods
  ### 3.1 Data Sources (Table 1)
  ### 3.2–3.n Model specifications, identifying assumptions
## 4. Results
  ### 4.1, 4.2, … — each with one headline figure + Table
## 5. Discussion / Limitations / Policy
## 6. Conclusion
## References (APA 7, alphabetical)
## Appendices (A, B, … — labeled, not lettered inline)
```

### Citations — APA 7, in-text

- Parenthetical: `(Author, Year)`, `(Author & Author, Year)`, `(Author et al., Year)` (3+ authors).
- Narrative: `Author (Year) found that…` / `Author et al. (Year) demonstrated…`
- Direct: `Author (Year, p. 12)` with page number only for direct quotes.
- Multiple in one paren: alphabetize by first author, semicolon-separated: `(Author, 2020; Other, 2024)`.
- Government / organizational: `(Metropolitan Transportation Authority [MTA], 2026)` first mention; `(MTA, 2026)` after.
- Reference list sorted alphabetically by first author last name, hanging indent.

### Test statistics — italicize the symbol, not the number

- `*p* = .034` (note: leading zero dropped; *p* italic; number upright)
- `*p* < .001` for significance below threshold (NEVER write `*p* = .000`)
- `*R*² = .202`, `*F*(3, 2313) = 108.83, *p* < .001`
- `*t*(2315) = -3.34, *p* < .001`
- `*z* = 40.87, *p* < .001`
- `Moran's *I* = .23`
- `χ²(1, *N* = 157) = 4.82, *p* = .028`
- `Cohen's *d* = 0.29`
- Confidence interval: `95% CI [.021, .087]`
- Effect size always reported alongside *p* (APA Publication Manual 7th ed. §6.40).

### Tables

```markdown
**Table N. Descriptive Caption, Not Just "Main Results"**

| Column | *N* | *M* (SD) | Δ | *t* | *p* | *d* |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| Treatment | 831 | 0.049 (0.021) | +0.010 | 6.40 | < .001 | 0.29 |
| Control | 1,486 | 0.039 (0.019) | — | — | — | — |

*Note.* Welch's *t*-test; treatment tracts had significantly higher disability rates than control tracts. Effect size small per Cohen (1988) convention.
```

### Numbers

- Commas as thousands separators: `4,717,140`, not `4717140` or `4.7M`.
- One decimal place for percentages in running text: `55.4%`.
- Two or three significant figures for statistical coefficients: `β = 0.263`, `*t* = 15.93`.
- Years always four digits: `2026`, not `'26`.
- Spell numbers under 10 unless a statistic: "three boroughs" but "*n* = 3 boroughs".
- Never start a sentence with a numeral — rewrite: "A total of 493 stations…" not "493 stations…"

### Voice

- Past tense for methods and results: "We estimated…", "OLS yielded…".
- Present tense for implications and figures: "Figure 3 shows…", "These results suggest…".
- First-person plural ("we") is acceptable in PNAS/AER/QJE/JAH style. Stick with it unless journal demands otherwise.
- Avoid intensifiers: "very significant", "highly robust" → drop the adverb.
- Never "prove" — "show", "indicate", "suggest", "demonstrate", "are consistent with".
- No contractions: "do not", not "don't".

### Honest limitations

Ship a `## 5.3 Limitations` subsection listing ≥5 specific, honest constraints. Good limitations are falsifiable ("Euclidean distance overstates coverage because it ignores street topology"), not polite hand-waves ("further research needed").

## When to invoke this skill

- Authoring `MANUSCRIPT.md`, `CASESTUDY.md`, `FINDINGS.md` (if not auto-generated)
- Reviewing a human-authored manuscript for publication-readiness
- Converting auto-generated tearsheet prose to paper-quality prose

## When NOT to invoke this skill

- Code comments — use plain prose, no citations needed.
- `README.md` — keep it breezy and action-oriented.
- Auto-generated tearsheets — `jellycell.tearsheets` produces its own voice; the template lives upstream.
- Internal `AUDIT.md` — pragmatic bullet-list voice is fine, not paper voice.

## Reference manuscripts (read before authoring)

- `manuscripts/MANUSCRIPT.md` (this repo)
  The canonical in-repo example. Read the abstract, §3, §4, and References before writing your own.
- [`subway-access` CASESTUDY.md upstream](https://github.com/random-walks/subway-access/blob/main/examples/accessibility-change-over-time/CASESTUDY.md)
  The v0.5 version with engine-audit appendix.
