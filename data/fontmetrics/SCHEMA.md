Here is the complete **SCHEMA.md** rewritten as a plain text file — **no backticks, no Markdown code fences**, so you can save it directly without triggering the Copilot crash.

---

# Font Metrics JSON Schema

For fontmetrics_extractor.py and fontmetrics_loader.py

This document describes the structure of the JSON files produced by the font‑metrics extractor, with a focus on the semantic glyph‑shape tags used to support heuristic anchor placement.

All fields are optional unless otherwise noted.

---------------------------------------------------------------------

## Top‑level structure

Each JSON file contains two dictionaries:

```
{
  "codepoint": {
    "0x0041": { ... },
    "0x0061": { ... }
  },

  "glyph": {
    "a.sc": { ... },
    "ae.sc": { ... }
  }
}
```

### codepoint
Glyphs that belong to the font’s Unicode repertoire.  
Keys are hexadecimal Unicode codepoints ("0x0061"), and values are per‑glyph metric records.

These glyphs represent encoded characters and are the primary inputs for anchor heuristics.

### glyph
Glyphs that exist in the font but do not map to a Unicode codepoint.  
These include:

• small‑cap base glyphs (e.g., a.sc, ae.sc, ij.sc)  
• unencoded alphabetic alternates (rare)  
• stylistic alternates, ligatures, and PUA glyphs (included for completeness)

Only a subset of these—specifically the small‑cap base glyphs—participate in anchor heuristics.  
All other unencoded glyphs are included for completeness but are not used when predicting anchor positions.

---------------------------------------------------------------------

## Per‑glyph record

Each glyph entry has the following structure:

```
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

### glyph
Human‑readable glyph name or character.  
For encoded glyphs, this is the Unicode character.  
For unencoded glyphs, this is the font’s glyph name (e.g., "a.sc").

### bbox
The outline bounding box: [xmin, ymin, xmax, ymax].

### anchors
GPOS mark anchors, keyed by anchor class ID.  
For Latin, class "0" is typically above, class "2" is below.

### width
Advance width.

### lsb, rsb
Left and right sidebearings.

### tags
Boolean semantic tags describing the glyph’s horizontal visual weight and slant/overhang behavior. These tags exist solely to support heuristic anchor placement when designer‑provided anchors are missing. They do not describe glyph anatomy; they encode only the directional cues needed to shift anchor_x left or right from the glyph’s horizontal center.

---------------------------------------------------------------------

### First‑pass semantic tags  
These tags capture the major horizontal‑balance features that influence anchor placement. They are intentionally simple and boolean.

```
"tags": {
  "has_left_weight": false,
  "has_right_weight": false,
  "is_symmetric": false,
  "has_overhang_right": false,  
}
```

**Tag definitions**

- **has_left_weight** — True if the glyph’s left side carries more horizontal visual mass than the right.  
  Examples: b, h, k, l, n, m, p, r; uppercase B, D, E, F, H, K, L, P, R.

- **has_right_weight** — True if the glyph’s right side carries more horizontal visual mass.  
  Examples: d, q, u; æ, œ (right bowl dominates); some italic forms.

- **is_symmetric** — True if the glyph’s horizontal mass is balanced around its center.  
  Examples: o, O, H, I, many small‑caps.

- **has_overhang_right** — True if the rightmost outline extends beyond the advance width.  
  Examples: f, j, y; many italic forms.

- **is_italic_slanted** — True if the glyph is italic or oblique enough that its visual center shifts left.

These tags are sufficient for a first‑pass heuristic that predicts `anchor_x` from the glyph’s horizontal balance.

---

### Intended usage of tags  
The tags allow the extractor or layout engine to compute a predicted anchor x‑coordinate when the font lacks designer‑provided anchors.

A typical heuristic uses:

- the outline’s horizontal center (`bbox_center`)  
- the outline width (`outline_width`)  
- a tag‑dependent normalized offset (`dx_norm`)

Examples of normalized offsets:

- symmetric glyph → `dx_norm = 0`  
- left‑heavy glyph → `dx_norm ≈ –0.08`  
- right‑heavy glyph → `dx_norm ≈ +0.06`  
- right‑overhang glyph → `dx_norm ≈ –0.20`  
- italic slant → subtract a small correction (≈ –0.03)

Then:

```
anchor_x = bbox_center + dx_norm * outline_width
```

This approach matches designer anchors well across styles and weights.

---

### Future tags (not yet included)  
These may be added later for more advanced heuristics:

- **has_diagonal_stress** — For v, w, y, IPA ʋ, ɯ, ɰ, and italic forms.  
- **has_vertical_center_shift** — For glyphs whose top and bottom centers differ (f, j, y).  
- **stem_center_x** — Numeric: average x‑position of stems.  
- **counter_center_x** — Numeric: centroid of the main counter.  
- **overhang_amount** — Numeric: xmax − advance_width.  
- **bowl_balance** — Numeric: (right_bowl_area − left_bowl_area) / total_area.

These refinements help with outliers and complex IPA shapes.


