# Font Metrics JSON Schema  

For `fontmetrics_extractor.py` and `fontmetrics_loader.py`

This document describes the structure of the JSON files produced by the font‑metrics extractor, with a focus on the **semantic glyph‑shape tags** used to support heuristic anchor placement.

All fields are optional unless otherwise noted.

---

## Top‑level structure

Each JSON file contains two dictionaries:

```json
{
  "glyphs": {
    "0x0041": { ... },
    "0x0061": { ... }
  },

  "_orphans": {
    "uniE000": { ... }
  }
}
```

### `glyphs`
Glyphs that belong to the font’s Unicode repertoire.

### `_orphans`
Glyphs that exist in the font but do not map to a Unicode codepoint (e.g., private‑use glyphs, alternates). They are included for completeness but are not normally used for anchor heuristics.

---

## Per‑glyph record

Each glyph entry has the following structure:

```json
{
  "glyph": "A",
  "bbox": [xmin, ymin, xmax, ymax],
  "anchors": {
    "0": [x, y],
    "2": [x, y]
  },
  "width": 600,
  "lsb": 50,
  "rsb": 40,
  "tags": { ... }
}
```

### `glyph`
Human‑readable glyph name or character.

### `bbox`
The outline bounding box:  
`[xmin, ymin, xmax, ymax]`.

### `anchors`
GPOS mark anchors, keyed by anchor class ID.  
For Latin, class `"0"` is typically *above*, class `"2"` is *below*.

### `width`
Advance width.

### `lsb`, `rsb`
Left and right sidebearings.

### `tags`
Boolean semantic tags describing the glyph’s **horizontal structure**.  
These tags support heuristic anchor placement when designer‑provided anchors are missing.

---

## First‑pass semantic tags

These tags capture the major structural features that influence **horizontal anchor placement**. They are intentionally simple and boolean.

```json
"tags": {
  "has_left_stem": false,
  "has_right_stem": false,
  "has_left_bowl": false,
  "has_right_bowl": false,
  "has_overhang_right": false,
  "is_symmetric": false,
  "is_multi_bowl": false,
  "is_italic_slanted": false
}
```

### Tag definitions

- **has_left_stem**  
  True if the glyph contains a vertical stem of approximately the font’s stem width near the left side of the outline.

- **has_right_stem**  
  True if a vertical stem exists near the right side.

- **has_left_bowl**  
  True if a closed contour (bowl) has its centroid left of the outline’s horizontal midpoint.

- **has_right_bowl**  
  True if a bowl centroid lies right of the midpoint.

- **has_overhang_right**  
  True if the glyph extends beyond its advance width (e.g., negative `rsb`), or has a rightward overhang.

- **is_symmetric**  
  True if the glyph is horizontally symmetric or nearly so (e.g., O, o, H, I, U, V, W, X).

- **is_multi_bowl**  
  True for glyphs with two or more bowl‑like contours (e.g., æ, œ, ɶ).

- **is_italic_slanted**  
  True for italic or oblique styles where the slant shifts the visual center.

These tags are sufficient for a first‑pass heuristic that predicts `above_x` and `below_x` from the glyph’s geometry.

---

## Intended usage of tags

The tags allow the extractor or layout engine to compute a **predicted anchor x‑coordinate** when the font lacks designer‑provided anchors.

A typical heuristic uses:

- the outline’s horizontal center  
- the outline width  
- a tag‑dependent normalized offset (`dx_norm`)  

For example:

- symmetric glyph → `dx_norm = 0`  
- left‑stem glyph → `dx_norm ≈ –0.08`  
- right‑stem glyph → `dx_norm ≈ +0.06`  
- overhang glyph → `dx_norm ≈ –0.20`  
- italic slant → subtract a small correction  

Then:

```
anchor_x = bbox_center + dx_norm * outline_width
```

This approach matches designer anchors surprisingly well across styles.

---

## Future tags (not yet included)

These tags may be added later for more advanced heuristics:

- **has_diagonal_stress**  
  For v, w, y, IPA ʋ, ɯ, ɰ, italic forms.

- **has_vertical_center_shift**  
  For glyphs whose top and bottom centers differ (f, j, y).

- **stem_center_x**  
  Numeric: average x‑position of stems.

- **counter_center_x**  
  Numeric: centroid of the main counter.

- **overhang_amount**  
  Numeric: xmax − advance_width.

- **bowl_balance**  
  Numeric: (right_bowl_area − left_bowl_area) / total_area.

These refinements help with outliers and complex IPA shapes.

