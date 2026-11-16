# Capital alternates and capital anchors: detail and history

The report's "Capital alternates" section says briefly how the patch changes the capital forms of the above marks (`grave.cap`, `acute.cap`, …) and the above anchors of the capitals, and what the grids show. This file has the detail, moved out of the report on 2026-11-16. Code: `src/libertinus_analysis/font_patching_capmarks.py` (stage 4), `font_patching_addmarks.py` (stage 3), `font_patching_normalizeanchors.py` (stage 5); `data/fea/{style}/ccmp.fea` (stage 10).

## Which marks have a capital form

In the original fonts, `ccmp` substitutes only four capital alternates, for the grave, acute, circumflex and breve, although the designer also drew the caron, double acute, double grave, inverted breve, dieresis and hook above (and, in regular and semibold, the dot above).

The patched fonts substitute twelve, after every capital listed in `@capitals` of `data/fea/{style}/ccmp.fea` (stage 10): grave, acute, circumflex, tilde, breve, dot above, dieresis, hook above, double acute, caron, double grave and inverted breve.

Stage 3 adds the two forms that were missing:
- `dotaccent.cap` in italic and semibold italic: the dot of the precomposed İ U+0130;
- `tildecomb.cap` in every style (2026-11-08): the tilde of the precomposed tilded capitals (`tildecomb` itself, except in semibold italic, where the precomposed capitals use a taller tilde, that of Ã U+00C3).

The other above marks have no capital form and attach with their own anchors. The ring above U+030A has none by decision: the precomposed Å U+00C5 sets the ring on the apex, and the combining ring keeps its clearance; nor do the vertical lines above U+030D and U+033E.

`@capitals` lists A–Z, Æ, Œ, Ð, Ø, Đ, Ħ, Ł, the IPA and African capitals, the Greek and Cyrillic capitals, and the 59 precomposed capitals with a cedilla, ogonek, horn or below mark that stage 9 gives an above anchor (Ç Ą Ę Į Ų Ư Ḍ Ẹ Ọ …; added 2026-11-08, so that, e.g., Lithuanian Ą́ and Yoruba Ẹ́ take the capital acute like Á and É).

## Mark anchors of the capital alternates (stage 4)

The mark anchor of each capital alternate is set from the designer's precomposed capitals A–Z. The mark's outline is found in each precomposed glyph that is a capital plus that mark, which gives how far the designer moved it there.

- Y is the capital anchor reference (850) less the median height by which the mark is raised in the precomposed glyphs.
- X of a symmetric mark is the centre of its outline on its own axis, X = C + Y tan θ − K.
- X of the asymmetric grave, acute, double acute and double grave is the median position of the mark in the precomposed glyphs relative to the candidate above anchor of the capital, W/2 + 850 tan θ − K.
- K is 150 in semibold italic and 0 elsewhere.

The precomposed placement is reproduced exactly where a capital's above anchor is on its candidate; where it is not, the composed mark is displaced by the same amount. Human-curated anchors (stage 7) overrule stage 4.

### Composed against precomposed

Each composed capital (base, capital alternate, anchors) compared with the designer's precomposed glyph, over the capitals that have one. Vertically every capital alternate matches: the median difference is 0 in every style, and no single capital differs by more than 12, except Ỏ U+1ECE, whose precomposed hook above is 24 units higher than the composed one in all styles but semibold italic.

The numbers are the median horizontal distance; n is the number of precomposed capitals, and * marks a curated anchor.

| mark | n | regular | italic | semibold | semibold italic |
|---|---|---|---|---|---|
| grave | 8 | 17 | 30* | 4 | 10 |
| acute | 17 | 9 | 14* | 16 | 28 |
| circumflex | 12–13 | 4 | 9* | 14 | 16 |
| tilde | 7–8 | 5 | 10 | 10 | 25 |
| breve | 6 | 2 | 6* | 10 | 10 |
| dot above | 20 | 9 | 13 | 10 | 15 |
| dieresis | 7 | 2 | 6 | 8 | 8 |
| hook above | 6 | 4 | 12 | 12 | 16 |
| double acute | 2 | 0 | 2* | 18 | 6 |
| caron | 12–15 | 7 | 6* | 16 | 11 |
| double grave | 6 | 12 | 4* | 15 | 15 |
| inverted breve | 6 | 2 | 10* | 12 | 9 |

### Notes by style

- **Regular.** All scripted (2026-11-08). The curated grave (−175, 723) was removed in favour of stage 4's (−162, 724), as in semibold italic: the median distance from the precomposed graves goes from 18 to 17 units, and the median offset from 18 units right to 6, since the graves vary letter by letter. The other curated anchors are reproduced by the script and are commented out in `fontanchors_human`.
- **Italic.** Eight curated anchors (2026-11-07) overrule stage 4: grave −6 (stage 4: 17), acute −50 (−37), circumflex 15 (24), breve −14 (−1), caron −32 (−29), double acute −109 (−103), double grave −40 (−34), inverted breve −12 (−2). Each is fitted so that the accent lands, as a median over the capitals, where the designer drew it in the precomposed glyphs, with the capitals' actual above anchors (so the signed median is 0). The dieresis, dot above, hook above and tilde are scripted.
- **Semibold.** All scripted. The designer's capital above anchors were near 805, with the capital alternates drawn to compensate; stage 5 moves the capitals to 850, the reference stage 4 computes from.
- **Semibold italic.** All scripted (2026-11-08). The acute, grave, double acute and double grave had been curated on 2026-11-06 at the mark-axis position, X = C + Y tan θ + d − K with d from regular (−236, −194, −282, −214, against stage 4's −195, −168, −243, −167). Those reproduced the precomposed capitals only on the designer's capital anchors, which are left of the candidates (median k 173 against K = 150), because the designer drew the precomposed accents on those anchors. Stage 4 is preferred because the precomposed glyphs are used wherever they exist, so a composed capital without one should match them; and since H I J K L N O U V Y Æ were moved on 2026-11-07, it is also closer to them. The larger distances of the acute (28) and tilde (25) come from capitals whose above anchors are off their candidates (A, B, D, Q, R, W, X; V, Y and E for the tilde), not from the mark anchors.

### Notes by mark

- The grave, acute and their doubles are placed by eye, letter by letter, in the precomposed glyphs, so the implied X varies by up to 190 units over the bases (most for the acute, because of L), and one anchor is a compromise.
- Tilde. Unicode has no precomposed G̃, which Guarani writes, so G + U+0303 is composed. With the combining tilde it sat 25 to 47 units higher than the tilde of the precomposed Ñ U+00D1, Ã U+00C3, Õ U+00D5 beside it; `tildecomb.cap` matches their height exactly. Gentium Plus does the same with its `tildecomb.LP`.
- Dot above. `dotaccent.cap` is new in italic and semibold italic; in regular, stage 4 raises its anchor by 50 units to match the precomposed dotted capitals.
- Not used as evidence, because the mark outline differs in the precomposed glyph: Ÿ U+0178 and Ẅ U+1E84 (dieresis), Ľ U+013D (comma-style caron), Ũ U+0168 in semibold italic (tilde), and Ĵ U+0134 in semibold italic.

## Above and below anchors of A–Z

Who set each A–Z anchor in the patched fonts (from `data/anchor_provenance/{style}.json`, 2026-11-16): designer = the designer's anchor, unchanged; normalized = the designer's, with Y snapped to a reference in stage 5; heuristic = the stage 6 candidate (the designer had none, or it was deleted in stage 1); curated = stage 7; stem = the stem-axis rule (stage 7b).

| style | side | designer | normalized | heuristic | curated | stem |
|---|---|---|---|---|---|---|
| regular | above | B–H J–S U–Z | | | A | I T |
| | below | B–H K–P S U–Z | | J Q R | A | I T |
| italic | above | A B C E F G J K M N P Q R S W X Z | | | D H L O U V Y | I T |
| | below | C G K L M P V | A B D F H N R S U W X Y Z | J Q | E O | I T |
| semibold | above | | G J Q R V W X Y | A C D E F H I K M N P S U | B L O Z | T |
| | below | H | R S V W X Y Z | A–G I J K L M N O P Q U | | T |
| semibold italic | above | A–G M P Q R S W X Z | | H J K N O | L U V Y | I T |
| | below | A–H K L M N O P S U V W X Z | | J Q R | I Y | T |

Every capital's above anchor is at the capital reference, 850: stage 5 moves the semibold capitals (the designer's were near 805) and any capital in another style within 795–835 (Ŋ Ƅ Ƣ Ɋ Ћ Ỻ Ⱪ Ⱬ), and semibold's curated capitals are written at 850. The capitals beyond A–Z in the grids get their anchors the same ways, or inherit them: derived capitals (Ð Ø Đ Ħ Ł …) in stage 8 (`DERIVED-LETTERS.md`), precomposed capitals in stage 9.
