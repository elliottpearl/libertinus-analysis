# Anchor Heuristics  
*(first‑pass rules for predicting above‑ and below‑mark anchor positions)*

This document describes the first‑pass heuristic rules used to compute **anchor_x** and **anchor_y** for glyphs that lack designer‑provided GPOS mark anchors. The heuristics rely on the semantic tags defined in `SCHEMA.md` and on stable vertical aspects of the Libertinus design. Later refinement passes may override or adjust these values.

The goal of these heuristics is not to replace designer judgment, but to provide a consistent, predictable fallback that matches the designer’s intent for most glyphs.

---

## 1. Overview

Anchor placement has two components:

- **Horizontal placement (x‑coordinate)** — determined by the glyph’s left/right mass distribution, stems, bowls, overhangs, and slant.
- **Vertical placement (y‑coordinate)** — determined by the glyph’s position relative to the font’s stable vertical aspects (baseline, x‑height, ascender height, etc.).

In the first pass, **x and y are computed independently**, except for italic or strongly asymmetric glyphs where slant or vertical structure requires a correction.

---

## 2. Vertical aspects of the font

Libertinus has at least five stable vertical reference lines:

- **Descender height**
- **Baseline**
- **x‑height**
- **Ascender height**
- **Capital height**

These appear as the gray horizontal lines in Figure 1 of the design notes. Their numeric Y‑coordinates are listed in Table 5 of the same document.

These vertical aspects define the “attachment zones” for above‑ and below‑mark anchors.

---

## 3. Heuristic for anchor_y

The vertical anchor position is determined by the glyph’s bounding box relative to the vertical aspects.

### 3.1 Basic rule

If a glyph sits on a particular vertical aspect, its anchor_y is set to the **standard clearance** for that aspect.

Examples:

- Glyphs that sit on the **baseline** → below‑anchor at **Y = −110**.
- Glyphs that reach the **ascender height** → above‑anchor at **ascender_height + ascender_clearance**.
- Glyphs that reach the **x‑height** → above‑anchor at **xheight + xheight_clearance**.

Each vertical aspect has a fixed clearance value.  
For example:

- Ascender above‑anchor clearance = `ascender_anchor_y − ascender_height = 885 − 698 = 187`.

### 3.2 Choosing the correct vertical aspect

If a glyph does not fully reach an aspect (e.g., a short ascender, a shallow descender), choose the **nearest** vertical aspect to the glyph’s bounding box.

This ensures that:

- small ascenders behave like x‑height glyphs,
- shallow descenders behave like baseline glyphs,
- mid‑height IPA glyphs attach at the x‑height.

### 3.3 Special cases

Some glyphs have mixed vertical structure:

- **bdpqky** — have both a stem and a counter.  
  The mark attaches according to the **counter**, not the stem.

- **fgjlt** — stem‑dominant glyphs.  
  The mark attaches according to the **major stem**, not the counter.

- **Italic f** — has a descender in Libertinus; treat it as a descender glyph.

These exceptions reflect optical placement rather than geometric rules.

---

## 4. Heuristic for anchor_x

Horizontal anchor placement is driven by the glyph’s **semantic tags** (see `SCHEMA.md`). The goal is to approximate the designer’s intended “visual center” of the attachment zone.

### 4.1 Basic formula

For most glyphs:

```
anchor_x = bbox_center + dx_norm * outline_width
```

Where:

- `bbox_center = (xmin + xmax) / 2`
- `outline_width = xmax − xmin`
- `dx_norm` is a normalized offset determined by semantic tags.

### 4.2 First‑pass dx_norm rules

These values are derived from measured dx_above_norm patterns in Libertinus.

- **is_symmetric** → `dx_norm = 0`
- **has_overhang_right** → `dx_norm = −0.20`
- **has_left_stem** → `dx_norm = −0.08`
- **has_right_stem** → `dx_norm = +0.06`
- **has_left_bowl** → `dx_norm = −0.05`
- **has_right_bowl** → `dx_norm = +0.04`
- **is_multi_bowl** → `dx_norm = 0`

### 4.3 Italic correction

Italic and semibold italic glyphs have a slanted visual center. Apply:

```
dx_norm -= 0.03
```

This shifts the anchor slightly left, matching designer practice.

### 4.4 When x and y interact

For most glyphs, x and y are independent.  
However, they interact in:

- **Italic glyphs** — slant shifts the top center horizontally.
- **Overhang glyphs** (f, j, y) — top and bottom centers differ.
- **Diagonal‑stress glyphs** (v, w, y, IPA ʋ, ɯ, ɰ) — visual center depends on height.

These cases may require a second‑pass correction (see Section 6).

---

## 5. Summary of first‑pass algorithm

### 5.1 Compute anchor_y

1. Determine which vertical aspect the glyph aligns with:
   - baseline, x‑height, ascender, descender, capital height.
2. Use the standard clearance for that aspect.
3. Apply special rules for:
   - counter‑dominant glyphs (bdpqky),
   - stem‑dominant glyphs (fgjlt),
   - italic f (descender).

### 5.2 Compute anchor_x

1. Compute `bbox_center` and `outline_width`.
2. Determine `dx_norm` from semantic tags.
3. Apply italic correction if needed.
4. Compute `anchor_x = bbox_center + dx_norm * outline_width`.

This produces a stable, predictable fallback anchor.

---

## 6. Future refinements (not in first pass)

These refinements improve accuracy for complex glyphs:

- **has_diagonal_stress**  
  Adjust anchor_x toward the open side of the diagonal.

- **has_vertical_center_shift**  
  Use different centers for above and below anchors:
  - `top_center_x` (sample outline near 80% height)
  - `bottom_center_x` (sample near 20% height)

- **counter_center_x**  
  Use counter centroid instead of bbox center for bowl‑dominant glyphs.

- **stem_center_x**  
  Use stem center for stem‑dominant glyphs.

- **overhang_amount**  
  Scale dx_norm by the magnitude of the overhang.

These refinements can be added in a second‑pass heuristic once the basic system is validated.

---

## 7. Validation against designer anchors

To confirm that the heuristic matches designer intent:

1. Compute predicted `anchor_x` and `anchor_y`.
2. Compare with actual anchors (if present).
3. Compute:
   - absolute error,
   - normalized error,
   - error distribution across glyph classes.
4. Identify outliers and refine tag weights or add second‑pass rules.

This process ensures that the heuristic remains faithful to the font’s design.
