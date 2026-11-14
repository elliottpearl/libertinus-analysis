# To do

The report's "To do" section (`tex/libertinus-analysis.tex`) is the short list; this file holds the details. Keep the headings here in step with the items there.

## Check the curated anchors in all styles, especially A–Z and a–z

(2026-11-12) Curated anchors were made style by style and at different times, and some disagree between styles about where an anchor belongs. For example, regular p has its below anchor (120, −319) under the stem, but the other styles do not. For each letter, compare the four styles' curated anchors (and the scripted ones they overrule) against the anchor model and the test sheets, and make them agree, or note why they differ.

Part of it is curation that the stem-axis rule leaves to a human (report, "Stem-axis rule" under "Patch j regular, above-anchor"):
- In italic and semibold italic, the below anchors of i, ı and l and the above anchor of m, where a curl moves the optical centre off the stem (the curled foot of i ı l, right; the arches of m). None of the existing values (the designer's i, ı and m, the curated l) is known to be reliable.
- Evidence from the precomposed glyphs, composed minus precomposed with the anchor on the stem: italic ị −14, ḷ +4 (median of the other dot-below letters +11); semibold italic ị −33, ḷ −22 (median −19, spread about ±30); italic ṁ +7, semibold italic −21.
- The ink-area centroid of the bottom zone (baseline to 100 above the stem's straight part) came within 4 units of ị and ḷ in three of four cases.
- Test sheets: `tex/stem_axis_test_sheet.pdf`, `tex/stem_angle_test_sheet.pdf`.

Semibold j: the stem-axis rule puts its above anchor on the stem, because the dot rules apply only in the italic styles, but its dot is 14 units left of the stem (see "Dots, in letters and marks" below). An above anchor of dotted j should be over the dot, as in the italic styles, unless the dot is moved. ȷ, and so ĵ and ǰ, keep the stem.

Left over from the curated-anchor reviews of 2026-10-29 and 2026-11-07 (the rest of those reviews has been resolved in `data/fontanchors_human/`):
- Semibold italic Ƶ U+01B5: above (312, 850) is italic's 462 − 150; the model gives (332, 873), because Ƶ's top is about 23 above the capline. Below (267, −110) matches the old bbox-centre slide; the model gives 299.
- Semibold italic below anchors without K below (−12): Y (277, −110) against the designer's 295, and others about 12 off. Invisible in practice, but adding 12 would make them consistent.
- Regular small X adjustments of 4–10 units on designer anchors (f below 136, r below 140, superscripts ʳ ʷ ʸ ᵐ ᵖ above): deliberate, or only rounding?
- Regular d below (235, −110), against the designer's 221; œ below (408, −110), against the candidate's 388; semibold e above (249, 645), against the candidate's 232.

## Audit the above anchors of the vowels against their precomposed glyphs

The precomposed glyphs are many and good evidence (survey of 2026-11-07). Where the patched anchor differs from the median mark centre of the precomposed glyphs by more than 15:
- italic o +20, O +22, E −20, Y −17;
- semibold y −19, Æ −16;
- semibold italic y +29 (regular's anchor, copied), Y −58, a +18, A −15, Æ −19.

Regular O is within 12, but its marks land 16–19 left of the centre line of O.

Two cautions:
- Italic and semibold italic Y and U were curated so that shaped marks land on their axes, and their precomposed glyphs disagree by 14–58.
- The semibold italic precomposed glyphs also run 30–40 right of the anchor model for g and E.

The vowel base anchors have not changed since. With the symmetric marks on their axes (2026-11-09), the median offset of composed marks from the precomposed glyphs per letter confirms the lowercase figures (italic o +19, semibold y −18, semibold italic y +30, a +22). It also adds i: marks on ı land 12–18 right of ì í î ï in every style (regular +16, italic +18, semibold +18, semibold italic +12). The capitals were not remeasured.

O and o lean to the left, unlike most of the other humanist letters, so their optical centre at the top may lie right of the bbox midpoint. That is a reason to move their above anchors right, to weigh in the audit.

## Revise the heuristic anchors of letters with a hook, tail or stroke (clear the mark zone, not the extreme point)

This is how stage 8 moves Y away from an added part (the hook, tail or stroke of a derived letter). Now the anchor moves by how much further the added part reaches than the base letter within 120 units of the mark's axis, and a tail at the bottom takes the candidate's Y, from the letter's lowest point. Both use the extreme point, not where the marks actually come close, so most anchors get more clearance than they need and a few too little (ʛ above overlaps one mark).

Alternatives measured on 2026-11-11 with every IPA mark:
- (A) The tightest mark on the derived letter gets the base letter's tightest gap. This removes over-clearance on 83 of 148 anchors but adds clearance on 43.
- (B) The same, but only toward the glyph, with a floor of about 20, so that only over-clearance and near-collisions change.

## Write instructions for using CGJ

These are general instructions for using CGJ U+034F to block unwanted normalization. A below-mark typed after a precomposed letter that already has an above-mark is reordered and recomposed by normalization:
- ì + tilde below becomes ḭ + grave, which brings back the dot of i;
- Ǻ + dot below becomes Ạ + ring + acute.

There are 130 such cases among the precomposed letters. It is a decomposition problem, to be avoided with a CGJ (or a dotless base) whether or not the font has mark-to-mark positioning. The report's sections "Lowercase i with tilde below and grave above, in italic and semibold italic" and following explore it, and "Floating tones" uses CGJ for a similar reason.

The instructions should say when CGJ is needed, where it goes, and its cost: a precomposed glyph before CGJ has no below-anchor, so the below-mark falls back to a default position.

## Check GSUB: dot removal and composition into precomposed letters

These come from the stub sections of the report ("Patch j dot removal for three above-marks", "Dot removal", "Precomposed characters"):
- The dot of i and j should be removed before any above-mark, but it is not removed for three: x above, turned tilde, double macron. Patch `ccmp` so that the dotless substitution fires in this context too.
- Check that the dot removal for i and j is complete.
- Where a precomposed character exists, a doublet (base + combining mark) or a triplet (base + two combining marks, in either mark order) should be turned into it by GSUB. Check that it is.

## Long term: add mark-to-mark positioning

Add stacking for the common above-marks in all four styles: ring, dieresis, macron, acute, grave, circumflex, caron, tilde, breve. The designer's stacked precomposed glyphs (ḕ, ṏ, ẫ, …) could supply the mark-to-mark anchors, as the precomposed capitals do for stage 4.

## Long term: audit the SFD sources for consistent component references

Do this across the four styles, and perhaps redraw or redefine components for consistency.

### Copies that could be references

These are glyphs that copy another glyph's splines: a derived letter drawn as a copy of its base, or a precomposed letter drawn as a copy of base and mark. As references, a correction to the base would reach every glyph built on it, and the derived and precomposed stages would not need to find the base in the outline again.

### Dots, in letters and marks

- The precomposed dot-below letters reference the dot above, moved below the letter (`uni0307` in regular and semibold, the spacing `dotaccent` in italic and semibold italic). The exceptions are ṃ (and regular ṇ), which reference the combining dot below `dotbelowcomb`. So the dot of a precomposed letter and the dot of a composed one differ in size: regular 100 against 108, italic 98 against 110, semibold 124 against 109, semibold italic 120 against 122.
- The shapes differ too:
  - regular and semibold: four-point circles;
  - italic: `uni0307` is a circle, but `dotaccent` and `dotbelowcomb` are skewed ovals;
  - semibold italic: `dotaccent` is a four-point skewed oval and `dotbelowcomb` a six-point one.
- The dot of semibold j is 14 units left of its stem (regular −3), a flaw in the drawing of j; ĵ and ǰ put the accent on the stem (+2). Options: move the dot onto the stem, or leave it and put j's above anchor over the dot (see "Check the curated anchors" above).
- Regular ṇ references both dots and n twice, so its two dots overlap.
- The diaeresis below U+0324 is two `dotbelowcomb` in regular and italic, but the precomposed ṳ is built from a diaeresis (`uni0308` in regular, semibold and semibold italic, the spacing `dieresis` in italic), with smaller dots in regular and italic.

### Commas and horns, in letters and marks (2026-11-11)

- In semibold and semibold italic the combining commas are drawn at the lighter style's weight. U+0312–U+0315 have 0.98 to 1.05 times the ink of regular's (or italic's), and semibold's comma below U+0326 has 0.91, where the designer's own semibold comma and quotes have 1.21 to 1.27.
- The horn U+031B is regular weight in semibold (1.00).
- The koronis U+0343 is a reference to `uni0313` in regular and italic, a reference to the horn in semibold (which had no mark anchor), and a horn-sized outline of its own in semibold italic. The patch curates both anchors (report, "Greek koronis U+0343" under "Comma-style marks").
- The spacing Greek and modifier signs are bolded only in part:
  - U+02BC, U+02BB, psili U+1FBF and koronis U+1FBD are about 1.11 in semibold;
  - U+1FBF and U+1FBD are 1.00 in semibold italic;
  - reversed comma U+02BD, dasia U+1FFE and varia U+1FEF are 1.00 (varia is regular's outline).
- The precomposed Greek letters reference neither combining mark: ἀ ἐ Ἀ ῤ reference U+02BC (U+1FBD in semibold italic ἀ), and italic draws its own.
- After a base letter, HarfBuzz shapes U+0343 as U+0313, its canonical equivalent, so a koronis on a letter shows the style's comma above. That comma's weight matters more than the koronis glyph.
- Options: embolden the combining commas (as stage 3's `embolden()` does for the marks it copies), or derive them from the style's own comma; make U+0343 the style's U+0313.

## Long term: add the remaining missing glyphs (ỿ, Ʉ)

The drafts of the other missing letters (Ɇ Ɍ Ɏ ɏ Ɉ ẜ ẝ ꝥ ꞓ Ɱ ꭒ Ɋ Ỻ Ⅎ …) are in the patch since 2026-11-14 (stage 2, `data/draft_glyphs/`). Two remain:

- ỿ (U+1EFF) in italic, semibold and semibold italic. Its loop should be drawn as a broad-nib pen stroke, as Noto Serif's and Junicode's are, while respecting the counter of regular's ỿ. Components, the method of the drafts, do not work for it.
  - First attempts (2026-11-14, `pen_stroke.py`, `draft_y_pen` in `missing_glyphs.py`) show that no fixed nib angle fits. Libertinus's y descender is nearly a hairline (43 in regular, against o's 34 and 88), so a fixed nib draws either a nearly monoline loop or a heavy one. The pen has to turn along the stroke: steep where it leaves the descender, at o's stress round the bottom, and along the return stroke at the end.
  - Open: that pen twist, and which part of regular's counter to keep (its teardrop shape, its size, or the loop's overall size).
- Ʉ (U+0244), which exists only in regular (outside the base groups).
