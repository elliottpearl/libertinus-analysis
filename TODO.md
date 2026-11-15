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

Semibold italic designer anchors still far from the candidate (moved here from the report's "Semibold italic anchor model", 2026-11-14; `ANCHOR-MODEL-HISTORY.md`, "Semibold italic"):
- Above: the bowl capitals D, B, W, R, Q, 40 to 60 left of the candidate; A and X about 30 left, P 32 right; ȵ (−63), c (+39). Curate one by one.
- Below: Æ (+123), q (+115), r (−77, inherited by ɍ), j (−60), C and D (±55), d (−47), A (−41), t (−40), and Ƣ.
- Both italic styles: the above-anchor of f is still the candidate and the below-anchor of j the designer's; check by eye.

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

## Missing glyphs, phase 2: coverage as broad as Langscitinus, toward Gentium Plus

Survey of 2026-11-14. Coverage was counted per Unicode block with Unicode 14 data (Python's `unicodedata`), so characters added in Unicode 15 and 16 are not counted.

### Done (phase 1)

- **Drafts in the patch** (stage 2, `data/draft_glyphs/`, approved 2026-11-14):
  - italic (16): Ʌ Ɇ Ɉ Ɋ ɋ Ɍ Ɏ ɏ Ỻ ỻ Ɱ Ɐ ꝥ ꞓ ꭒ Ⅎ;
  - semibold (17): the same without Ɉ, plus ẜ ẝ;
  - semibold italic (18): the same plus Ɉ ẜ ẝ.
- **Revised designer glyphs** (stage 2): semibold ɭ; ʅ (all styles); italic ɍ; U+E27F ɿ with descender; U+034F CGJ.
  - The sheet also carries revisions that are not in the patch: regular ɋ and Ɋ (U+F630, U+F631), semibold Ɉ (U+F632), italic ẝ (U+F633).
- **Marks** (stage 3): about 45 in semibold, 63 in semibold italic, from U+0332–036F; semibold U+0358–0363 replaced.
- **Ʉ** (approved 2026-11-14): U with the style's own U+0336 across both stems, placed as in regular's Ʉ; the recipe reproduces regular's at 0.2% mismatch.
  - It is in `BASE_LATIN`, `BASE_CAP`, `@capitals` (all four styles) and `data/derived_letters.py` (from U, above and below).
  - It inherits U's anchors in every style. Regular's own Ʉ had no anchors before.
- **Phase 2 drafts of 2026-11-14.** None of these is in Langscitinus.
  - ꭤ (all four styles), approved: ɑ flipped top to bottom in de-slanted coordinates (`flipped()`). Gentium's ꭤ is its ɑ flipped (0.1% mismatch; rotated: 74%). In `BASE_LATIN`; stage 6 gives it the candidate (x-height).
  - ⱻ (all four styles), approved: `e.sc` turned (`turned()`). In `BASE_LATIN`; stage 6 gives it the candidate (small-capital height).
  - ˪ ˫ ˯–˸ (12, semibold and semibold italic), approved; ˹–˿ (7) pending. The lighter style's outline, pushed outward as stage 3 pushes the above marks it copies (`draft_modifier()`).
    - ˹–˿ wait for the decision below ("Slant of the geometric modifiers in the italics").
  - ꭤ in the semibold styles inherits the fat foot serif of the designer's ɑ (see "Fat serifs in semibold ɑ ɒ ʊ ʠ" below).
    - The designer's own semibold modifiers have 1.0–1.25 times the ink of the lighter style's; this gives about 1.12.
    - `copied()`, which pushes out by the stems' difference, gave 1.7–2.9 times, so it is not used.
- The sheet's "All drafts in context" now lists, under "revised:", the designer's glyphs revised because of problems found while drafting: regular ɋ Ɋ, italic ẝ, semibold Ɉ. These revisions are only in the draft fonts (PUA U+F630–F633), not in the patch.

### Coverage per block

| Block | assigned | patched R / I / SB / SBI | Langscitinus R | Gentium Plus R | Noto Serif R |
|---|---|---|---|---|---|
| Basic Latin, Latin-1, Latin Extended-A | 319 | full | full | 318 | full |
| Latin Extended-B | 208 | 208 / 206 / 205 / 206 | 208 | 208 | 208 |
| IPA Extensions | 96 | full | full | full | full |
| Spacing Modifier Letters | 80 | 75 / 75 / 56 / 56 | 75 | 80 | 80 |
| Combining Diacritical Marks | 112 | 112 / 112 / 110 / 110 | 111 | 108 | 112 |
| Latin Extended Additional | 256 | 256 / 252 / 251 / 251 | 256 | 256 | 256 |
| Latin Extended-C | 32 | 19 | 19 | 32 | 32 |
| Phonetic Extensions | 128 | 37 / 19 / 20 / 19 | 39 | 128 | 128 |
| Phonetic Extensions Supplement | 64 | 5 / 6 / 5 / 5 | 9 | 64 | 64 |
| Combining Diacritical Marks Supplement | 64 | 0 | 4 | 15 | 63 |
| Combining Diacritical Marks Extended | 31 | 0 | 0 | 11 | 26 |
| Modifier Tone Letters | 32 | 3 | 3 | 32 | 32 |
| Latin Extended-D | 193 | 8 | 9 | 160 | 193 |
| Latin Extended-E | 60 | 1 | 3 | 6 | 60 |
| Latin Extended-F | 57 | 0 | 0 | 8 | 57 |
| Latin Extended-G | 31 | 0 | 0 | 31 | 31 |

- Charis SIL covers the same as Gentium Plus in these blocks.
- Gentium Plus has about 420 characters in these blocks that patched regular lacks: a reasonable ceiling for a linguistics font.
- Noto Serif fills whole blocks for completeness.
- Within Latin Extended-D, Gentium has: Egyptological (A722–A72F) 14/14, medievalist (A732–A76F) 62/62, modifiers/insular/saltillo (A770–A78A) 27/27, African/phonetic (A78B–A7AF) 31/37, newer (A7B0–) 22/49.

### Langscitinus over Libertinus

Langscitinus is built on Libertinus 6.11; these fonts are 7.051. Before importing, check that outlines, weights and anchors match the 7.051 glyphs they sit beside. Wherever the patch lacks a character in the core blocks, Langscitinus lacks it too; it only adds the characters below.

- **Contour tone marks ᷄ ᷅ ᷆ ᷇ (U+1DC4–1DC7), all four styles, with mark anchors.**
  - Regular and italic look sound (zero advance, above the x-height): import.
  - Semibold and semibold italic are broken (advances 397 and 366; semibold ᷇ at y 623–801): own recipe instead, from the style's macron and acute or grave.
  - Add ᷈ ᷉ (U+1DC8–1DC9, in Gentium) by the same recipe.
- **Regular only:** ᴺ ᴿ ᶑ ᶣ ᶮ ᶾ ꝺ ꭖ ꭗ ⅄ (and ᶣ ꝺ in italic too).
  - Import into regular (and italic).
  - Use own recipes in the other styles: superscripts by the existing superscript recipe, ᶑ = ɗ + ɖ's tail, ⅄ = Y turned; ꝺ (insular d) and ꭖ ꭗ are medium.
- **ₘ ₙ in semibold:** the Langscitinus semibold glyphs sit at superscript height (y 365–697), a bug. Use own recipe in semibold and semibold italic, as the style's other subscripts.
- **Cyrillic Ӆ ӆ (regular, semibold):** outside the Latin scope. Import only if wanted.
- **◌ U+25CC:** already in Libertinus.

### The missing glyphs in the core blocks, sorted

These are Latin Extended-B, Spacing Modifier Letters, Combining Diacritical Marks, Latin Extended Additional, Latin Extended-C, Latin Extended-E and Latin Extended-G.

The kinds:
- **Easy:** built from the style's own glyphs (a component, mirror, turn, scale, or an existing bar, hook or overlay mark), as the phase-1 drafts.
- **Medium:** a part the style has, fitted with a new join or cut, or new GSUB.
- **Hard:** needs drawing.
- **Import:** from Langscitinus.
- **Leave out:** neither Gentium nor Langscitinus has it.

Styles in parentheses are those that lack the character; none means all four.

**Latin Extended-B**
- Ʉ (I SB SBI): easy, approved and in the patch.
- ɂ (I SB SBI): easy to medium. Regular's is not a scaled ʔ (433 wide and 439 high, against ʔ's 429 and 656), so ʔ's stem has to be shortened.
- ɀ (SB): easy. z + ȿ's swash tail (semibold has ȿ).

**Spacing Modifier Letters**
- ˥ ˦ ˧ ˨ ˩: the glyphs are easy (a staff and a bar). The contour ligatures are medium: GSUB that joins sequences of tone letters into one contour, as Gentium and Charis do. Not in Langscitinus.
- ˪ ˫ ˯–˿ (SB SBI, 19): easy; ˪ ˫ ˯–˸ approved and in the patch, ˹–˿ pending (slant). They exist in regular and italic, drawn one by one (only ˳ ˲ ˵ ˷ repeat another glyph's outline), so the draft copies the lighter style's and emboldens it.

**Combining Diacritical Marks**
- ̈́ (SB SBI): easy. The dialytika tonos of the style's ΐ ΰ (as `dotaccent.cap` comes from İ).
- ͅ (SB SBI): easy. The iota subscript of the style's ᾳ.

**Latin Extended Additional**
- ẟ (SB SBI): easy to medium. Regular's ẟ is not δ: it is wider at the top (479 against 456), and italic's likewise, so the top stroke has to be fitted.
- Ỽ ỽ (I SB SBI): medium. Regular's shape has no ready part in the other styles.
- Ỿ ỿ (I SB SBI): hard. A broad-nib pen loop; see the ỿ notes below.

**Latin Extended-C** (13; in Gentium, not in Langscitinus)
- Easy:
  - ⱻ: `e.sc` turned (approved, in the patch);
  - ⱺ: o + a small ring;
  - ⱹ: ɹ + ɽ's tail;
  - ⱼ: subscript j, as ᵢ;
  - ⱽ: superscript V, as the existing superscript capitals;
  - Ⱳ ⱳ: W w + the top hook of ƙ / Ⱪ;
  - Ɒ: Ɑ turned, once Ɑ exists.
- Medium:
  - Ɑ: a capital alpha, from O's bowl and a stem;
  - ⱱ: v + a right hook;
  - ⱸ: e with a notch cut in the bar;
  - Ȿ Ɀ: S Z + the swash tails of ȿ ɀ, fitted to capitals.

**Latin Extended-E** (60)
- In Gentium (6):
  - easy: ꬰ (ɑ + bar), ꭤ (ɑ flipped; approved, in the patch), ꭞ (superscript ɫ), ꭜ (superscript ɧ);
  - medium: ꭓ (Latin chi, from χ with serifs), ꭥ (Ω at small-cap size).
- In Langscitinus regular (2): ꭖ ꭗ, import into regular, medium elsewhere.
- Leave out the other 52: Teuthonista, Sakha and Americanist letters that neither Gentium nor Langscitinus has.

**Latin Extended-G** (31, extIPA additions of Unicode 14; all in Gentium, none in Langscitinus). Low priority, after Phonetic Extensions.
- Easy (mirrors and turns): 𝼁 reversed script g, 𝼂 small-cap turned G, 𝼃 reversed k, 𝼇 reversed eng, 𝼐 small-cap turned K (`k.sc`).
- Medium:
  - with a retroflex hook (ɖ ʂ ʐ have one): 𝼅 𝼈 𝼉 𝼊 𝼙 𝼚 𝼛 𝼜 𝼝;
  - with a curl, belt, double bar or fishhook: 𝼀 𝼄 𝼆 𝼋 𝼌 𝼍 𝼎 𝼏 𝼑 𝼞.
- Hard: the palatal-hook letters 𝼒 𝼓 𝼔 𝼕 𝼖 𝼗 𝼘. Libertinus has no palatal hook. Drawing it once also unlocks ᶀ–ᶎ in Phonetic Extensions Supplement.

Totals:
- Matching regular in every style: 24 glyphs in italic, 46 each in the semibolds. These include the subscript and superscript modifier letters ᴕ ᵅ ᵆ ᵌ ᵎ ᵔ ᵕ ᵙ ᵜ–ᵧ (Phonetic Extensions), which regular has and the others lack.
- In every style: Latin Extended-C (13), tone (5 + 6 marks), Latin Extended-E (8) and Latin Extended-G (31).

### Decision: slant of the geometric modifiers in the italics

Should the geometric spacing modifiers be upright in the italic styles?
- The tone corners ˹ ˺ ˻ ˼, the shelves ˽ ˾ and the arrow ˿ are at issue, and perhaps the other geometric ones: ˪ ˫ ˯–˲, and later the tone letters ˥–˩ and Modifier Tone Letters.
- Libertinus italic slants all its spacing modifiers (tan 11.5°), and the semibold italic drafts copy italic's, so they are slanted too.
- Gentium Plus italic keeps ˹ ˺ ˻ ˼ ˿ upright and slants ˽ ˾ (and ˥ ˪). Noto Serif italic keeps all upright. Junicode italic slants them.
- Upright in semibold italic would also mean revising italic's own: designer glyphs revised on the sheet, as ɋ Ɋ ẝ Ɉ are.

### Fat serifs in semibold ɑ ɒ ʊ ʠ

Found 2026-11-14, because ꭤ (ɑ flipped) looked wrong in the semibold styles. In both semibold styles these four IPA letters have flat slab serifs about 100 units thick. The style's Latin letters and the same letters in the lighter styles have serifs of 32–54.

| | a foot | u foot | ɑ foot | ɒ head | ʊ heads | ʠ head |
|---|---|---|---|---|---|---|
| regular | 38 | 39 | 37 | 36 | 44 | 33 |
| semibold | 39 | 46 | 102 | 103 | 98 | 104 |
| italic | 54 | 54 | 42 | 42 | 44 | 34 |
| semibold italic | – | 48 | 102 | 103 | 98–99 | 102 |

How this was checked:
- Every flat slab in every Latin and IPA base letter was measured: ink runs from the baseline, or down from the x-height, cap height or ascender, flat over at least 15 units.
- Each slab was compared with the same slab on the same glyph in the lighter style. The median ratio is 1.11 (semibold against regular) and 1.21 (semibold italic against italic).
- Flagged at 1.9× or more:
  - ɑ ɒ ʊ ʠ in both semibold styles (2.2–3.2×);
  - T Ŧ Ʈ Ⱦ (bar-end serifs), X (apex), S (terminal), f ɍ ɠ Ƃ (terminals), ƴ ʗ. These look like design (terminals and beaks), not serifs.
- The four agree in both semibold styles, so semibold italic's are probably semibold's slanted. This is a designer inconsistency, not provably a mistake. But nothing else in either semibold style has it, and Gentium Plus Bold's ɑ has an ordinary foot serif.
- Fix (suggested, deferred 2026-11-14): revise the four in both semibold styles, giving them the style's own serif (the foot of semibold a or u, the head of semibold u or q). Show them on the sheet as revisions of the designer's glyphs. Then redraft ꭤ from the revised ɑ.

### Later, beyond these blocks

- Phonetic Extensions and Supplement: about 150, mostly small capitals and superscript modifier letters. Needed for Uralic and phonetic notation.
- Modifier Tone Letters (29).
- Latin Extended-D: African/phonetic, saltillo and the modifiers, and the newer letters.
- Leave out: the medievalist (Junicode's field) and Egyptological letters, Combining Diacritical Marks Extended, and Latin Extended-F beyond Gentium's 8.

### ỿ (U+1EFF) and Ỿ, in italic, semibold and semibold italic

The loop should be drawn as a broad-nib pen stroke, as Noto Serif's and Junicode's are, while respecting the counter of regular's ỿ. Components, the method of the drafts, do not work for it.
- First attempts (2026-11-14, `pen_stroke.py`, `draft_y_pen` in `missing_glyphs.py`) show that no fixed nib angle fits. Libertinus's y descender is nearly a hairline (43 in regular, against o's 34 and 88), so a fixed nib draws either a nearly monoline loop or a heavy one.
- The pen has to turn along the stroke: steep where it leaves the descender, at o's stress round the bottom, and along the return stroke at the end.
- Open: that pen twist, and which part of regular's counter to keep (its teardrop shape, its size, or the loop's overall size).
