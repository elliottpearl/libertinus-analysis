# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A diagnostic sandbox for combining-mark (GPOS mark-to-base) behavior in Libertinus Serif, aimed at IPA and linguistics notation. It measures the four original fonts, reports on them in a XeLaTeX PDF, and builds patched fonts (`fonts/*-patch.otf`) with corrected and added anchors. It is exploratory and unfinished; expect legacy modules and half-built stages.

## Commands

There is no test suite and no linter. Work is driven by top-level `run_*` wrapper scripts, which are edited in place to choose inputs and then executed. **Always run them from the repo root**: several modules use paths relative to the working directory (`data/fea/...`, `data/fontmetrics/...`, `data/fontanchors_implied/...`), and `data/` is imported as a top-level package from the root.

```bash
# normal environment (everything except FontForge scripts)
.venv/bin/python run_build_fontmetrics.py             # fonts -> data/fontmetrics/{style}.json
.venv/bin/python run_print_report_fontmetrics_full.py # JSON -> tex/input/fontmetrics_*.tex
.venv/bin/python run_anchor_copy_report.py            # clusters of identical anchors -> tex/input/copied_anchors.tex
.venv/bin/python run_anchor_audit.py                  # bad/suspect designer anchors -> data/fontanchors_audit/{style}.py, tex/input/anchor_audit.tex
.venv/bin/python run_print_combo_matrix.py            # base x mark grids, original vs patched fonts
.venv/bin/python run_patch_font.py                    # fonts/*.otf -> fonts/*-patch.otf
./run_xelatex_report.sh                               # tex/libertinus-analysis.tex -> PDF

# FontForge environment (Python 3.11; system fontforge module symlinked in)
.venv-fontforge/bin/python run_print_implied_anchors.py
.venv-fontforge/bin/python run_print_implied_cap_marks.py
```

Two virtual environments exist because the system FontForge module is built for Python 3.11; see `README-VENV.md` for setup. Only scripts that `import fontforge` (the `implied_*` modules and their two wrappers) need `.venv-fontforge`.

`test_build_fontmetrics.sh` is not a test; it counts how often each semantic tag is true/false in the JSON.

## Architecture

Python modules live in `src/libertinus_analysis/` (package `libertinus_analysis`); module names below are relative to it.

### Style keys and the font registry

Everything is keyed by style: `regular`, `italic`, `semibold`, `semibold_italic` (plus `*_patch` variants). `FONTS` in `font_context.py` maps each key to a font path and the **GPOS lookup index of its mark-to-base lookup, which differs per font** (4, 4, 1, 2). Anchor classes within that lookup are referred to by index: `0` = above, `2` = below (`1` above-right, `3` above-right/left-angle). In the fontmetrics JSON these indices are string keys (`"0"`, `"2"`). **Original semibold differs:** its class `1` is the designer's `top_punkt`, a second above class (dot above U+0307, diaeresis, ring, hook above, comma above; base anchors 96 lower on lowercase, 83 on capitals, on only 24 bases), and its `3` and `4` are ogonek/hooks and cedilla. Stage 1 of the patch merges `top_punkt` into class 0; the fontmetrics JSON, read from the original fonts, still has it.

### Data flow

1. **Extract** — `fontmetrics_extractor.py` reads the original fonts and writes `data/fontmetrics/{style}.json`: per-glyph bbox, anchors, width, sidebearings, tags (schema in `data/fontmetrics/SCHEMA.md`). The report layer reads only this JSON (via `fontmetrics_loader.py`), never the font files, so anything that needs outlines must be computed in the extractor and stored.
2. **Derive** — `fontmetrics_helpers.py` holds the per-style reference tables (`VERTICAL_THRESHOLDS_OPT`, `ANCHOR_Y_REF_OPT`, `CLEARANCES_OPT`, `OPTICAL_CORRECTION`) and the candidate functions (`get_aya`, `get_bya`, and `get_anchor_candidate` for (X, Y)); see "Anchor model and candidates" below.
3. **Report** — `fontmetrics_report.py` builds LaTeX table bodies (one column per glyph, a block of rows per style) written to `tex/input/`, which `tex/libertinus-analysis.tex` `\input`s. `combo_matrix.py` + `classifiers.py` produce the base x mark grids. Generated `.tex` fragments and the PDF are committed.
4. **Patch** — `font_patching.py` orchestrates stages on the GPOS lookup and GSUB (see below).

Character sets (which bases, which marks) come from `data/ipa/ipa_unicode.py` as `unicode_groups[NAME]["items"]`, e.g. `BASE_LATIN`, `BASE_IPA`, `MARK_ABOVE`, `MARK_BELOW`.

### Anchor model and candidates

**Read `ANCHOR-HEURISTICS.md` before calculating, auditing or patching any anchor.** It summarizes the model with every number and formula needed to compute a candidate: aspect bands, anchor Y references, clearances, overshoots, the per-style X formulas and K shifts, mark anchors, and which parts the code implements. The authority behind it is the report, `tex/libertinus-analysis.tex` ("Anchor model" through "Semibold italic anchor model", plus "Vertical aspects…"). When the understanding changes, update the report first, then `ANCHOR-HEURISTICS.md`. Keep the model in that file, not here.

In short: the base anchor is where the mark goes, so the clearance lives in the base anchor. Y is the glyph's vertical aspect plus that aspect's clearance, the same in every style. X is the bbox midpoint in roman. In italic it is the midline of the slanted advance-width lane at the anchor's own height. Semibold italic keeps the designer's model: the italic position minus a shift K (150 above, −12 below).

Standing rules:
- Candidates are geometric centres computable from metrics. They are not optical centres; a human curates where they fail.
- Designer anchors are inconsistent (wrong, copied between glyphs or styles, not snapped to references). Trust them only in aggregate, never as evidence of intent for a single glyph. The patch is meant to normalize them.
- **Never move semibold italic to the italic model** (decided 2026-10-12). Patch only anchors that do not conform to its own model.

### Patch pipeline (`font_patching.patch_font`)

Stages in order; 5 is planned and commented out. Glyphs come first; scripted anchor stages (4–6) come before the human-curated anchors, which overrule them; derived letters (8) inherit after the curated anchors but never over one; precomposed inheritance is the last anchor stage; GSUB is rebuilt and the coverage sorted at the end.

1. Clean up the lookup. First, `font_patching_mergeclasses.py` merges semibold's `top_punkt` (class 1) into class 0: its marks move to class 0 with anchor y + 96, its base anchors are dropped (G, which has no class-0 anchor, gets one from it), and U+0315 stays in class 1 as the above-right class of the other styles. Placement on lowercase is unchanged; the dot-like marks now attach wherever a class-0 anchor exists. It runs first so that stage 3 and later see one above class. Then delete bad anchors (`font_patching_deleteanchors.py`) so that stages 6–8 refill them. Anchors marked `"delete"` in `data/fontanchors_audit/overrides.py` are always deleted, for any reason, including not fitting the style's anchor model (semibold italic a, s, h, J above, which carried the slant). The audit's own "bad" verdicts are deleted only if `DELETE_BAD_ANCHORS` in `font_patching.py` is on; it is off because that list is unreviewed: about 490 deletions, about 150 of them outside stage 6's Latin/IPA scope and so left with no anchor, and in semibold italic it flags the copies of regular's anchors that the semibold italic model keeps. Prefer deletion + stage 6 over a curated anchor wherever the candidate is right; stage 7 is for anchors the candidate cannot get right. `anchor_audit.py` (run via `run_anchor_audit.py`) reads the font files directly, tests every above/below base anchor in the style's mark-to-base lookup whose glyph has a Unicode codepoint (unencoded small caps and alternates are ignored), and writes the bad and suspect ones with reasons to `data/fontanchors_audit/{style}.py`, plus a test sheet to `tex/input/anchor_audit.tex` (the "Anchor audit" section of the report). Those files are regenerated on each run; human decisions go in `data/fontanchors_audit/overrides.py` (`"keep"` / `"delete"`). With the audit on, only "bad" anchors are deleted. Thresholds are constants at the top of `anchor_audit.py`.
2. Add glyphs — U+E100 `space_en_base`, an invisible spacing base (CFF charstring built by hand). For a floating mark (e.g. a floating tone), the Unicode way is NBSP + mark, so U+00A0 also gets x-height above/below anchors in stage 7.
3. Add missing marks — `font_patching_addmarks.py` adds the combining marks a style lacks, with mark anchors, by copying outlines the designer drew elsewhere: semibold takes regular's outline (above marks moved right 12), semibold italic takes italic's outline moved right 12 with regular's anchor verbatim (the semibold italic anchor model), and `dotaccent.cap` in the two italic styles is the dot of the precomposed Idotaccent. It opens the other original fonts to read those outlines. Copied above marks are made bolder to match the designer's own (about 12%): a part that is another mark is swapped for the style's own mark, and the rest is pushed outward by `embolden()`; below marks, lines and combining letters are copied unchanged. The "Adding missing marks" section of the report shows the emboldened ones. In semibold it also replaces U+0358–U+0363, which the original font fills with copies of the capital accents.
4. Capital-mark anchors — `font_patching_capmarks.py` sets the mark anchor of each `.cap` accent from the precomposed capitals A–Z: y is the capital anchor reference (850; semibold 805) minus how far the mark is raised there (median); x is the outline's centre on its own axis for symmetric marks, and the median precomposed position relative to the base's midline for grave, acute, double acute, double grave; semibold italic subtracts K = 150. Curated `.cap` anchors in `fontanchors_human` that the script reproduces (regular, 8 of 10) are commented out; italic's are all kept and differ from the script by 6–62 units in x because they fit the designer's off-midline capital anchors.
5. Normalize designer anchor y *(planned)*
6. Heuristic anchors — `font_patching_heuristicanchors.py` gives each base in `BASE_LATIN` ∪ `BASE_IPA` that lacks an above or below anchor its candidate from `get_anchor_candidate` (rounded), read from the original font's fontmetrics JSON. It only fills gaps, never moves an existing anchor, and skips canonically decomposed glyphs (stage 8 handles them). Candidates fail where §4 of `ANCHOR-HEURISTICS.md` says (e.g. j gets Y 834 from its dot); curated anchors in stage 7 overrule them.
7. Human-curated anchors from `data/fontanchors_human/{style}.py` (`bases`, `marks`, `bases_by_name`, `marks_by_name`; overwrite or create, never delete). A curated anchor that a scripted stage (or the designer's own anchor) reproduces within about 10 units is redundant and is commented out with a note naming what reproduces it (audit of 2026-10-29); keep curated anchors for what the stages cannot get right. `regular` is far more complete than the other styles.
8. Derived letters — `font_patching_derivedanchors.py` gives each letter listed in `data/derived_letters.py` (a base letter plus a bar, stroke, hook, tail, curl or belt; classes per entry, optionally per style) its base letter's final anchor plus the horizontal shift between the outlines, found by matching outline crossings on a 10-unit height grid. It inherits only where at least 70% (`MIN_MATCH`) of the base's outline is found in the derived letter (most italic and semibold italic derived letters were redrawn and are skipped), and never over a curated anchor. It runs after stage 7 so that it inherits the base's final anchor. `run_derived_anchor_report.py` writes the comparison sheet `tex/input/derived_anchors.tex` (designer, candidate, inherited, curated, per style; "Derived letters" section of the report).
9. Precomposed inheritance — a precomposed glyph lacking an anchor inherits it from its deepest Unicode-decomposition base; glyphs that already have one are reported and left alone
10. GSUB `ccmp` rebuilt from `data/fea/{style}/ccmp.fea` (dot removal, `.cap` accent forms). feaLib's builder destroys GPOS and GDEF, so both are saved and restored around the build.
11. Sort coverage — `font_patching_sortcoverage.py` sorts the mark-to-base lookup's BaseCoverage and MarkCoverage by glyph ID, with their records, because the anchor stages append glyphs at the end (otherwise fontTools warns "Coverage is not sorted by glyph ids" on every compile).

### Planned: mark anchors

The audit and stage 1 cover base anchors only. Elliott intends to audit and patch **mark** anchors too (noted 2026-10-11; not started; listed in the report's to-do). The mark-anchor model (`X = C + Y tan θ − K`) is in `ANCHOR-HEURISTICS.md` §3.

- Findings so far are summarized in the report's "Mark anchor model" section (after Figure 4), including what the patch already changes and a list of changes needed. They come from one-off checks that are not in the repo: X offset from the mark's axis and anchor-to-outline distance, each compared with regular, plus the precomposed glyphs on o, n, u.
- Capital-form marks (`grave.cap`, `acute.cap`, `circumflex.cap`, `breve.cap`, substituted over capitals by `ccmp`) are unencoded, so a mark audit keyed on codepoints misses them. In semibold italic their anchors carry the slant while capital base anchors do not, so they land 160–190 units left; in italic most `.cap` marks have no mark anchor at all (fallback positioning, 120–190 units right); in semibold 15 of A–Z (ABCDEFGHIKLMNPU) have no above anchor.
- The combining dot above (U+0307) sits lower through its anchor than in precomposed glyphs (45 units lower in regular, 11 in italic); its mark anchor is a candidate for patching.
- Curated mark anchors go in the `marks` / `marks_by_name` dicts of `data/fontanchors_human/{style}.py`.

### Legacy code

Files with `legacy` in the name (`font_patching_legacy.py`, `font_patching_helpers_legacy.py`, `legacy-geometry.py`, `data/legacy-fontdata/`) are superseded and not on the active paths. `data/vertical_data.py` predates the `*_OPT` tables in `fontmetrics_helpers.py` and disagrees with them in places; the `*_OPT` tables are the ones the code uses.

## LaTeX conventions

From `README-FONTS.md`: fonts are loaded with `fontspec` from `fonts/`; always use `Path = ../fonts/` and always include the file extension (`.otf`, `.ttf`). Semibold is the bold face. The patched family is `\LibertinusSerifPatch`. Table cells render sample glyphs as `\char"XXXX`, with `\cgj` between base and mark in the fontmetrics tables.
