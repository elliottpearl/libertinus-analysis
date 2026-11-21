# Anchor model and anchor candidates

How Libertinus places above- and below-anchors (GPOS mark-to-base classes 0 and 2), and how to calculate a candidate anchor from font metrics alone.

This file is the working reference: every number and formula needed to compute or check an anchor. The report, `tex/libertinus-analysis.tex`, states the model only briefly ("Anchor model", "Italic anchor model", "Semibold italic anchor model", "Mark anchor model"; the Y tables are in "Vertical references, anchor Y coordinates and reference, and clearance"). The derivations, measurements, dates and rejected alternatives are in `ANCHOR-MODEL-HISTORY.md`. When the model changes, update this file and the history, and the report's brief statement if what it says is no longer true.

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
| | x-height `x` | 429 [429, 442] | 429 [429, 450]* | 434 [433, 457]* | 434 [434, 458]* |
| | baseline `b` | 0 [−12, 0] | 0 [−12, 1] | 0 [−12, 1] | 0 [−20, 0] |
| | descender `d` | −232 [−238, −227] | −232 [−238, −227] | −232 [−238, −212] | −232 [−239, −219] |
| anchor Y reference | above, ascender | 885 | 890 | 885 | 890 |
| | above, capital | 850 | 850 | 850 | 850 |
| | above, x-height | 645 | 645 | 645 | 645 |
| | below, baseline | −110 | −110 | −110 | −110 |
| | below, descender | −319 | −319 | −319 | −319 |
| clearance | ascender | 187 | 192 | 187 | 192 |
| | capital | 205 | 205 | 205 | 205 |
| | x-height | 216 | 216 | 211 | 211 |
| | baseline | 110 | 110 | 110 | 110 |
| | descender | 87 | 87 | 87 | 87 |

Semibold's capital row is the patched value. The designer set semibold's capitals near 805 (clearance 160) and compensated only in the `.cap` marks, so marks without a `.cap` form crashed into capitals; the patch moves the capitals to 850 and adds 45 to the `.cap` mark anchors.

The bands are the designer's BlueValues/OtherBlues from the SFDs, except the x-height bands marked *, widened on 2026-11-07 (from 442, 447, 447) so that x-height letters rising 1–11 above the designer's band (italic ɐ ɞ ɡ ɵ ɽ ʂ ʐ ʑ, semibold ɢ ʑ, semibold italic ʐ ʑ) snap to 645 like their base letters; no IPA above-mark overlaps them there. In code these numbers are `VERTICAL_THRESHOLDS_OPT`, `ANCHOR_Y_REF_OPT` and `CLEARANCES_OPT` in `fontmetrics_helpers.py`. The older `data/vertical_data.py` disagrees with them in places and is not used.

**Choosing the aspect.** For the above-anchor of a capital (Unicode category `Lu`, plus U+0294–U+0296), the aspect is always the capital, and the candidate Y always snaps to the capital reference (850), even if `ymax` is above the band: capitals have no ascenders, and what rises above the capline (J's top stroke in the italic styles, T's serifs in the semibold styles, Ø's slash, Ʒ, the hooks of Ƈ Ɠ) is away from the centre where the mark sits. The aspect string still records the excess (`c+34` for semibold italic J). The exception is capital iota Ɩ U+0196, a genuine ascender, which takes the ascender aspect (885; italic styles 890). Italic ʔ ʕ, whose tops are 27 and 38 above the capline, have curated anchors with the bowl overshoot ε = 10 (`ay = 850 + delta − 10`: 867, 878). For everything else, compare `ymax` with the nearer of x-height or ascender. For the below-anchor, compare `ymin` with baseline or descender. The result is written as an aspect string: `x` means `ymax` is inside the x-height band; `x+33` means it is 33 above the aspect value and outside the band.

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

`W` is the advance width (`width` in the fontmetrics).

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

**Measured shift `k` vs model constant `K`.** Each anchor has its own measured shift: how far it lies left of its italic-model position.
- base: `k = W/2 + Y tan θ − X`
- mark: `k = C + Y tan θ − (X − d)`, where `d` is the mark's offset from its axis in regular (0 for a symmetric mark)
- a mark lands `k_mark − k_base` right of the base's midline (n `k = 170`, macron `k = 141`: macron lands 29 left)

Measured shifts vary (about `Y tan θ` at the anchor's height plus a small amount; U+0313 at Y 605: 125, U+0309 at Y 765: 168), and only their differences matter. The model fixes one `K` per class for every base and mark anchor: **K = 150 above, K = −12 below**. These are the medians of the designer's mark shifts (most above-marks 132–168, below-marks −23 to −4), chosen so that most designer mark anchors conform. The designer's base anchors have median shifts of 139 / −1 (lowercase Latin+IPA, above / below) and 173 / −5 (capitals). An anchor conforms if its `k` is close to `K`.

Candidates: `ax = W/2 + ay tan θ − 150` and `bx = W/2 + by tan θ + 12`.

| anchor | ay or by | ax or bx |
|---|---|---|
| above, x-height | 645 | W/2 − 19 |
| above, capital | 850 | W/2 + 23 |
| above, ascender | 890 | W/2 + 31 |
| below, baseline | −110 | W/2 − 10 |
| below, descender | −319 | W/2 − 53 |

Example: semibold italic n has W = 606, giving `ax = 284` and `bx = 293`. The font has 264 and 265 (regular's values), so the macron lands 29 left of the midline.

The cancellation is approximate. `k` for a mark is `Y tan θ` plus a constant, while the designer's base anchors sit near `W/2 − 9` at every height, so the error grows by 2 for every 10 units of height difference between the anchors. The median distance of a designer base anchor from the candidate is about 20 for lowercase and 30 for capitals.

The italic model is the case K = 0. Using it here would put above-marks about 150 too far right. Patch only anchors that do not conform, moving them to these candidates. The non-conforming groups the patch corrected (`.cap` marks without K; a s h J above, set with the slant; marks with unusual k; many capitals; ʮ ʯ transposed) and the ones still open (bowl capitals D B W, A X P above; Æ q j C D d A below; ȵ c above) are listed in `ANCHOR-MODEL-HISTORY.md`, "Semibold italic", and the open ones in `TODO.md`.

### Mark anchors

A mark anchor lies on the mark's own axis: `X = C + Y tan θ + d − K`.
- `C` is where the axis meets the baseline: the horizontal centre of the outline with the slant removed. Measure the centre of the sheared outline `x' = x − y tan θ`.
- `Y` is the mark anchor's height (section 1).
- K is the style's value from the table (0 except in semibold italic).
- `d` is regular's offset of the mark from its axis (`X − C` in regular): 0 for a symmetric mark, e.g. −32 for the acute. An asymmetric mark keeps it in every style.

When the anchors meet, the mark's axis lies on the base's midline: an italic mark is displaced along the italic axis, not straight up or down.

The patch enforces this for the X of symmetric above marks and, since 2026-11-12, symmetric below marks (K below −12 in semibold italic; not the tacks), setting a mark's shift `k = C + Y tan θ − X` to K exactly (mark-axis rule, stage 4, 2026-11-09; threshold 10 until 2026-11-12, now none). `C` is the centre of the de-slanted ink bounds (within 2.2 units of the mirror or 180°-rotation symmetry axis on every symmetric mark; kept 2026-11-12), except for the combining letters that are not boxy: the area centroid for e c h r t (U+0364 U+0368 U+036A U+036C U+036D), and for combining i (U+0365) the stem's midline at the stem's top, carried to the baseline at the slant (`AXIS_MEASURE` in `font_patching_markaxis.py`). Other mark anchors are curated one at a time against the precomposed glyphs. The history of the mark anchors is in `ANCHOR-MODEL-HISTORY.md`, "Mark anchors".

### Central-stem letters

Letters with a central stem and no curl (i, ı, j, ȷ, l, m by its middle stem, I, T, ɪ) have their above anchor, and all but j and ȷ their below anchor, on the stem's axis (stem-axis rule, stage 7b, 2026-11-12): `X = m(y_ref) + (Y − y_ref) tan θ − K`, where `m` is the stem's midline, the mean of its two straight edges read from the control points, and `y_ref` the top of their overlap in height for the above anchor and its bottom for the below anchor. Y is not touched. The rule runs after the curated anchors and sets X over them; derived letters (ɨ ɩ ɫ Ŧ ɱ …) move with their base letter in stage 8, and ɾ ɿ are not in the group (hooked top).

The anchor is carried at the declared θ, not at the stem's own angle (lowercase italic stems are steeper, 12.1–13.5°; I and T shallower, 10–11°): the stem's own angle was tested and rejected, because the designer's dots and precomposed accents sit left of the θ line, not right of it.

In italic and semibold italic, curls move the optical centre, and the rule adapts: dotted i and j put the above anchor over the centre of the dot (11–13 left of the stem's axis); dotless ı and ȷ put it on the axis of that dot, so that an accent takes the dot's place (their curved entry stroke pulls the centre left, and the precomposed ì í î … ĵ ǰ agree); the below anchors of i, ı, l (curled foot) and the above anchor of m (arches) are left out, to be curated. See the report and `tex/stem_axis_test_sheet.pdf`, `tex/stem_angle_test_sheet.pdf`.

### Dots: the dot lookup

The dot above (U+0307), the vertical line above (U+030D) and the dot below (U+0323) on the letters of `data/dot_letters.py` are placed by a second mark-to-base lookup (stage 9b, `font_patching_dotanchors.py`), added to `mark` after the main one; for a base it lists, its anchor replaces the main lookup's (HarfBuzz applies lookups in order, and a later attachment replaces an earlier one), and a base it does not list, or lists without an anchor of that class, keeps the main lookup's. Its mark anchors are copies of the main lookup's. This restores the designer's dot convention: in every style the dot of ḃ ḋ ḣ is at the height of ȧ ṅ and the dot of ỵ at the height of ạ ṇ (ḟ ẛ ṫ are the exceptions, with the dot above the top).

- **Y:** the x-height reference above (645), the baseline reference below (−110), as on an x-height letter.
- **X, in order:** (1) the designer's precomposed letter, where it has the dot at the x-height-letter height (ḃ ḋ ḣ ỵ), so that composed matches precomposed: X = centre of its dot − the base's shift inside it (`fit_base`) − the dot mark's centre + its anchor X; (2) a derived letter of `data/derived_letters.py` whose base is listed inherits the base's dot anchor, moved by `fit_base` (at least `MIN_FIT`), and if that leaves the dot under `MIN_GAP` (the derived letter is drawn a little differently where the dot lands) it is pushed sideways as in (3) (2026-11-21); (3) otherwise the model's X for the x-height body (the ink between the baseline and the x-height): roman, its ink midpoint; italic, `W/2 + Y tan θ − K`; then pushed sideways in steps of 4, up to 200, to the nearest X where the dot keeps `MIN_GAP` from the letter and its centre stays within the body's extent across the slant. A letter with no such X gets no dot anchor.
- **Which letters:** a letter is listed only if its dot is clear in all four styles (gap at least MIN_GAP − 6, or the designer's precomposed position) and sits over the letter's body; the judgement calls among the clear ones are `EXCLUDED_ABOVE` / `EXCLUDED_BELOW` with a reason. The sheet's "Open" group is what remains undecided.
- **MIN_GAP** is the designer's closest dot among ḃ ḋ ḣ in the style: 61 regular, 63 italic, 31 semibold, 40 semibold italic. A vertical line is judged by its own gap on o (38–40 below, 52–67 above), since it is taller than a dot.
- **Precomposed letters** of `data/precomposed_letters.py` (those without a mark on that side) whose base letter is listed inherit its dot anchor by `fit_base` (ḅ ḍ ḥ ķ above, ý ÿ ṕ … below).
- The precomposed dots imply a Y 10–32 off the reference (regular above 659, below −128; the curated mark-zone moves of 2026-11-12, `ANCHOR-MODEL-HISTORY.md`), so a composed ḃ matches a composed ȧ in height, not the precomposed ḃ.

## 4. Where candidates fail

These need curated anchors (`data/fontanchors_human/{style}.py`):
- asymmetric letterforms, where the geometric centre is not the optical one;
- letters that overhang their advance width, such as f and j, in every italic style (the lane midline comes from W);
- the above-anchor of j in every style: the hook pulls the bbox midpoint left of the stem, so X is put on the stem's axis (section 3, central-stem letters). Its Y (and i's) is the candidate's, from the dot: only marks that skip the ccmp dotless swap (U+033F) attach to i or j, so the anchor must clear the dot;
- Æ, whose top edge lies right of the glyph's midpoint: the above-anchor belongs where Ǣ and Ǽ put their accents, the below-anchor under the common stroke;
- in semibold italic, the non-conforming glyphs listed in `ANCHOR-MODEL-HISTORY.md`, "Semibold italic" (bowl capitals and others still open).

## 5. What the code implements

- **Y:** `get_aya` / `get_bya` in `fontmetrics_helpers.py` implement section 2 with ε = 2. `anchor_audit.py` uses them.
- **Mark anchors:** `font_patching_capmarks.py` and `font_patching_addmarks.py` implement `C + Y tan θ − K` with K = 150 in semibold italic.
- **Audit X:** `anchor_audit.py` compares X in sheared coordinates against the centre of the sheared outline, not `W/2`, with K added back in semibold italic.
- **Patch, stage 5:** `font_patching_normalizeanchors.py` moves semibold's capitals to the capital reference, snaps designer anchors within 5 of a Y reference to it, and reports the rest without moving them.
- **Patch, stage 9b:** `font_patching_dotanchors.py` builds the dot lookup (section 3, "Dots"); `run_dot_lookup_sheet.py` tests every candidate.
- **Patch, stage 6:** `font_patching_heuristicanchors.py` writes `get_anchor_candidate` (rounded) into the patched font for each Latin/IPA base that lacks an above- or below-anchor. Curated anchors overrule it; existing anchors are not moved. - **Patch, stage 7b:** after the curated anchors, `font_patching_stemaxis.py` moves the X of the central-stem letters onto the stem's axis (section 3), over designer and curated anchors alike.
- **Fontmetrics tables:** `get_anchor_candidate` in `fontmetrics_helpers.py` gives the candidate (X, Y) for the a? and b? rows: Y from `get_aya` / `get_bya`, X from section 3 at that Y (bbox midpoint in roman, `W/2 + Y tan θ − K` in italic styles). The marks tables use `get_mark_anchor_candidate`: Y is the outline bottom plus (above) or top minus (below) the style's median mark-anchor offset (`MARK_ANCHOR_OFFSET_OPT`), X is `axis_x + Y tan θ − K`, with `axis_x` the de-slanted outline centre stored by the extractor.

## 6. Possible second pass (not implemented)

An earlier design, never implemented and never validated, would shift X from the geometric centre by an amount depending on each glyph's horizontal visual weight:

`anchor_x = centre + dx_norm × outline_width`

`dx_norm` would be set by boolean tags. The extractor already computes the tags (`has_left_weight`, `has_right_weight`, `is_symmetric`, `has_overhang_right`; see `data/fontmetrics/SCHEMA.md`). Nothing reads them yet. The proposed values were: symmetric 0, left weight −0.08, right weight +0.06, overhang right −0.20 added. They predate the lane model and would need re-measuring against it.

Other ideas from that design:
- attach counter-dominant glyphs (b d p q k y) by the counter and stem-dominant glyphs (f g j l t) by the stem;
- for diagonal-stress glyphs (v w y ʋ ɯ ɰ), use a centre that depends on height;
- use the counter centroid or stem centre as an X candidate.
