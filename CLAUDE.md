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

### Style keys and the font registry

Everything is keyed by style: `regular`, `italic`, `semibold`, `semibold_italic` (plus `*_patch` variants). `FONTS` in `font_context.py` maps each key to a font path and the **GPOS lookup index of its mark-to-base lookup, which differs per font** (4, 4, 1, 2). Anchor classes within that lookup are referred to by index: `0` = above, `2` = below (`1` above-right, `3` above-right/left-angle). In the fontmetrics JSON these indices are string keys (`"0"`, `"2"`).

### Data flow

1. **Extract** — `fontmetrics_extractor.py` reads the original fonts and writes `data/fontmetrics/{style}.json`: per-glyph bbox, anchors, width, sidebearings, tags (schema in `data/fontmetrics/SCHEMA.md`). The report layer reads only this JSON (via `fontmetrics_loader.py`), never the font files, so anything that needs outlines must be computed in the extractor and stored.
2. **Derive** — `fontmetrics_helpers.py` holds the per-style reference tables (`VERTICAL_THRESHOLDS_OPT`, `ANCHOR_Y_REF_OPT`, `CLEARANCES_OPT`, `OPTICAL_CORRECTION`) and the anchor-candidate logic described below.
3. **Report** — `fontmetrics_report.py` builds LaTeX table bodies (one column per glyph, a block of rows per style) written to `tex/input/`, which `tex/libertinus-analysis.tex` `\input`s. `combo_matrix.py` + `classifiers.py` produce the base x mark grids. Generated `.tex` fragments and the PDF are committed.
4. **Patch** — `font_patching.py` orchestrates stages on the GPOS lookup and GSUB (see below).

Character sets (which bases, which marks) come from `data/ipa/ipa_unicode.py` as `unicode_groups[NAME]["items"]`, e.g. `BASE_LATIN`, `BASE_IPA`, `MARK_ABOVE`, `MARK_BELOW`.

### Anchor candidate rules

The purpose of the fontmetrics tables is to help a human set above/below anchors. `ANCHOR-HEURISTICS.md` is the first-pass design note; the current rules in `fontmetrics_helpers.py` are:

- **Aspect strings** (`aa` above, `ba` below): the nearest vertical aspect to the glyph's bbox ymax/ymin, as a letter (`a` ascender, `c` capital, `x` x-height, `b` baseline, `d` descender), with a signed delta appended when the extremum is outside that aspect's tolerance band (`x+33`, `d+60`). Capitals (category `Lu`) choose between `c`/`a`; everything else between `x`/`a`.
- **Candidate y** (`get_aya`/`get_bya`): no delta → snap to the per-style reference value. With a delta → reference + delta, then a small optical correction pulling the anchor toward the glyph (subtracted above, added below; 0 for ascenders). The correction is crude (2 units) because the script does not know whether the extremum is a bowl or a flat.
- **Candidate x**: the bbox midpoint for upright styles; for italics the midpoint is slant-corrected to the anchor's y (`get_axm`/`get_bxm`), so an error in y shifts x by about 0.21 units per unit.

Existing designer anchors in the fonts are inconsistent: some are wrong, many are copied between glyphs or styles (`run_anchor_copy_report.py`), and they are not snapped to reference values. Treat them as reliable only in aggregate. The patch is intended to normalize them.

### Patch pipeline (`font_patching.patch_font`)

Stages in order; 1, 4 and 5 are planned and commented out:

1. Delete bad anchors *(planned)*
2. Add glyphs — U+E100 `space_en_base`, an invisible spacing base (CFF charstring built by hand)
3. Human-curated anchors from `data/fontanchors_human/{style}.py` (`bases`, `marks`, `bases_by_name`, `marks_by_name`; overwrite or create, never delete). `regular` is far more complete than the other styles.
4. Normalize designer anchor y *(planned)*
5. Heuristic anchors for glyphs still lacking them *(planned)*
6. Precomposed inheritance — a precomposed glyph lacking an anchor inherits it from its deepest Unicode-decomposition base; glyphs that already have one are reported and left alone
7. GSUB `ccmp` rebuilt from `data/fea/{style}/ccmp.fea` (dot removal, `.cap` accent forms). feaLib's builder destroys GPOS, so it is saved and restored around the build.

### Legacy code

Files with `legacy` in the name (`font_patching_legacy.py`, `font_patching_helpers_legacy.py`, `legacy-geometry.py`, `data/legacy-fontdata/`) are superseded and not on the active paths. `data/vertical_data.py` predates the `*_OPT` tables in `fontmetrics_helpers.py` and disagrees with them in places; the `*_OPT` tables are the ones the code uses.

## LaTeX conventions

From `README-FONTS.md`: fonts are loaded with `fontspec` from `fonts/`; always use `Path = ../fonts/` and always include the file extension (`.otf`, `.ttf`). Semibold is the bold face. The patched family is `\LibertinusSerifPatch`. Table cells render sample glyphs as `\char"XXXX`, with `\cgj` between base and mark in the fontmetrics tables.
