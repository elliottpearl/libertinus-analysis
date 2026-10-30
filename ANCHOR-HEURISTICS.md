# Anchor model and anchor candidates

How Libertinus places above- and below-anchors (GPOS mark-to-base classes 0 and 2), and how to calculate a candidate anchor from font metrics alone.

The source of truth is the report, `tex/libertinus-analysis.tex`: the sections "Anchor model", "Italic anchor model", "Semibold italic anchor model" and "Vertical aspects, anchor Y coordinates and reference, and clearance". This file summarizes them with the numbers needed for calculations. If the two disagree, the report is right and this file should be updated.

A candidate is a geometric centre. A type designer places anchors at the optical centre, where a mark looks best; this project substitutes something it can compute. Designer anchors are inconsistent (many are copied or wrong), so compare candidates with them only in aggregate.

## 1. The model

- **The base anchor is where the mark goes.** The clearance between base and mark is built into the base anchor, not the mark. (Noto is the opposite: base anchors sit on the x-height or baseline, the mark anchor is at the origin, and the clearance is in the mark outline.)
- **The mark anchor is near the centre of the mark.** For a symmetric mark it is at the horizontal centre of the outline. For an asymmetric mark such as the acute or grave, it is a few units to one side.
- **The mark anchor's height:** for an above-mark it is about 140 above the bottom of the outline. That is near the top of a tall mark (circumflex) and above the top of a short one (macron, dot). An x-height base's above-anchor is 216 above the x-height, so the bottom of a tall mark is about 75 above the base, and a short mark sits a little higher. The report does not yet describe below-mark anchor heights.
- **Italic:** the same model applies along the italic axis (section 3).

## 2. Anchor Y (all styles)

The Y of a base anchor is the glyph's vertical aspect plus that aspect's clearance. Roman and italic styles use the same Y values, so marks sit at the same heights in all styles.

| | aspect | regular | italic | semibold | semibold italic |
|---|---|---|---|---|---|
| aspect Y, band | ascender `a` | 698 [688, 698] | 698 [688, 698] | 698 [690, 698] | 698 [696, 705] |
| | capital `c` | 645 [645, 658] | 645 [645, 658] | 645 [645, 662] | 645 [645, 662] |
| | x-height `x` | 429 [429, 442] | 429 [429, 442] | 434 [433, 447] | 434 [434, 447] |
| | baseline `b` | 0 [−12, 0] | 0 [−12, 1] | 0 [−12, 1] | 0 [−20, 0] |
| | descender `d` | −232 [−238, −227] | −232 [−238, −227] | −232 [−238, −212] | −232 [−239, −219] |
| anchor Y reference | above, ascender | 885 | 890 | 885 | 890 |
| | above, capital | 850 | 850 | **805** | 850 |
| | above, x-height | 645 | 645 | 645 | 645 |
| | below, baseline | −110 | −110 | −110 | −110 |
| | below, descender | −319 | −319 | −319 | −319 |
| clearance | ascender | 187 | 192 | 187 | 192 |
| | capital | 205 | 205 | 160 | 205 |
| | x-height | 216 | 216 | 211 | 211 |
| | baseline | 110 | 110 | 110 | 110 |
| | descender | 87 | 87 | 87 | 87 |

The bands are the designer's BlueValues/OtherBlues from the SFDs. In code these numbers are `VERTICAL_THRESHOLDS_OPT`, `ANCHOR_Y_REF_OPT` and `CLEARANCES_OPT` in `fontmetrics_helpers.py`. The older `data/vertical_data.py` disagrees with them in places and is not used.

**Choosing the aspect.** For the above-anchor of a capital (Unicode category `Lu`, plus U+0294–U+0296), the aspect is always the capital, and the candidate Y always snaps to the capital reference (850; semibold 805), even if `ymax` is above the band: capitals have no ascenders, and what rises above the capline (J's top stroke in the italic styles, T's serifs in the semibold styles, Ø's slash, Ʒ, the hooks of Ƈ Ɠ) is away from the centre where the mark sits. The aspect string still records the excess (`c+34` for semibold italic J). The exception is capital iota Ɩ U+0196, a genuine ascender, which takes the ascender aspect (885; italic styles 890). Italic ʔ ʕ, whose tops are 27 and 38 above the capline, have curated anchors with the bowl overshoot ε = 10 (`ay = 850 + delta − 10`: 867, 878). For everything else, compare `ymax` with the nearer of x-height or ascender. For the below-anchor, compare `ymin` with baseline or descender. The result is written as an aspect string: `x` means `ymax` is inside the x-height band; `x+33` means it is 33 above the aspect value and outside the band.

**Candidate Y.**
- Inside the band: snap to the reference (`ay = 645` for `x`).
- Outside the band: the reference plus the delta, moved back toward the glyph by an overshoot correction ε. Above: `ay = ref + delta − ε`. Below: `by = ref + delta + ε`. Equivalently, `ay = ymax + clearance − ε`.

**Overshoot ε.** A flat stem overshoots its aspect by 2. Bowls overshoot by 6 at the descender, 10 at the baseline, 10 at the x-height and 13 at the capital height. Ascenders get 0 (`ymax = 698` for every full ascender). Bbox metrics cannot tell a bowl from a stem, so the code uses 2 everywhere except ascenders (`OPTICAL_CORRECTION`). A human choosing a bowl value should use the bowl numbers.

## 3. Anchor X

Calculate Y first: in italic styles X depends on the anchor's own height (aspect plus clearance), not the aspect's height. An error of 10 in Y moves X by about 2.

| style | θ | tan θ | base candidate X | K above | K below |
|---|---|---|---|---|---|
| regular, semibold | 0 | 0 | bbox midpoint `(xmin + xmax) / 2` | 0 | 0 |
| italic | 12° | 0.2126 | `W/2 + Y tan θ` | 0 | 0 |
| semibold italic | 11.5° | 0.2035 | `W/2 + Y tan θ − K` | 150 | −12 |

`W` is the advance width (`width` in the fontmetrics JSON).

### Roman (regular, semibold)

The candidate is the midpoint of the bounding box. It suits mostly symmetric letterforms.

### Italic

The glyph's *italic lane* is its advance-width box slanted by θ, and the lane's midline is `X = W/2 + Y tan θ`. The candidates are the midline at the anchor heights: `ax = W/2 + ay tan θ` and `bx = W/2 + by tan θ`.

| anchor | ay or by | ax or bx |
|---|---|---|
| above, x-height | 645 | W/2 + 137 |
| above, capital | 850 | W/2 + 181 |
| above, ascender | 890 | W/2 + 189 |
| below, baseline | −110 | W/2 − 23 |
| below, descender | −319 | W/2 − 68 |

Example: italic n has W = 518, giving `ax = 396` and `bx = 236`. The font has 394 and 235. The above-anchor is right of the below-anchor by `(ay − by) tan θ`, about 160 for an x-height letter.

### Semibold italic

This style has its own model, and the patch keeps it. The designer used regular's anchors on slanted outlines: 42 of 44 above/below mark anchors and 319 of 384 above/below base anchors are regular's coordinates exactly. Neither base anchor nor mark anchor carries `Y tan θ`. Both are left of the italic-model position by about the same shift K, so the errors cancel when the anchors meet.

Candidates: `ax = W/2 + ay tan θ − 150` and `bx = W/2 + by tan θ + 12`.

| anchor | ay or by | ax or bx |
|---|---|---|
| above, x-height | 645 | W/2 − 19 |
| above, capital | 850 | W/2 + 23 |
| above, ascender | 890 | W/2 + 31 |
| below, baseline | −110 | W/2 − 10 |
| below, descender | −319 | W/2 − 53 |

Example: semibold italic n has W = 606, giving `ax = 284` and `bx = 293`. The font has 264 and 265 (regular's values), so the macron lands 29 left of the midline.

The cancellation is approximate. K for a mark is `Y tan θ` plus a constant, while the designer's base anchors sit near `W/2 − 9` at every height, so the error grows by 2 for every 10 units of height difference between the anchors. The median distance of a designer base anchor from the candidate is about 20 for lowercase and 30 for capitals.

The italic model is the case K = 0. Using it here would put above-marks about 150 too far right. Patch only anchors that do not conform, moving them to these candidates. The report lists the known non-conforming glyphs and marks.

### Mark anchors

A mark anchor lies on the mark's own axis: `X = C + Y tan θ − K`.
- `C` is where the axis meets the baseline: the horizontal centre of the outline with the slant removed. Measure the centre of the sheared outline `x' = x − y tan θ`.
- `Y` is the mark anchor's height (section 1).
- K is the style's value from the table (0 except in semibold italic).
- An asymmetric mark keeps regular's offset from its axis.

When the anchors meet, the mark's axis lies on the base's midline: an italic mark is displaced along the italic axis, not straight up or down.

## 4. Where candidates fail

These need curated anchors (`data/fontanchors_human/{style}.py`):
- asymmetric letterforms, where the geometric centre is not the optical one;
- letters that overhang their advance width, such as f and j, in every italic style (the lane midline comes from W);
- in semibold italic, the non-conforming glyphs and marks listed in the report (capitals, `.cap` marks, a s h J, marks with unusual K).

## 5. What the code implements

- **Y:** `get_aya` / `get_bya` in `fontmetrics_helpers.py` implement section 2 with ε = 2. `anchor_audit.py` uses them.
- **Mark anchors:** `font_patching_capmarks.py` and `font_patching_addmarks.py` implement `C + Y tan θ − K` with K = 150 in semibold italic.
- **Audit X:** `anchor_audit.py` compares X in sheared coordinates against the centre of the sheared outline, not `W/2`.
- **Patch, stage 6:** `font_patching_heuristicanchors.py` writes `get_anchor_candidate` (rounded) into the patched font for each Latin/IPA base that lacks an above- or below-anchor. Curated anchors overrule it; existing anchors are not moved.
- **Fontmetrics tables:** `get_anchor_candidate` in `fontmetrics_helpers.py` gives the candidate (X, Y) for the a? and b? rows: Y from `get_aya` / `get_bya`, X from section 3 at that Y (bbox midpoint in roman, `W/2 + Y tan θ − K` in italic styles). The marks tables use `get_mark_anchor_candidate`: Y is the outline bottom plus (above) or top minus (below) the style's median mark-anchor offset (`MARK_ANCHOR_OFFSET_OPT`), X is `axis_x + Y tan θ − K`, with `axis_x` the de-slanted outline centre stored by the extractor.

## 6. Possible second pass (not implemented)

An earlier design, never implemented and never validated, would shift X from the geometric centre by an amount depending on each glyph's horizontal visual weight:

`anchor_x = centre + dx_norm × outline_width`

`dx_norm` would be set by boolean tags. The extractor already writes the tags to the fontmetrics JSON (`has_left_weight`, `has_right_weight`, `is_symmetric`, `has_overhang_right`; see `data/fontmetrics/SCHEMA.md`). Nothing reads them yet. The proposed values were: symmetric 0, left weight −0.08, right weight +0.06, overhang right −0.20 added. They predate the lane model and would need re-measuring against it.

Other ideas from that design:
- attach counter-dominant glyphs (b d p q k y) by the counter and stem-dominant glyphs (f g j l t) by the stem;
- for diagonal-stress glyphs (v w y ʋ ɯ ɰ), use a centre that depends on height;
- use the counter centroid or stem centre as an X candidate.
