# Anchor model: history, evidence and decisions

This file keeps the detail behind the report's anchor model sections (`tex/libertinus-analysis.tex`: "Anchor model", "Italic anchor model", "Semibold italic anchor model", "Mark anchor model"): the derivations, measurements, figures, dates and rejected alternatives. The report states only the current model briefly; the numbers needed to compute anchors are in `ANCHOR-HEURISTICS.md`. Add new findings and open decisions here, and change the report only when its brief statement of the model is no longer true. It subsumes the former `MARK-ANCHOR-HISTORY.md` (2026-11-14).

## Base anchors

### Roman

The model in full, as the report stated it until 2026-11-14. Every font has five vertical reference lines (ascender, capline, x-height, baseline, descender). Each glyph has a tight bounding box and an ideal bounding box, where it seems to live once the overshoots of bowls and serifs are discounted; the design goal is that the top and bottom of the ideal bounding box are reference lines, except for non-full ascenders and descenders. The clearance is the vertical distance between the ideal bounding boxes of base and mark. In a consistently designed font it is the same for every glyph at a given reference line (dots should not dance below the baseline from letter to letter, and acutes and graves on letters of the same height sit at the same height). In Libertinus it is encoded in the base anchor: above-anchor Y = top of the ideal bounding box + the clearance of the nearest reference line, below-anchor Y = bottom − that clearance; for a non-full ascender or descender the edge is not the reference line, but the clearance is the same. X is at the horizontal optical centre, which depends on the letterform and on what the designer thinks looks best; for a mostly symmetric letter in roman the candidate is the bbox midpoint.

Mark anchors: a symmetric mark's anchor is at its horizontal centre, an asymmetric one's (acute, grave) a few units to one side. An above-mark's anchor is about 140 above the bottom of its outline: near the top of a tall mark (circumflex), above the top of a short one (macron, dot). An x-height base's above-anchor is 216 above the x-height, so the bottom of a tall mark is about 75 above the base.

Noto, for comparison (report, Figure 2): base below-anchor on the baseline, above-anchor at the x-height, overlay inside the glyph; the mark's anchor at the origin (0, 0) with the outline drawn below it. So Noto encodes the clearance in the mark, Libertinus in the base.

### Italic

The lane midline is `X = W/2 + Y tan θ` (θ = 12°). The height in the formula is the anchor's own height (edge of the ideal bounding box ± clearance), not the reference line's, so Y must be found before X; a 10-unit error in Y moves X by about 2. Worked values: above-anchor at W/2 + 137 (x-height, ay = 645), W/2 + 181 (capital, 850), W/2 + 189 (ascender, 890); below-anchor at W/2 − 23 (baseline, −110), W/2 − 68 (descender, −319). A mark's anchor is at `C + Y tan θ`, C being where its axis meets the baseline (the outline's horizontal centre with the slant removed); an asymmetric mark keeps its roman offset from the axis. The midline is a geometric centre, not an optical one.

### Semibold italic

The derivation, as the report stated it until 2026-11-14.

- **The designer's anchors are regular's.** 42 of the 44 above- and below-mark anchors, and 319 of the 384 above- and below-anchors of bases, have exactly regular's coordinates. They do not follow the slant: an above-anchor sits left of where the italic model puts it by roughly the amount the slant has moved the outline at that height, for base and mark alike, so the errors cancel when the anchors meet and the mark's axis lands near the base's midline.
- **Shift k.** For a base anchor `k = W/2 + Y tan θ − X`; for a mark `k = C + Y tan θ − (X − d)`, with d the mark's offset from its axis in regular (0 if symmetric; −32 for the acute). A mark lands `k_mark − k_base` right of the base's midline. Figure 4 of the report: n above k = 170, macron k = 141, so the macron lands 29 left of the midline of n. With K = 150 the model's positions would be 20 right of n's designer anchor and 9 left of the macron's.
- **Why k varies.** A copied X carries no slant, so k ≈ Y tan θ at the anchor's own height plus a small amount from how the outline was drawn: comma above U+0313 (anchor Y 605) k = 125, hook above U+0309 (Y 765) k = 168. Only differences of k move a mark off the midline, so any single value works if every base and mark anchor uses it.
- **K.** K = 150 above (median shift of the designer's above-marks; most 132–168) and −12 below (median of the below-marks; most −23 to −4), taken from the marks so that most designer mark anchors already conform. The designer's base anchors have median shifts 139 above / −1 below on lowercase Latin and IPA, 173 / −5 on capitals. tan θ = 0.2035.
- **Candidates.** `ax = W/2 + ay tan θ − 150`, `bx = W/2 + by tan θ + 12`: W/2 − 19 (x-height), W/2 + 23 (capital), W/2 + 31 (ascender); W/2 − 10 (baseline), W/2 − 53 (descender). Semibold italic n, W = 606: ax = 284, bx = 293; the font has 264 and 265, regular n's values.
- **The cancellation is approximate.** A mark's k grows with its own anchor height, but the designer's base anchors sit near W/2 − 9 at every height, so they do not move right for a capital or an ascender. The error of a mark on a base grows by 2 units for every 10 of height difference between the anchors. Median distance of a designer base anchor from the candidate: about 20 (lowercase), 30 (capitals).
- **Never the italic model (decided 2026-10-12).** A base anchor without K would put every above-mark about 150 too far right, since the marks carry K. The patch keeps conforming designer anchors and moves only the others: a base anchor to the candidate, a mark anchor to `C + Y tan θ + d − K`.

What the patch corrected in the original font:

- The capital forms of the above-marks (`grave.cap`, …) lacked K and landed 160 to 190 left of the middle of a capital; set from the precomposed capitals, with K (stage 4).
- The above-anchors of a, s, h and J were set with the slant, as in italic, so marks landed 130 to 190 too far right; deleted and replaced by candidates (stages 1 and 6).
- Marks whose k was far from K (dieresis, tilde, inverted breve, hook above, koronis, right tack below, tilde below): on the model by the mark-axis rule or curated anchors (see "Mark anchors" below).
- Many capitals and other letters far from the candidate now have candidates, curated or stem-axis anchors, or inherited anchors; the transposed anchors of ʮ and ʯ are replaced by candidates.

Still open (as of 2026-11-14; also in `TODO.md`, "Check the curated anchors"):

- The bowl capitals and a few others keep the designer's above-anchor, 40 to 60 left of the candidate: D, B, W; A and X about 30 left, P 32 right. To be curated one by one (no bowl-capital rule; declined 2026-11-06). On 2026-11-18 R was kept and Q given the candidate, which is O's anchor (Q's bowl is O's).
- Designer below-anchors far from the candidate: Æ (+123), q (+115), j (−60), C and D (±55), d (−47), A (−41); above, ȵ (−63) and c (+39). On 2026-11-18 r below was kept, t and p below and y above given the candidate, and Ƣ ƣ curated in every style (far-anchor test sheet).
- Overhanging letters: the above-anchor of f is still the candidate and the below-anchor of j the designer's, in both italic styles; to be checked by eye.
- The Hebrew ligatures U+05F0–U+05F2 have above- and below-anchors in this lookup in semibold italic only; harmless, left as they are.

### The dot lookup (2026-11-20)

The reference-line model puts every mark on an ascender or descender letter at the ascender or descender reference. For p and q below that was decided on 2026-11-18 (`TODO.md`): a baseline anchor beside the descender lets the bridge, tilde and macron below overlap the descender unless the anchor is pushed to the bowl's outer edge (italic p: a gap of o's size for the wide marks only about 160 right of the designer's 248, past the bowl's ink at the baseline, 96–349). Narrow marks are another matter: the dot is clear at the designer's italic baseline anchor (gap 43, against 78 on o) and the vertical line nearly so (4 on p, 37 on q).

The designer's precomposed letters follow a dot convention rather than the reference lines: ḃ ḋ ḣ have the dot exactly at the height of ȧ ṅ, and ỵ at the height of ạ ọ ṇ, in all four styles (regular 547..647 and −208..−108, italic 523..619 and −163..−67, semibold 510..634 and −176..−52, semibold italic 512..632 and −180..−60); ḟ ẛ ṫ put it above the top. The dot lookup restores that convention for U+0307 and U+0323 without changing the main model: a second mark-to-base lookup, after the main one, whose anchors replace the main lookup's for the letters it lists. Tested with HarfBuzz: p̣ moves to the baseline, p̱ and unlisted letters are unchanged, and a base listed for one side only keeps the main lookup's position for the other (an empty anchor makes the lookup skip). The patched fonts do not stack two below marks by mark-to-mark, so the lookup's order relative to `mkmk` does not matter for p̣̱; it is appended last.

Other fonts: Gentium Plus and Charis SIL split their mark-to-base lookups by attachment (above, below, ogonek, cedilla), not by mark width; dots and vertical lines are in the same lookups as every other mark. Gentium Plus, Junicode and Charis regular put every below mark on p and q at the baseline under the bowl; Noto Serif under the descender; Charis italic p at the baseline and q at the descender. None places the dot differently from the wider marks.

The vertical lines: U+030D goes with the dot above (`LINE_ABOVE`): every listed letter's line gap is within 1 of the line's gap on o, except semibold d (42 against 52). U+0329 does not (`LINE_BELOW` off): it collides on the italic y family (y ɏ 17, ƴ 9) and is tight on semibold p q þ ƴ ꝥ (26–30 against 39 on o).

The first list (2026-11-20, `tex/dot_lookup_test_sheet.pdf`): above b d h (designer) k þ ɗ ɠ ʠ ɮ ⱨ ⱪ; below p q y (designer) þ ɲ ɳ ɱ ɥ ʮ ʯ ɏ ƴ ꝥ (ŋ was in it at first and taken out the same day: its hook curls under the letter, so the push put the dot under the left stem, italic x 45; Gentium Plus, Charis SIL, Noto Serif and Junicode all put marks on ŋ under the descender). ʎ above is excluded: a dot at the x-height on turned y looks odd. The candidates left out, with reasons, are in `data/dot_letters.py`. Since HarfBuzz composes y + U+0323 into ỵ (and ý + U+0323 into ỵ + acute), y's own dot anchor is reached only with CGJ; it matters through the letters that inherit it (ɏ ƴ), and the y-family precomposed letters' inherited dot-below anchors are never reached. Likewise b d h + U+0307 become ḃ ḋ ḣ, but ḅ ḍ ḥ + U+0307 use their inherited dot anchors. Known tight cases kept: italic y family below (the designer's ỵ itself has a gap of 14), semibold d above (28, from ḋ), regular ⱪ above (55).

## Mark anchors

Terms: `k` is a mark's shift, `k = C + Y tan θ − X`: the centre of the mark's outline on its own axis (C, where the axis meets the baseline) at the anchor's height, minus the anchor's X. `K` is the style's shift: 0, or in semibold italic 150 above and −12 below (`ANCHOR-HEURISTICS.md` §3). "Lower", "higher", "left" and "right" describe where a mark lands on a base whose anchor conforms. A mark lands lower when its anchor is further above its outline, and left when its anchor is further right.

### Evidence

Each mark can be checked in three ways:

1. Its X offset from its axis, compared with regular.
2. The distance between its anchor and its outline, compared with regular. The base anchors have the same Y in every style, so a mark sits at the same height in every style only if this distance is the same.
3. The designer's precomposed glyphs. HarfBuzz substitutes them wherever they exist (authors are not expected to use CGJ), so a composed combination should match them. They are not consistent between styles, though: the macron of ō was 18 units lower than the combining macron in regular, but 32 units higher in italic. Horizontally they also carry the offsets of the base anchors, so for X they can confirm a finding but not settle one: the X of a symmetric mark is set by the model (the mark-axis rule). Vertically they are better evidence: every x-height base has its above anchor at 645, so where the offset of a composed mark from the precomposed glyphs is the same on every base, it belongs to the mark's anchor.

### How mark anchors change

The mark anchors have been reviewed style by style, against regular, the designer's precomposed glyphs and the mark zone figures. There is no scripted audit of them, as there is of base anchors (`anchor_audit.py`). They change in three ways:

- The capital forms (`grave.cap`, `acute.cap`, …) are set from the precomposed capitals (stage 4).
- A symmetric mark is put on its own axis (the mark-axis rule, stage 4).
- Everything else is changed one anchor at a time, as a curated anchor (stage 7), where the precomposed glyphs support the change. For Y the evidence is the median offset of the composed mark from the precomposed glyphs. A curated mark anchor is the final anchor and obeys the mark-axis rule itself; stage 4 skips it, and reports it if it does not.

### Stage 1, semibold: the `top_punkt` class merged

The designer's second above class `top_punkt` (class 1) is merged into the above class. Its 12 marks (dot above, diaeresis, hook above, ring above, U+0312, U+0313, U+0314, U+031A, U+0351, U+0357, U+0363 and `hookabovecomb.cap`) move to class 0 with their anchors raised by 96 units, the difference between the two classes' base anchors. They sit where they did on a lowercase letter, but now attach to every base with an above anchor, not only the 24 with a `top_punkt` anchor.

### Stage 3, semibold and semibold italic: added marks

The combining marks the style lacks are added, and semibold's U+0358–U+0363, which were copies of the capital accents, are replaced. Their anchors are regular's. In semibold italic the outline is italic's, moved right 12 units, with regular's anchor. This lands the added above marks 7 to 15 units left of the model, inside the spread of the designer's own marks (k from 111 to 168).

### Stage 4: capital forms

In all styles the capital forms are set from the designer's precomposed capitals: on the axis for a symmetric mark, at the precomposed offset for an asymmetric one, with K = 150 in semibold italic. This fixes semibold italic, whose capital forms lacked K and landed 120 to 160 units left, and italic, where only `grave.cap` had an anchor (in the wrong class).

Italic's eight `.cap` anchors are curated (2026-11-07). Each X is fitted so that the accent lands, as a median over the capitals, where the designer drew it in the precomposed glyphs, as in regular (stage 4 had left the symmetric marks about 14 units left of them). The fit was made after italic O, U and Y took the median accent centre of their own precomposed glyphs as their above-anchor X (493, 508, 441).

### Curated mark anchors before 2026-11-09 (stage 7)

#### All styles: seven tall below marks (2026-11-08)

Tacks U+0318 and U+0319, half rings U+031C and U+0339, plus sign U+031F, ring U+0325, up arrow U+034E. They rose 82 to 94 units above their anchor, against 33 to 77 for the other below marks. So at the descender's below anchor (Y = −319) each overlapped 1 to 13 of the 26 to 31 Latin and IPA descenders, and under baseline letters their median gap was 7 to 26 units, against about 40 for marks such as the vertical line below. Each anchor was moved up, X unchanged, so that the mark rises 62 above it, as U+0329 and U+0348 do. No below mark now overlaps a descender, and their median gap under baseline letters is 38 to 47. The precomposed Ḁ and ḁ confirm the ring (within 2 units in regular, italic and semibold italic). Lowering the descender reference to −342 instead also removed the overlaps, but left the crowding under baseline letters and moved every mark under descenders.

#### All styles: up and down tacks below U+031D and U+031E (2026-11-11)

Both tops are 62 above the anchor, so 48 below the baseline on an x-height letter, as the left and right tacks and the vertical line below. X is along the slant in the italic styles. The two are the same outline turned over. Other fonts level their boxes (the up tack's tip with the down tack's bar, within 0 to 11 units: Gentium Plus, Noto Serif, Junicode, DejaVu Serif, FreeSerif), and none levels the bars. Libertinus, like Linux Libertine O, put the down tack 37 units deeper than the up tack (gaps 33 and 70 on o; 45 and 58 in semibold italic). So the up tack was the tightest below mark, clearing descenders by 4 to 7 units, and the down tack among the loosest.

#### All styles: tacks below U+0318 and U+0319

X is centred on the whole outline, along the slant in the italic styles, with K = −12 in semibold italic (regular earlier, the other styles 2026-11-11). The designer's anchors, the same as in Linux Libertine O, split the difference between the outline and the vertical stroke: the stroke landed 25 to 39 units off centre one way and the outline 19 to 36 the other. Fonts that centre the tacks centre the whole outline, which is also the middle of the horizontal stroke, and none centres the vertical stroke (Gentium Plus, Noto Serif, Junicode and DejaVu Serif, within about 10 units; 2026-11-11). The tacks have no precomposed glyphs, so the model decides. They now land with each style's other below marks.

#### Semibold

- Grave and acute 30 units lower (713 to 683), as in regular. The grave keeps the designer's X = −127, 10 units (median) from the precomposed glyphs. The grave and acute tone marks U+0340 and U+0341, which stage 3 adds at 713, have the same anchors, as in regular (2026-11-11).
- Ring above lowered 27 to 715, the height of the ring in ů, and vertical line above lowered 31 to 688, as in the other styles (2026-11-01).
- Half rings above U+0351 and U+0357 (2026-11-08): after stage 1 they landed 20 to 32 units low. They now have regular's anchor-to-outline offsets, (90, 623) and (82, 613). The X of about +100 is right: semibold draws these marks right of the origin.
- Koronis U+0343 (−92, 539) (2026-11-11): the designer's is a reference to the horn and had no mark anchor. It is placed as regular's U+0313, as in semibold italic.
- Inverted breve U+0311 −217 and tilde below U+0330 −200, on the model (X = C + Y tan θ + d − K; median distance from the precomposed glyphs 11 to 4 and 13 to 4; 2026-11-06). Both have since been moved onto the axis by the mark-axis rule.

#### Italic

Tilde below centred on its outline (8 units). Double acute (−55, 725), with X moved 17 units from the designer's regular offset and Y by the vertical move.

#### Semibold italic

- Hook above U+0309 −142, inverted breve U+0311 −223 and U+0314 −91, on the model (median distance from the precomposed glyphs 26 to 8, 19 to 3, 19 to 4; 2026-11-06).
- Tilde below centred on its outline (22 units off regular's offset).
- Koronis U+0343 (128, 532), from (−96, 605) (2026-11-11). The designer drew it as a horn-sized outline right of the origin with the comma above's anchor, so k was 371. It is now placed as regular's and italic's U+0313 (their U+0343 is the same glyph): the anchor 135 above the outline's bottom and 21 left of its ink centroid along the slant, with K = 150. The outline is left as it is (to-do list). After a base letter HarfBuzz replaces U+0343 by its canonical equivalent U+0313, so `uni0343` is shaped only on its own.
- Macron below raised 52 units to (−233, −58), 23 units below its outline as in the other styles (it sat 25 units under n, against 86 to 96 in the other styles; ṉ confirms; 2026-11-06).
- Curated grave and double acute that lacked K (landing 142 and 190 units left on every conforming base) were removed; the designer's anchors conform. They had been fitted on a, whose above anchor carried the slant. Stage 1 now deletes the above anchors of a, s, h and J and stage 6 gives them candidates.

### Rejected: moving every mark anchor to the model (2026-11-08)

A stage that moved every mark anchor onto the model, X = C + Y tan θ + d − K, was tested and rejected (`run_mark_snap_sheet.py`, `tex/input/mark_snap.tex`). Most moves were under 20 units, and as many marks got further from the precomposed glyphs as got closer. The mark-axis rule does not repeat it: it moves only symmetric marks, and only their X.

### Vertical moves from the precomposed glyphs (2026-11-09)

For each above mark, Δy is the median vertical offset of the composed mark (base + CGJ + mark) from the designer's precomposed glyphs, over the lowercase letters with an x-height base. Every such base has its above anchor at 645, and Δy is the same on every base to within a few units, so it belongs to the mark's anchor. Where |Δy| ≥ 10 the mark anchor is curated Δy higher, so that the mark sits Δy lower. In the italic styles its X moves with the slant, by Δy tan θ, so that the mark keeps its k.

- Regular: macron +18, dot above −45, double acute +11.
- Italic: dot above −11, double acute +11.
- Semibold: tilde +14, macron −12, dot above −21.
- Semibold italic: macron −32, dot above +11, ring +23, double acute +11.

The dot above in every style and the semibold italic ring were later superseded by the mark-zone consistency moves (2026-11-12).

### Mark-axis rule for symmetric marks (2026-11-09; below marks and threshold 0, 2026-11-12)

Stage 4 (`font_patching_markaxis.py`) puts the anchor X of a symmetric mark on its own axis, k = K, with k measured on the mark's ink. The rule does not touch Y.

- **Above marks (2026-11-09).** The mirror-symmetric ones (circumflex, tilde, macron, breve, dot above, dieresis, ring, caron, vertical line and double vertical line above, candrabindu, inverted breve, x above, vertical tilde, double overline, perispomeni, bridge above, not tilde, homothetic, almost equal to, fermata, zigzag) and the combining Latin letters U+0363–U+036F. Asymmetric marks keep their designed k: grave, acute and their tone-mark forms, double acute and double grave (a symmetric pair placed off centre), hook above, the comma-shaped marks, the half rings and the right arrowhead.
- **Threshold.** Until 2026-11-12 the rule moved only anchors with |k − K| ≥ 10. With that threshold it moved 37 mark anchors. Among the common marks: italic tilde (k 11, moved 11 units), semibold dieresis (12), semibold italic tilde (139, 11) and dieresis (112, 38). Among the others: the vertical tilde (about 18, in regular, italic and semibold), the perispomeni (18, in regular and italic) and most of semibold italic's combining letters (k 130 to 140). The semibold italic dieresis, which landed 26 units left of its precomposed glyphs where every other mark landed 5 to 16 right, now lands 12 right, like the others. What was left was under 10 (the ring: +2, +3, 0, +7; test sheet `tex/mark_threshold_test_sheet.pdf`). Since 2026-11-12 there is no threshold: every anchor whose X rounds to a different value is moved. Curated anchors of symmetric marks were moved onto the axis with the change (X only; regular macron, italic dot above, semibold tilde, macron, dot above and inverted breve, semibold italic macron, dot above, ring and inverted breve; 1 to 9 units).
- **Below marks (2026-11-12).** The mirror-symmetric below marks (`SYMMETRIC_BELOW`: plus and minus sign, dot, diaeresis and ring below, vertical line, bridge, inverted double arch, caron, circumflex, breve and inverted breve, tilde and macron below, double low line, inverted bridge, square, seagull, equals sign, double vertical line, left right arrow and upwards arrow below), with K = −12 in semibold italic, whose below marks are drawn with it as its base anchors are. The tacks keep their decided placement, and grave and acute below, the half rings, comma below and left angle below are asymmetric. It moves 19 or 20 anchors per style, most by 1 to 4 units. The largest are the inverted breve below in semibold and semibold italic (13, 12), the tilde below (8 in regular and semibold, 13 in semibold italic, whose curated anchor had left out K), the breve below in the italic styles (7), and the square and left right arrow below (5 to 7). Test sheet `tex/mark_below_axis_test_sheet.pdf`. The curated below anchors were moved with it (plus sign, ring, tilde, macron below, upwards arrow; 1 to 13 units).
- **Why not the precomposed glyphs.** Matching each mark to the precomposed glyphs (Δx = 0 per mark) would be the wrong target. Part of what a composed mark differs from the precomposed glyphs by is the base anchor's offset, common to every mark on that base. Fitting it into each mark would carry it to every base without a precomposed form (most IPA letters).

#### How the axis is measured

The axis is the centre of the ink bounds, with the slant removed, except for some combining letters (2026-11-12):

- Combining letters that are not boxy: their bounds and area centroid are more than about 4 units apart in regular (r 11, c 9, h 8, e 6, t 4). For those (e c h r t) the axis is the area centroid, which weights the stems over a thin arm, terminal or open side. For r it lies between the bounds and the stem (−7, −18, −28 relative to the old anchor in regular), as Gentium Plus, Noto Serif and Junicode place their combining r (75%, 40% and 30% of the way to the stem).
- Combining i U+0365 is measured on its stem (midline at the stem's top, carried at the slant), which its left top serif pulls the bounds 2.6 units off.
- Combining a, d, m, o, u, v, x are boxy enough for the bounds (bounds and centroid within 3).

**Bounds or symmetry axis (decided 2026-11-12: bounds).** A more precise axis would be the line about which the outline best matches its mirror image, or, for the tilde, zigzag and vertical tilde, the centre about which it best matches its rotation by 180°, since their terminals could push the bounds off centre. Measured on all 204 symmetric marks and symmetric `.cap` forms in the four patched fonts (outline de-slanted, scanned every half unit of height, overlap with its image maximized; test sheet `tex/mark_symmetry_axis_test_sheet.pdf`):

- The largest difference from the bounds centre is 2.2 units (semibold italic `breve.cap`), then 2.0 (semibold italic `breveinvertedcmb.cap`) and 1.6 (italic `breve.cap`). 188 of 204 are under 1 unit.
- The tilde-like marks (tilde, tilde below, perispomeni, vertical tilde, zigzag, almost equal to) match their 180° rotation about a centre within 1.3 units of the bounds centre. Their terminals do not push the bounds off centre.
- Not tilde U+034A and homothetic U+034B match neither symmetry exactly (about 10% of the ink uncovered by the image), since they combine a tilde with straight strokes. Their rotation centre is still within 1 unit.
- The italic and semibold italic dots (U+0307, U+0308) are skewed ovals. Their mirror mismatch is 13%, their rotation mismatch small, and both axes are on the bounds centre.

The anchors are integers, so the bounds centre is kept.

### Mark-zone consistency across styles (2026-11-12)

The base anchors have the same Y in every style. So a mark sits at the same place among its style's marks (its mark zone) in every style only if its gap from its anchor, relative to the median gap of the style's marks, is the same. For most marks it is, within 8 units. Test sheet `tex/mark_zone_consistency_sheet.pdf` shows the rest, each mark in its zone in the four styles, with the precomposed letters on every Latin and IPA base. Where the designer's precomposed letters are themselves inconsistent between styles, the composed marks were made consistent instead, with more clearance, and no longer match the tighter precomposed letters:

- Dot below U+0323 and diaeresis below U+0324: both at +28 in every style, the depth of the macron below and the minus sign below. The precomposed dots below are loose in regular (all 55 letters, 103 to 109 below the baseline on o) and tight in the other styles; ṳ, the only precomposed diaeresis below, is unusually tight in every style. Regular's dots go up 12 and 10; italic's, semibold's and semibold italic's down 22 to 34.
- Dot above U+0307: +30 in every style (it was +44 in regular, +13 to +20 in the others, following each style's precomposed letters): regular down 14, the others up 10 to 17. This replaces the vertical moves of 2026-11-09 for the dot above.
- Semibold diaeresis U+0308 up 9 (to +24, as in the other styles), and `dieresis.cap` with it.
- Semibold italic ring U+030A up 16 (to +3, as in the other styles); å is not evidence (a and A are discarded). This replaces its vertical move of 2026-11-09.
- Semibold breve below U+032E down 6 (to +1, as in the other styles).

The capital dot `dotaccent.cap` follows the lowercase dot's old pattern (regular +10, semibold −2, relative to the capital forms) and is not changed.

These moves made the styles agree; they did not make each style's zone denser. Measured on o (inner edge of every above and below mark, before and after): in regular the outlying dots came in, and the spread of the zones fell (sd 17.7 → 16.6 above, 16.8 → 15.4 below; range 465–547 → 465–533 above, −103 → −90 at the deepest below). In italic, semibold and semibold italic the dots, which sat near the middle of their zones, moved out to match regular's new positions, and the spread rose slightly (sd +0.5 to +1.3); the outer limits of the zones did not change.

### Open decisions

The report no longer lists open decisions or what the patch changes; they are kept here.

- **Stacked above marks (2026-11-18).** Found by the PDF scans (`run_pdf_combo_sheet.py`): italic ö̀ (proofreading-613, p. 297) and ä̀ (proofreading-633, p. 263) put the grave on the diaeresis, unanchored, in both the original and the patched fonts. Two paths need anchors. (1) HarfBuzz composes a + U+0308 into ä wherever the font has it, so a second mark on a precomposed letter is mark-to-base: the letter needs an above anchor at stacking height. Regular ä ö ü and italic ā have one (designer's); italic and semibold ä ö ü do not, and stage 9 inherits an above anchor only for letters without an above mark. (2) Where no precomposed letter exists (ŋ̈̀, ə̈́) or the text has CGJ, the first mark stays a glyph and the second needs mark-to-mark (`mkmk`), which is nearly absent: regular has two first marks (grave, breve) for 11 second marks, italic two for four, semibold only U+02C9 (for 6 second marks), semibold italic none; the patch does not touch `mkmk`.
  To decide: the stacking clearance, and whether it is per mark. A single stack anchor per first mark (its ink top + S) with the second marks' own anchors carries each mark's own offset over the first mark, as it does over x-height letters (o, patched, ink to ink: regular double acute 38, hook 53, breve 54, circumflex and caron 63, ring 66, grave 70, acute 72, tilde 77, macron 79, diaeresis 87, dot 94; semibold 25–91), so S only shifts them all. A per-mark stacked gap is possible: in `mkmk` the attaching mark has its own anchors (the lookup's Mark1Array, separate from mark-to-base), and for precomposed letters a separate mark-to-base lookup covering only the letters with an above mark could give the attaching marks the same stacked anchors, so both paths would agree. The designer's precomposed stacks do not settle it: regular lowercase gaps (ink to ink) are 18–69 (ǡ 18, ǻ 19, ǚ 21, ẫ 29, ṏ 31, ȭ 39, ǖ ǟ ȫ 42–43, ẵ 43, ḗ 47, ḕ 52, ṓ 58, ṍ ṻ 69), about half the same mark's gap over o (median ratio about 0.5), italic 2–67 (ṑ 2, ṓ 12), semibold 16–45; the acute and grave on the diaeresis (ǘ ǜ ḯ and capitals) dip between the dots in all four styles, in the Greek manner (ΐ), where Gentium Plus, Noto Serif, Junicode and Pagella stack them clear (+7 to +52 on ǘ); the Vietnamese ấ ầ ẩ put the second mark beside the circumflex, by design.

### Decided: left as they are

- **Italic and semibold italic, above marks on lowercase letters against the precomposed accents (2026-11-11).** Over the 107 lowercase precomposed letters with one above accent, the composed mark lands a median 7 units (italic) and 8 (semibold italic) right of the precomposed accent, relative to the letter. With pure candidates as base anchors the medians are +16 and +2 (regular and semibold, bbox midpoint: +9 and +6, so the designer puts accents a little left of centre in roman too). This is not K, which is in both the base and the mark anchors and cancels when a mark attaches. It is not the slant (as a slant error the two italic styles would point opposite ways, by under 1°), and not the lane (the ink lane gives +19 and +1, with wider extremes). The offset varies by letter more than by mark (italic s +35, w +25, g +23, z +23, r −29; semibold italic y +30, c +25, z +25, a +21, g −20). Checked by eye in the grids: the precomposed accents are unusually far left on italic s and w (above all ẇ and ẘ), whose bowls support the composed marks further right, and the precomposed glyphs of semibold italic differ from italic's. The composed marks are as well centred as the precomposed accents, or better; no anchor is changed.
- **Italic macron.** Its precomposed glyphs disagree (−1 on ā ē ḡ, −32 on ī ō ū ȳ), so it gets no vertical move. Across the styles the italic precomposed macrons are unusually loose (2026-11-12), but the combining macron sits where it should in its zone; nothing is changed.
- **The capital hook above `hookabovecomb.cap` (2026-11-12).** Semibold italic's sits about 32 units higher in its capital zone than the other styles', but the designer is not consistent about how tight the hook should be; left as it is.
- **Semibold double acute, diaeresis, hook above and circumflex**, which sit 10 to 19 units lower than in regular: they are within 10 units of their precomposed glyphs vertically, which do not support a move (semibold's x-height is also 5 units higher than regular's). (The diaeresis was later raised 9 by the mark-zone consistency moves.)
- **Semibold italic comma above U+0313 (k = 125) and double grave U+030F (k = 168):** the precomposed glyphs do not support a move.
- **Semibold italic tilde:** the mark-axis rule moves it from 12 to 23 units right of its precomposed glyphs, the rule's one cost.
- **Regular left half ring above U+0351:** it shares the right half ring's anchor and lands 16 units right of centre (Gentium Plus puts it about 11 left).
- **The axis of a symmetric mark is the centre of its bounds** (2026-11-12; see "Bounds or symmetry axis" above).

### Moved out of the report's open decisions

- **Semibold j (2026-11-12).** Its dot is 14 units left of its stem (regular −3), but the dot rules of the stem-axis rule apply only in the italic styles; ĵ and ǰ put the accent on the stem (+2). This is a flaw in the drawing of j and a question for the base anchors, not the mark anchors. It is now in `TODO.md`, under "Dots, in letters and marks" and "Check the curated anchors".
