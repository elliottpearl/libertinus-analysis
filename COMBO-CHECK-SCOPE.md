# combo-check: scope

Scope of a standalone tool that finds base + combining mark combos and
precomposed letters that may print badly in a LangSci volume, ranks them by
badness, and tells a proofreader where to find each one in the PDF and in the
LaTeX source. It is written for the Claude Code session that will build the
tool, and for the people who review this scope.

Status: draft, 2026-11-23. Open questions are at the end.

## 1. Purpose and users

- **Users.** LangSci production staff and proofreaders. They run the tool on
  their own Linux server, read the report, and fix the source (or report a
  font problem). They have the volume PDF open in one window and the report
  in another.
- **Font focus.** Libertinus Serif in its four styles, as LangSci uses it
  (Langscitinus, a patch of Libertinus 6.11). Other fonts in the volume are
  checked by the generic tests only.
- **Unit of work.** One complete volume: one PDF of the whole book (in
  production it is one file), its LaTeX source tree, its `.log`, and its
  `.synctex.gz`.

### Non-goals

- Fixing the source, or patching or writing fonts.
- The anchor model, the candidate anchors and the patch pipeline of
  libertinus-analysis. The tool gets what it needs from that project as data
  (the reference pack, §6), never as code.
- Anchor classes other than above and below, except where §5 says so (the
  attached marks, the double diacritics).
- Optical judgement. The ink tests are geometric and compared with the font's
  own precomposed letters (§5.3). A human decides what is actually bad.
- Legacy 8-bit fonts (TIPA's `tipa8`–`tipa10`, other Type 1 fonts without a
  usable ToUnicode). The tool lists such fonts and their pages as not
  scanned, so that nobody takes silence for a clean result.

## 2. Environment

- Python 3.11 or later, on Linux. No FontForge.
- Python packages: PyMuPDF (PDF text trace, embedded fonts, annotations,
  crops), fontTools (fonts, GPOS, outlines), uharfbuzz (shaping),
  skia-pathops (outline geometry).
- Command-line tools: `synctex` (TeX Live) to map a PDF position to a source
  file and line.
- It must run without the libertinus-analysis repo, without the patched fonts,
  and without network access.

## 3. Inputs

| Input | Required | Use |
|---|---|---|
| Volume PDF | yes | what was printed: glyphs, positions, embedded fonts |
| Font folder | yes | the font files that set the volume (GPOS, GSUB, glyph names) |
| `.synctex.gz` | strongly preferred | PDF position → source file and line |
| LaTeX source tree | preferred | what was typed: NFC/NFD, macros, the `\accent` primitive |
| `.log` | preferred | "Missing character" lines, font loading |
| Reference pack (§6) | optional | the libertinus-analysis findings: deleted and patched anchors |

If SyncTeX is missing, the source locator falls back to a text search (§7.2).
LangSci builds with `latexmk` or a similar tool, so `-synctex=1` should cost
nothing to add; this should be checked with them (open question 1).

## 4. Pipeline

1. **Identify the fonts.** For each font embedded in the PDF, find the
   matching file in the font folder. Compare the outlines of several glyphs,
   using their glyph IDs.
   - Do not match on the PostScript name: Langscitinus 6.11 and Libertinus
     7.051 are both called `LibertinusSerif-Regular`, `-Italic`, `-Semibold`
     and `-SemiboldItalic`.
   - xdvipdfmx embeds OpenType CFF fonts as CID-keyed subsets with CID =
     GID. Check this, then use the GIDs to get the real glyph names
     (`dotlessi`, `acutecomb.cap`, `uni0307`).
   - Report a subset that matches no file, and give its glyphs the ink tests
     only.
2. **Extract.** For every page, read every glyph with PyMuPDF
   (`page.get_texttrace()`): GID, Unicode from ToUnicode, origin, size,
   font, and the transform. Do not trust ToUnicode for glyphs substituted
   by `ccmp` (`.cap` accents, dotless i); take their identity from the glyph
   name.
3. **Cluster.** A cluster is a base glyph followed by the marks that belong
   to it in reading order. A mark is a glyph with GDEF class 3 in the matched
   font, or Unicode category Mn or Me. A precomposed letter alone is also a
   cluster. Record for each occurrence the physical page, the printed folio,
   the line on the page, the word, the font and size of each member, and the
   printed positions.
4. **Deduplicate.** Group occurrences by (font, glyph sequence, the marks'
   printed offsets from the base rounded to 1 unit). A volume of 700 pages
   has tens of thousands of occurrences but a few hundred distinct combos.
   Run the per-combo tests (§5.1–5.3) once per group. Run the context tests
   (§5.4: neighbours, lines above and below) per occurrence, but only for
   groups that can collide, using a bbox test before the outline test.
5. **Test.** Run the tests of §5.
6. **Rank.** Rank by §6.
7. **Report.** Write the outputs of §7.

## 5. Tests

### 5.1 Attachment status, from the matched font's GPOS and GSUB

For each mark in a cluster, find what the font provides:

- **mark-to-base**: the base has an anchor of the mark's class in some
  MarkBase lookup of the `mark` feature. When several lookups give one, the
  last one applies; the patched fonts have a second MarkBase lookup for the
  dot above and below.
- **mark-to-mark**: the previous mark has an anchor of the mark's class in a
  MarkMark lookup of `mkmk`. Langscitinus Semibold and Semibold Italic have
  no `mkmk` feature at all, so every stacked mark there is unattached.
- **none**: the mark has zero advance (GDEF) and sits where its outline is
  drawn relative to the pen position after the base.

Do not hard-code anchor class indices or lookup indices. They differ per
font: the mark-to-base lookup index is 4, 4, 1, 2 in the four 7.051 fonts,
and 7.051 Semibold has a second above class (`top_punkt`). Tell above from
below by the mark's Unicode combining class (230 above, 220 below, 202 and
216 attached; 232/233/234 double) and, for marks without one, by the sign of
the mark anchor's Y.

Also cross-check the printed position against a HarfBuzz shaping of the
cluster in the matched font. A difference of more than 2 units means the
font was misidentified or the cluster was not shaped as one run (§5.2,
split cluster). Report it, do not hide it.

### 5.2 Text, decomposition and recomposition

From the PDF:

- **Missing glyph**: `.notdef` in the PDF, or a "Missing character" line in
  the log (the log gives the character and the font, the PDF does not).
- **Split cluster**: a mark in a different font, size or style from its base.
  XeTeX shapes each font run separately, so the mark never meets its base.
  This usually comes from a font switch inside a macro.
- **Orphan mark**: a mark after a space or at the start of a line, or on a
  base without anchors (digits, punctuation, U+0020). Floating marks belong
  on NBSP or U+25CC dotted circle. HarfBuzz does not insert a dotted circle
  for Latin, so nothing in the PDF warns of an orphan.
- **Inconsistent rendering**: one grapheme (the same NFC string) printed in
  two ways in the volume, for example as precomposed ǎ in one place and a +
  U+030C in another, or with different mark glyphs. HarfBuzz composes base +
  mark into the precomposed glyph when the font has it, unless something
  blocks it (CGJ, ZWJ, a font switch, a non-canonical order).

From the source (each finding joined to PDF occurrences by NFC string, not by
position):

- **Shaper decomposition**: a precomposed character the font lacks, so
  HarfBuzz decomposes it and the anchors decide its look. Informational.
- **Recomposition then stacking**: for example e + U+0323 + U+0302 + U+0301,
  which HarfBuzz sets as ệ + U+0301. The next mark then attaches to a
  precomposed letter that already has an above mark. Volumes 613 and 633 have
  this with italic ö + U+0300 and ä + U+0300: those letters have no above
  anchor, so the grave falls on the diaeresis. The ink test catches the
  collision; this test names its cause.
- **Non-canonical order**: the typed order differs from NFD order. This
  matters only for marks of the same combining class, whose order is kept
  and decides the stacking; otherwise it is informational.
- **Lookalikes and misuse**: spacing accents typed as if combining (U+00B4,
  U+00A8, U+00AF, U+02C6–U+02DD, `^`, `~`, `` ` `` next to a letter);
  deprecated combining characters (U+0340, U+0341, U+0343, U+0344 and the
  other singleton decompositions); a mark after a space inside a word (the
  volume 613 cases "pe ́" and "ŋwàʼnyə̀ ̀").
- **TeX accents**: `\'`, `\``, `\^`, `\d`, `\b`, `\=`, `\v`, `\u`, `\H`, `\c`,
  `\k`, `\r`, `\.`, `\~` and the tipa macros. Under fontspec these map to a
  precomposed character when one exists. Otherwise TeX places the accent with
  the `\accent` primitive, by box arithmetic, and GPOS plays no part. Find
  where the fallback happened, from the source and the PDF together.

### 5.3 Ink geometry, per distinct combo

Use outlines from the subsets embedded in the PDF, so that the shapes are
exactly what printed, placed at the printed positions. Measure in font units
(per 1000 em) so that the results do not depend on the point size. In the
italic styles, de-slant by the font's `post.italicAngle` (−12° in both
Libertinus and Langscitinus) before taking any horizontal measure.

**Measures:**

- **Collision.** The overlap area between mark ink and base ink, and between
  marks in a stack. If the inks do not overlap, the minimum distance between
  them.
- **Gap.** The vertical distance between mark ink and base ink within the
  mark's x-span (above marks: base top to mark bottom; below marks: mark top
  to base bottom).
- **Offset.** The horizontal distance between the centre of the mark's ink
  and the base's axis. The axis is the centre of the base's ink at the
  height where the mark meets it: the top band for above marks, the bottom
  band for below marks.

**References, from the same font's precomposed letters.** For each mark and
each kind of base (x-height, ascender or capital for above marks; baseline or
descender for below marks), take the median gap and offset over the font's
precomposed letters that decompose to base + that mark. To find the mark's
ink in a precomposed letter, remove the contours that match the base glyph's
contours after a translation. A combo is flagged when its gap or offset is
far from the reference (thresholds in a config file, starting at about
±40 units for the gap and ±30 for the offset), or when its marks collide. No
reference exists for a mark with no precomposed letters; for those, flag only
collisions and gaps above an absolute limit.

**Marks with their own rules:**

- **Attached marks** (ogonek, cedilla, horn U+031B, hooks U+0321 and U+0322,
  overlays U+0334–U+0338, the rhotic hook U+02DE): designed to touch or cross
  the base. They are not tested for collision; they are flagged if they do
  not touch.
- **Double diacritics** (U+035C–U+0362, the tie bars): span two bases. Test
  the centre of the mark against the midpoint of the two bases' ink, and for
  collision with both. Neither font anchors U+0361; it lands where its
  outline is drawn (volumes 613 and 614).
- **Joining marks** (U+0305 overline, U+0332 low line, U+0333): test that
  they join across letters, not that they are centred. Volume 613 has U+0305
  over the wrong letter.

**Precomposed letters on their own.** The base letter's ink should fit inside
the precomposed letter's, after a shift and a scale of up to 15%, for at
least 80% of the ink. Also flag an advance or bbox far from the base's. This
catches broken glyphs such as italic ɍ in Libertinus 7.051, which was drawn
over the outlines of Í and J́ (advance 601 against r's 357).

### 5.4 Ink geometry, per occurrence

- A mark against the ink of the neighbouring glyphs: a wide mark on f, i, l,
  ı, or an italic overhang.
- A mark against the lines above and below: tall stacks against descenders,
  below marks against ascenders and capital accents.

## 6. Badness

Rank by **tier**, then by **severity** within the tier. Count occurrences
separately: the count decides the order of work, not the badness.

| Tier | Meaning |
|---|---|
| 0 | missing glyph, orphan mark, split cluster |
| 1 | unattached: no mark-to-base anchor, or a stacked mark with no mark-to-mark anchor |
| 2 | attached, but the reference pack says the anchor is wrong (below) |
| 3 | attached, but an ink test fails |
| 4 | attached and clean (listed only on request) |

- **Severity**, in font units: the overlap or minimum distance, then the
  distance of the gap and offset from their references, then the patch
  displacement (below).
- An ink failure raises tier 2 to show both reasons. An unattached combo
  whose ink passes stays in tier 1 but is marked "ink OK", so that a reviewer
  can pass over it quickly.
- Source findings with no visible effect (shaper decomposition, a harmless
  non-canonical order) are listed apart from the ranking.

### 6.1 Reference pack

A JSON file exported from libertinus-analysis by a script in that repo
(`run_export_reference_pack.py`, to be written). It changes as the patch
changes, so it carries its own version.

- **Header**: export date, libertinus-analysis commit, Libertinus release
  of the original fonts (7.051), the SHA-256 of each original and patched
  font file.
- **Per style, per glyph** (name and code point), per anchor class
  identified by role (above, below, attached; not by index), per lookup
  (main, dot):
  - the original 7.051 base anchor,
  - the patched base anchor and its owner (designer, normalized, heuristic,
    curated, stem, derived, precomposed; from `data/anchor_provenance/`),
  - `deleted: true` and the reason, if `data/fontanchors_audit/overrides.py`
    marks it `"delete"`.
- **Per style, per mark**: the original and patched mark anchors, and the
  `.cap` form used after capitals.
- **Glyphs the patch adds** (marks a style lacks, the draft letters), listed
  so the tool can say "the patch adds this glyph".

The tool uses it like this:

- **Patch displacement.** For a mark attached to a base: (patched base anchor
  − patched mark anchor) − (anchor in the font in use − its mark anchor), in
  units. It compares the font in use with the patched target directly, so it
  holds for Langscitinus too, where LangSci changed anchors after 6.11. A
  combo is tier 2 if the displacement is at least 10 units (the
  `MIN_MOVE` of libertinus-analysis's `run_pdf_combo_sheet.py`).
- **Deleted anchor.** The font in use has exactly the original 7.051
  coordinates of a deleted anchor. Match on the coordinates as well as the
  glyph name, so that a deletion never applies to an anchor LangSci has
  already changed.
- **Unattached now, attached by the patch.** The font has no anchor but the
  pack has one: say so, with the patched displacement from where the mark
  printed.
- Without a pack, tier 2 is empty and everything else works.

## 7. Outputs

### 7.1 Files

- `report.json`: everything, one record per distinct combo with its
  occurrences. The other outputs are views of it.
- `report.html`: the ranked list for people. One row per distinct combo with:
  tier, severity, the reasons in words, count, a crop of the first
  occurrence (from the PDF, at about 8× zoom, base and mark outlines
  outlined), and its locations (§7.2). The full list of occurrences folds
  out.
- `volume-annotated.pdf`: a copy of the volume with a highlight annotation
  on every flagged occurrence. The note says the tier, the reason and the
  finding's ID in the report. A viewer's annotation panel then lists the
  findings in page order.

### 7.2 Locations

Each occurrence carries:

- **Physical page** (what "go to page" takes when the PDF has no page
  labels) and **printed folio** (what is printed on the page, and what
  hyperref's page labels show in most viewers). Read the folio from the
  page's own text, not the page labels, which may be absent or wrong.
- **Line on the page**, counted from the top of the text block, and the
  **word as printed**.
- **Search text**: the plain words around the combo, without combining
  marks, because viewers search for combining marks unreliably (some match
  the base letter alone, some nothing).
- **Source**: `file:line` from `synctex edit` at the cluster's position.
  Without SyncTeX, the source files and lines where the word's NFC or NFD
  form appears, marked as a text match.
- A link `volume-annotated.pdf#page=N` in the HTML report.

## 8. Acceptance tests

The proofreading PDFs in libertinus-analysis's `data/legacy-fontdata/`
(volumes 530, 540, 613, 614, 633) and the findings in its
`data/pdf_combo_notes.py`. Volume 614 is split into two PDFs; join them for
the test, or test the parts one at a time. The tool must find, without being
told about them:

- U+0361 tie bar unattached (613, 614: t͡ʃ, t͡s, d͡ʒ, k͡p);
- U+0305 over the wrong letter (613, p. 285);
- italic ö + U+0300 and ä + U+0300 (613 p. 289, 633 p. 255), with the
  grave colliding with the diaeresis;
- marks after a space (613 p. 85, p. 87; 614 p. 1:93);
- the stray U+0306 after an asterisk (614 p. 1:143);
- the TIPA fonts of 613 listed as not scanned;
- the semibold positions that differ from 7.051 (613, 633), as a sign that
  the fonts in use are not 7.051. The tool should identify the volume's
  fonts correctly (Langscitinus or Libertinus, by outline) and show no shaping
  mismatch.

Test the fonts themselves with italic ɍ in Libertinus 7.051 (§5.3).

## 9. Milestones

1. Font identification, extraction, clusters, locations (§4.1–4.3, §7.2),
   with a plain list of every distinct combo and its occurrences. Usable on
   its own as an inventory.
2. Attachment status and the text tests from the PDF (§5.1, §5.2 first part),
   tiers 0 and 1, the HTML report and the annotated PDF.
3. The reference pack: the exporter in libertinus-analysis, then tier 2.
4. Ink tests (§5.3, §5.4) and tier 3.
5. Source tests (§5.2 second part).

## 10. Open questions

1. Does LangSci compile with `-synctex=1`, and can the tool run where the
   `.synctex.gz` and the source are, or only where the PDF is?
2. Where does the tool live, in a LangSci repo or its own, and who maintains
   it? Where is the reference pack published, and how does the tool get the
   latest one?
3. Does LangSci want a command-line tool only, or a CI step that fails a
   build above some tier?
4. The ink thresholds (§5.3) are first guesses. They should be tuned on the
   acceptance volumes before LangSci sees any report.
5. Is the fonts' licence (OFL) enough for LangSci to receive the patched
   fonts as well? If so, the tool could shape with them directly instead of
   using the reference pack's anchors, which is more exact (it would also
   see `ccmp` and the added glyphs).
