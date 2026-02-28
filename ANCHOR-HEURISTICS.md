# Anchor Heuristics
*(first‑pass rules for predicting above‑ and below‑mark anchor positions)*

This document defines the first‑pass heuristic for computing **anchor_x** and **anchor_y** for glyphs that lack designer‑provided GPOS mark anchors. The heuristics rely on a small set of semantic tags whose sole purpose is to indicate **horizontal visual weight** and **slant/overhang behavior**. These tags do not describe glyph anatomy; they exist only to guide anchor placement.

The goal is to produce a stable, predictable fallback anchor that approximates designer intent for most glyphs. A later refinement pass may override or adjust these values.


## 1. Overview

Anchor placement has two independent components:

- **Horizontal placement (anchor_x)** — determined by the glyph’s horizontal visual balance: left‑heavy, right‑heavy, symmetric, overhanging, or slanted.
- **Vertical placement (anchor_y)** — determined by the glyph’s relationship to the font’s stable vertical aspects (baseline, x‑height, ascender height, etc.).

The first pass computes **x and y independently**, except for italic or strongly asymmetric glyphs where slant or overhang requires a correction.

---

## 2. Vertical aspects of the font

Libertinus has five stable vertical reference lines:

- Descender height  
- Baseline  
- x‑height  
- Ascender height  
- Capital height  

These define the “attachment zones” for above‑ and below‑mark anchors. Their numeric Y‑coordinates are listed in the design notes.

---

## 3. Heuristic for anchor_y

### 3.1 Basic rule

If a glyph aligns with a particular vertical aspect, its anchor_y is set to the **standard clearance** for that aspect.

Examples:

- Baseline glyphs → below‑anchor at Y = −110  
- Ascender glyphs → above‑anchor at ascender_height + ascender_clearance  
- x‑height glyphs → above‑anchor at xheight + xheight_clearance  

Each vertical aspect has a fixed clearance value derived from the font.

### 3.2 Choosing the correct vertical aspect

If a glyph does not fully reach an aspect (e.g., a short ascender), choose the **nearest** aspect to the glyph’s bounding box. This ensures:

- shallow ascenders behave like x‑height glyphs  
- shallow descenders behave like baseline glyphs  
- mid‑height IPA glyphs attach at the x‑height  

### 3.3 Special cases

Some glyphs have mixed vertical structure:

- **bdpqky** — counter‑dominant; attach according to the counter.  
- **fgjlt** — stem‑dominant; attach according to the major stem.  
- **Italic f** — treat as a descender glyph.

These reflect optical placement rather than geometry.

---

## 4. Heuristic for anchor_x

Horizontal anchor placement is driven by **semantic tags that encode horizontal visual weight**, not anatomical structure. The tags indicate whether the glyph’s mass is left‑heavy, right‑heavy, symmetric, overhanging, or slanted.

### 4.1 Basic formula

For most glyphs:

anchor_x = bbox_center + dx_norm * outline_width

Where:

- bbox_center = (xmin + xmax) / 2  
- outline_width = xmax − xmin  
- dx_norm is a normalized offset determined by semantic tags  

### 4.2 Semantic tags (first‑pass)

The tag set is intentionally minimal and behavior‑driven:

- **has_left_weight** — glyph’s left side carries more visual mass  
- **has_right_weight** — glyph’s right side carries more visual mass  
- **is_symmetric** — horizontal mass is balanced  
- **has_overhang_right** — rightmost outline exceeds advance width  

These tags are mutually compatible and may combine.

### 4.3 First‑pass dx_norm rules

These values are derived from measured dx_above_norm patterns in Libertinus.

- is_symmetric → dx_norm = 0  
- has_left_weight (only) → dx_norm = −0.08  
- has_right_weight (only) → dx_norm = +0.06  
- has_overhang_right → dx_norm += −0.20  
- is_italic_slanted → dx_norm += −0.03  

If both has_left_weight and has_right_weight are true (rare), treat as symmetric.

is_italic_slanted is per-font.  

### 4.4 Interaction between x and y

For most glyphs, x and y are independent.  
Exceptions:

- Italic glyphs — slant shifts the top center horizontally.  
- Overhang glyphs (f, j, y) — top and bottom centers differ.  
- Diagonal‑stress glyphs (v, w, y, IPA ʋ, ɯ, ɰ) — visual center depends on height.  

These may require a second‑pass correction.

---

## 5. Summary of first‑pass algorithm

### 5.1 Compute anchor_y

1. Determine which vertical aspect the glyph aligns with.  
2. Use the standard clearance for that aspect.  
3. Apply special rules for counter‑dominant or stem‑dominant glyphs.

### 5.2 Compute anchor_x

1. Compute bbox_center and outline_width.  
2. Determine dx_norm from semantic tags.  
3. Apply italic correction if needed.  
4. Compute anchor_x = bbox_center + dx_norm * outline_width.

This produces a stable, predictable fallback anchor.

---

## 6. Future refinements (not in first pass)

These refinements improve accuracy for complex glyphs:

- **diagonal_stress_direction** — shift anchor toward the open side of the diagonal.  
- **vertical_center_shift** — use different centers for above and below anchors.  
- **counter_center_x** — use counter centroid for bowl‑dominant glyphs.  
- **stem_center_x** — use stem center for stem‑dominant glyphs.  
- **overhang_amount** — scale dx_norm by magnitude of overhang.  

These can be added in a second‑pass heuristic.

---

## 7. Validation against designer anchors

To confirm that the heuristic matches designer intent:

1. Compute predicted anchor_x and anchor_y.  
2. Compare with actual anchors (if present).  
3. Compute absolute and normalized error.  
4. Identify outliers and refine tag weights or add second‑pass rules.

This ensures the heuristic remains faithful to the font’s design.
