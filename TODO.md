I compared every curated anchor in `data/fontanchors_human/italic.py` and `semibold_italic.py` with the current model. Five are clearly wrong, about seven more are worth a second look, and the rest are either fine or deliberate exceptions. Bases were checked with `W/2 + Y tan θ − K` at the curated anchor's own height; marks against the mark candidate (`C + Y tan θ − K`, with Y from the outline plus the style's median offset). I haven't changed anything.

## Clearly wrong

| Style | Anchor | Curated | Model | What happened |
|---|---|---|---|---|
| semibold italic | grave U+0300, mark | (0, 683) | −156 | The comment says "was (−142, 683)". That original value fit the model; the curated one has no K, so the grave lands about 150 units right on every base. |
| semibold italic | double acute U+030B, mark | (−28, 719) | −163 | Comment: "x-mid of bbox". That's the upright midpoint, with no slant and no K, so it lands about 135 units right. |
| italic | U+E100 spacing base, above | (160, 645) | 297 | W/2 with no slant (the roman rule). Floating marks sit about 137 units left of where they sit on italic letters. Its own NBSP entry (262) is correct. |
| italic | U+E100 spacing base, below | (160, −110) | 137 | The same roman rule, 23 units right. |

The fifth is ʊ U+028A, in both styles. Its above-anchor is about 30 units too far left and its below-anchor about 30 too far right. That's what you get from roughly half the slant:
- italic: (358, 645) and (267, −110), against a model of 392 and 232;
- semibold italic: (219, 645) and (281, −110), against 248 and 257. The original font's below-anchor, (258, −114), already fits the model.

## Worth a second look
- **Semibold italic Ɛ U+0190, above (256, 850):** the model gives 293, so it's 37 left.
- **Semibold italic Ƶ U+01B5:**
  - Above (312, 850): I made this from 462 − 150. The model gives (332, 873), because Ƶ's top is about 23 units above the capline here.
  - Below (267, −110): this matches the old bbox-centre slide. The model gives 299.
- **Semibold italic Ş U+015E (232) and Ɵ U+019F (335):** copied from S and O. Those are the designer's anchors, but O is one of the capitals 40–60 units left of the model. If S and O are corrected later, these copies should follow.
- **K = −12 left out of below-anchors in semibold italic:** Y, Ɵ, Ʊ and Ʋ are 12 units off, and the tilde below U+0330 (−196, model −182) about 14. These are invisible in practice, but adding 12 would make them consistent.

## Probably deliberate (no action)
- **f below, both styles (30 and 62):** f overhangs its advance width, so a curated anchor is expected.
- **Ƴ below, both styles (+45):** under the stem, as the "italic lane of stem" comment on its above-anchor says.
- **Italic a below (251, +31):** placed under the bowl, per its comment.
- **Italic ū (396, 785):** copied from ō.
- **Italic `.cap` marks:** these fit the designer's off-midline capital anchors (`CLAUDE.md` already says so).
  - The X differences on `acute.cap` (−40) and `hungarumlaut.cap` (−55) are the usual offset of an asymmetric mark.
  - The higher Y on `hookabovecomb.cap` (+37) and `uni030F.cap` (+26) is the "y implied" from the precomposed capitals.
- **Italic double acute U+030B (−57, 714):** within the double acute's normal asymmetric offset.

Everything else matches the model within a few units: italic O, Y, Ģ, Ş, Ɵ, Ʊ, Ʋ, Ƶ, ɘ, ə and NBSP, and semibold italic's corrected above-anchors and NBSP.

Do you want me to fix the clearly wrong ones?
- Restore the original grave anchor (−142, 683).
- Set the double acute to (−168, 719), which is the model's −163 plus the −5 offset your comment intended.
- Set italic U+E100 to (297, 645) and (137, −110).
- For ʊ, either drop the curated anchors or use the model values.

The "second look" items need your judgement.
---

## Curated anchors kept for a decision (audit of 2026-10-29)

The audit built the patched fonts without stage 7 and compared every curated anchor with what the glyph gets without it. "Without" is that value: the designer's anchor, the stage 6 candidate, a stage 8 inheritance, or a stage 4 `.cap` mark anchor. Differences are curated minus without. 37 redundant curated anchors were commented out; 164 are the only source of their anchor and stay. These were kept for you to decide:

### Within 10 units, but deliberate

- **Ə below**, regular (316, −110) and semibold (343, −110): the candidate is 10 to the right (326, 353), off the centre of the bowl's bottom, which the curated values were measured to.
- **Y normalisations** of designer anchors. Removing them brings back the designer's value until stage 5 (normalise designer anchor Y) exists:
  - regular below: ɐ (229, −110) was −114; ɑ (222, −110) was (212, −114); ɒ (259, −110) was −114; ʊ (253, −110) was (258, −114)
  - italic below: O (310, −110) was −113; ʊ (267, −110) was (258, −114)
  - semibold above: O (363, 805), S (252, 805), Z (321, 805), each was 802 or 803; Z below (308, −110) was −107
- **X adjustments of 4–10 units** on designer anchors. They look deliberate; remove any that were only rounding:
  - regular below: c (227) designer 236; f (136) designer 132; m (404) designer 408; r (140) designer 135; É (287, −110) designer (279, −107)
  - regular superscripts above: ʳ (128) designer 119; ʷ (229) designer 219; ʸ (171) designer 168; ᵐ (248) designer 238; ᵖ (144) designer 148
  - italic: tilde below mark (−220, −70) designer −227

### 11–20 units from what the stages give

- regular: `grave.cap` (−175, 723) against stage 4 (−162, 724); d below (235, −110) against designer 221; œ below (408, −110) against candidate 388; Ə above (306, 850) against candidate 326 (the apex of the arc, measured); ɓ above (255, 885) against inherited 238; ɻ above (238, 645) against inherited 226
- italic: ʔ above (376, 867) against candidate (373, 850) (bowl overshoot of 10, decided); double acute mark (−57, 714) against designer −74 (the report's "Mark anchor model" section finds the designer's value has regular's offset, and lists removing the curated one under "Changes needed"); `uni030F.cap` (−47, 766) against stage 4 −34
- semibold: e above (249, 645) against candidate 232
- semibold italic: Y below (277, −110) against designer 295; tilde below mark (−196, −70) against designer −213
