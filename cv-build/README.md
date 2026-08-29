# CV build toolkit

Rebuilds `Mohamed-Hasabalah-CV.pdf` from source and verifies it parses like an ATS expects.

## Usage

```bash
cd "cv-build"
python build.py
```

That inlines the fonts, renders the PDF to the vault root, and runs 9 checks.
Use `python build.py --no-verify` to skip the checks.

**Edit `cv.html` only.** `cv-print.html` is generated on every run and can be deleted.

## Files

| File | What it is |
|---|---|
| `cv.html` | **The master.** Edit this. Content + all styling. |
| `fonts/*.woff2` | Source Serif 4 (600), Source Sans 3 (400/600/700) |
| `build.py` | Inline fonts → render PDF → verify |
| `cv-print.html` | Generated. Fonts baked in, works offline. |

Output: `../Mohamed-Hasabalah-CV.pdf`

Keep `../CV-Mohamed-Hasabalah-Senior-Software-Engineer.md` in sync by hand —
that's the plain-text version for ATS portals, and it deliberately keeps the
**full LinkedIn/GitHub URLs** where the PDF shows short handles.

## The 9 checks

| Check | Why it exists |
|---|---|
| Exactly 2 pages | The target length |
| Text layer extractable | Proves it isn't rendering as an image |
| No corrupt characters | Caught a real bug: em dashes extracted as `<?>` |
| Text layer pure ASCII | Root cause of the above — keep punctuation plain |
| Section order sequential | Caught a real bug: bullets emitted after "Languages" |
| Employers in order | Caught a real bug: bullets detached from their jobs |
| Contact fields extract | Recruiter must be able to copy email/phone |
| No bullet over 25 words | Scannability |
| Quantification ≥ 50% | Bullets containing a number |

## Rules learned the hard way

**Never use non-ASCII punctuation.** Em dashes (—), en dashes (–) and middle
dots (·) extracted as `<?>` in the PDF text layer. Use `-` and `/`.

**Never use `position: relative` on list items.** Positioned elements paint in a
later phase, so every bullet was emitted *after* every job header — an ATS would
have built a nonsense work history. The bullet marker uses
`display:inline-block` + negative `text-indent` instead. Don't "fix" that back.

**Icons must be inline SVG, never emoji or icon fonts.** SVG renders as vector
paths and contributes nothing to the text layer. Emoji would reintroduce the
non-ASCII corruption above.

**Watch CSS specificity on spacing.** `.summary { margin: 0 }` silently beat
`section > * + *`, collapsing every gap. Spacing rules must match or exceed the
specificity of the resets they fight.

**Fonts are inlined for a reason.** With a network `<link>`, Chrome's PDF export
raced the webfont load and embedded only one of the four faces — the rest
silently fell back to Georgia and Segoe UI. Base64 removes the race.

**Check the render, not just the diff.** The clipped "Cairo", the stray
separator bar, and a skills entry that was never true were all found by looking
at images, not at code.

## If a change pushes it to 3 pages

In the `@media print` block, in this order:
1. `ul.points > li + li` margin (currently 2.3pt)
2. `.roles/.projects .role-block + .role-block` margin (6.8pt)
3. `ul.points li` line-height (1.34)
4. `@page` margin (9mm 12.5mm)

Shorten bullets before shrinking type. Below ~8.5pt it stops looking senior.

## Still unverified

Four numbers in the CV are estimates, not facts. Confirm or replace before sending:

- `15+ report requests a month` (MicrotecSaudi)
- `10 document types` (MSDC / QuestPDF)
- `roughly 6 hours per week` saved (MSDC / QuestPDF)
- `monthly and manual to several per week` (EL-SAFA)

`45 minutes to under 10` (MSDC / Oracle) is confirmed defensible — know the
report name and the index you added.
