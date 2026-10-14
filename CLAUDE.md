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

Everything is keyed by style: `regular`, `italic`, `semibold`, `semibold_italic` (plus `*_patch` variants). `FONTS` in `font_context.py` maps each key to a font path and the **GPOS lookup index of its mark-to-base lookup, which differs per font** (4, 4, 1, 2). Anchor classes within that lookup are referred to by index: `0` = above, `2` = below (`1` above-right, `3` above-right/left-angle). In the fontmetrics JSON these indices are string keys (`"0"`, `"2"`).

### Data flow

1. **Extract** — `fontmetrics_extractor.py` reads the original fonts and writes `data/fontmetrics/{style}.json`: per-glyph bbox, anchors, width, sidebearings, tags (schema in `data/fontmetrics/SCHEMA.md`). The report layer reads only this JSON (via `fontmetrics_loader.py`), never the font files, so anything that needs outlines must be computed in the extractor and stored.
2. **Derive** — `fontmetrics_helpers.py` holds the per-style reference tables (`VERTICAL_THRESHOLDS_OPT`, `ANCHOR_Y_REF_OPT`, `CLEARANCES_OPT`, `OPTICAL_CORRECTION`) and the candidate functions (`get_aya`, `get_bya`, the `xm`/`axm`/`bxm` midpoints); see "Anchor model and candidates" below.
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
- The fontmetrics tables' italic `axm`/`bxm` do not follow the lane model yet (see `ANCHOR-HEURISTICS.md` §5). Don't cite them as model candidates until that report to-do is done.

### Patch pipeline (`font_patching.patch_font`)

Stages in order; 5 and 6 are planned and commented out. Glyphs come first; scripted anchor stages (4–6) come before the human-curated anchors, which overrule them; precomposed inheritance is the last anchor stage; GSUB is rebuilt at the end.

1. Delete bad anchors — implemented in `font_patching_deleteanchors.py` but switched off by `DELETE_BAD_ANCHORS` in `font_patching.py`, because nothing refills the deleted anchors until stages 5–6 exist. `anchor_audit.py` (run via `run_anchor_audit.py`) reads the font files directly, tests every above/below base anchor in the style's mark-to-base lookup whose glyph has a Unicode codepoint (unencoded small caps and alternates are ignored), and writes the bad and suspect ones with reasons to `data/fontanchors_audit/{style}.py`, plus a test sheet to `tex/input/anchor_audit.tex` (the "Anchor audit" section of the report). Those files are regenerated on each run; human decisions go in `data/fontanchors_audit/overrides.py` (`"keep"` / `"delete"`). Only "bad" anchors are deleted. Thresholds are constants at the top of `anchor_audit.py`.
2. Add glyphs — U+E100 `space_en_base`, an invisible spacing base (CFF charstring built by hand). For a floating mark (e.g. a floating tone), the Unicode way is NBSP + mark, so U+00A0 also gets x-height above/below anchors in stage 7.
3. Add missing marks — `font_patching_addmarks.py` adds the combining marks a style lacks, with mark anchors, by copying outlines the designer drew elsewhere: semibold takes regular's outline (above marks moved right 12), semibold italic takes italic's outline moved right 12 with regular's anchor verbatim (the semibold italic anchor model), and `dotaccent.cap` in the two italic styles is the dot of the precomposed Idotaccent. It opens the other original fonts to read those outlines. Copied above marks are made bolder to match the designer's own (about 12%): a part that is another mark is swapped for the style's own mark, and the rest is pushed outward by `embolden()`; below marks, lines and combining letters are copied unchanged. The "Adding missing marks" section of the report shows the emboldened ones. In semibold it also replaces U+0358–U+0363, which the original font fills with copies of the capital accents.
4. Capital-mark anchors — `font_patching_capmarks.py` sets the mark anchor of each `.cap` accent from the precomposed capitals A–Z: y is the capital anchor reference (850; semibold 805) minus how far the mark is raised there (median); x is the outline's centre on its own axis for symmetric marks, and the median precomposed position relative to the base's midline for grave, acute, double acute, double grave; semibold italic subtracts K = 150. Curated `.cap` anchors in `fontanchors_human` that the script reproduces (regular, 8 of 10) are commented out; italic's are all kept and differ from the script by 6–62 units in x because they fit the designer's off-midline capital anchors.
5. Normalize designer anchor y *(planned)*
6. Heuristic anchors for glyphs still lacking them *(planned)*
7. Human-curated anchors from `data/fontanchors_human/{style}.py` (`bases`, `marks`, `bases_by_name`, `marks_by_name`; overwrite or create, never delete). `regular` is far more complete than the other styles.
8. Precomposed inheritance — a precomposed glyph lacking an anchor inherits it from its deepest Unicode-decomposition base; glyphs that already have one are reported and left alone
9. GSUB `ccmp` rebuilt from `data/fea/{style}/ccmp.fea` (dot removal, `.cap` accent forms). feaLib's builder destroys GPOS and GDEF, so both are saved and restored around the build.

### Planned: mark anchors

The audit and stage 1 cover base anchors only. Elliott intends to audit and patch **mark** anchors too (noted 2026-10-11; not started; listed in the report's to-do). The mark-anchor model (`X = C + Y tan θ − K`) is in `ANCHOR-HEURISTICS.md` §3.

- Findings so far, from a one-off check that is not in the repo: regular and italic marks fit (italic tilde is 11 off); semibold has anchor heights that differ from regular for about a quarter of its marks.
- Capital-form marks (`grave.cap`, `acute.cap`, `circumflex.cap`, `breve.cap`, substituted over capitals by `ccmp`) are unencoded, so a mark audit keyed on codepoints misses them. In semibold italic their anchors carry the slant while capital base anchors do not, so they land 160–190 units left; in italic most `.cap` marks have no mark anchor at all (fallback positioning, 120–190 units right); in semibold 15 of A–Z (ABCDEFGHIKLMNPU) have no above anchor.
- The combining dot above (U+0307) sits lower through its anchor than in precomposed glyphs (45 units lower in regular, 11 in italic); its mark anchor is a candidate for patching.
- Curated mark anchors go in the `marks` / `marks_by_name` dicts of `data/fontanchors_human/{style}.py`.

### Legacy code

Files with `legacy` in the name (`font_patching_legacy.py`, `font_patching_helpers_legacy.py`, `legacy-geometry.py`, `data/legacy-fontdata/`) are superseded and not on the active paths. `data/vertical_data.py` predates the `*_OPT` tables in `fontmetrics_helpers.py` and disagrees with them in places; the `*_OPT` tables are the ones the code uses.

## LaTeX conventions

From `README-FONTS.md`: fonts are loaded with `fontspec` from `fonts/`; always use `Path = ../fonts/` and always include the file extension (`.otf`, `.ttf`). Semibold is the bold face. The patched family is `\LibertinusSerifPatch`. Table cells render sample glyphs as `\char"XXXX`, with `\cgj` between base and mark in the fontmetrics tables.
