# Font semantics

## Purpose

The semantic data stored in this directory describe how combining marks should be horizontally aligned relative to each base glyph in a given font style. These values are not derived from geometry or from the font’s SplineSets. Instead, they reflect typographic knowledge about the canonical shape of each Unicode character in a humanist serif style (e.g., Libertinus).

This semantic classification is intended to be determined once, by a designer or by an LLM, and then stored permanently. It is separate from the numeric metrics extracted by `fontmetric_extractor.py`, which are algorithmic and repeatable.

## General usage

For each glyph, the horizontal position of an above‑mark or below‑mark is usually determined by centering the mark over a meaningful structural midpoint of the glyph. Different glyphs use different midpoints depending on their shape. Some glyphs use different midpoints for above‑marks and below‑marks
The semantic midpoint type is therefore stored per anchor (above and below), and per-glyph.

## Midpoint types

Combining marks placed above or below a base glyph must be horizontally aligned to a meaningful structural center of that glyph. The semantic midpoint type describes which structural feature of the glyph should be used as the reference for mark placement. These midpoint types are independent of the numeric midpoint values, which are computed later by the metric extractor.

The midpoint types are:

### bbox

The horizontal midpoint of the glyph’s bounding box.
Use this when the glyph has no clear structural center, or when its shape is too irregular, too symmetric, or too ambiguous for stem, bowl, or vertex midpoints to apply.
Examples: X, x, Z, z, many fricative IPA letters such as ʃ or ʂ.

### stem

The horizontal midpoint of one or two dominant vertical stems, or of a central vertical band.
Use this when the glyph’s primary structure is defined by vertical strokes.
Examples: h, n, m, l, i, t, b, d, p, q.
For ligatures such as æ or œ, the central joining band may function as a stem.

### bowl

The horizontal midpoint of the left and right extrema of a bowl shape.
Use this when the glyph’s top or bottom outline is dominated by a curved bowl.
Examples: o, c, e, a, upper bowl of g, many IPA vowels such as ə or ɜ.
A glyph may have a top bowl and a bottom bowl; the midpoint may differ for above and below anchors.

### vertex

The x‑coordinate of a top or bottom apex in a vertex‑shaped glyph.
Use this when the glyph has a pointed top or bottom that defines its visual center.
Examples: v, w, y, small‑capital V‑like IPA letters.

### none
No meaningful semantic midpoint exists.
Use this only when the glyph shape provides no stable structural feature for mark alignment, and bbox is not appropriate.
This category should be rare.

These categories are independent of the actual numeric midpoint values, 
which are computed later by some algorithm looking at the SplineSet.



## Per‑anchor semantics

Each glyph has two independent semantic midpoint classifications:
- midpoint_anchor_above
- midpoint_anchor_below

A glyph may use different midpoint types for above and below marks.
Examples:
- a: above uses bowl; below uses stem
- g (two‑storey): above uses upper bowl; below uses lower bowl
- v: above uses vertex; below uses stem or bbox depending on style
- ʃ: above uses bowl; below often uses bbox

These decisions depend on the canonical shape of the Unicode character in a humanist serif style, not on the specific SplineSet of a particular font.

## AGENT prompt

This `SCHEMA` is designed so that any LLM agent can produce the 
semantic midpoint classifications for a given set of base glyphs. 
The agent must determine, for each codepoint, 
which midpoint type is appropriate for the above anchor 
and which is appropriate for the below anchor, 
using the definitions above.
The agent should assume a regular (upright), humanist serif font in the style of Libertinus. 
The agent should base its decisions on the canonical shape of each Unicode character, 
not on any specific font file.
If a decision is ambiguous or requires justification, the agent may include an optional rationale field:
"rationale_anchor_above": short explanation
"rationale_anchor_below": short explanation
Rationales should be concise and only included when necessary.
The agent must output a JSON object with entries as specified below.

Initially, this semantic data should be produced for `BASE_HEURISTICS` from `data/ipa/ipa_unicode.py`.
This is a subset of 106 Unicode characters, indexed by hex codepoints, including A-Z, a-z, and some IPA vowels and consonants. 

## JSON format

Semantic data are stored in JSON files named 'data/fontsematics/{font_key}.py` where 
`font_key` is `regular`, `italic`, `semibold`, `semibold_italic`.

At present, only `regular` and `italic` are expected to differ in mark-position semantics.

Each file contains a JSON object with the following structure.


```
{
  "codepoint": {
    "0x0041": { 
      "semantics": {
        "midpoint_anchor_above": "...",
        "midpoint_anchor_below": "...",
        "rationale_anchor_above": "free text",
        "rationale_anchor_below": "free text",
      }      
    },
  },
}

```
where "..." is the midpoint type key "bbox", "stem", "bowl", "vertex", or "none"
"rationale_anchor_above" or "rationale_anchor_below" could be empty, 
or short free-text explanations when appropriate
for exceptions.

The "codepoint" key appears unnecessary, 
but this format is consistent with the JSON format for fontmetrics data.

## Algorithmic usage

Separate algorithms will calculate the X coordinate of the midpoint and anchor type, 
given the SplineSet of the glyph. 
These X coordinate values can be compared to existing anchor coordinates, 
or used as candidates for anchors not yet set.



# new classification

A revised SCHEMA needs to reflect the core insight you’ve developed: **every mark‑centering decision begins with identifying whether the glyph uses a *vertical aspect* or *horizontal aspects* as the centering reference**, and then specifying the *type* of those aspects. The schema below rewrites your section so it expresses this logic cleanly, explicitly, and in a way that an extractor can implement deterministically.

---

## Semantic midpoint schema (revised)

### Purpose  
Each glyph may require a different structural reference for horizontally centering above‑marks and below‑marks. The semantic midpoint classification identifies **which structural aspect of the outline** determines the horizontal alignment of a combining mark. This classification is stored **per anchor** (above and below) and **per glyph**.

The system distinguishes two fundamentally different centering modes:

- **Vertical‑aspect centering** — the mark is centered over a *single* vertical alignment axis defined by a structural feature.
- **Horizontal‑aspect centering** — the mark is centered between *two* horizontal features (left and right), and the midpoint between them defines the alignment axis.

Both modes are structural, not geometric: they describe the designer’s intended alignment reference, not the literal stroke direction.

---

## Midpoint classification

Each anchor (above and below) must specify:

```
mode: "vertical" | "horizontal"
```

### If `mode: "vertical"`  
The mark is centered over a **single vertical aspect** of the glyph.  
Specify:

```
aspect: <vertical-aspect-type>
```

#### Vertical aspect types  
A vertical aspect is any feature that defines a **single vertical alignment axis** for centering. These are identified by distinctive Y‑structure in the outline, even if the strokes forming them are diagonal or curved.

- **stem** — centerline of a dominant vertical stroke.  
  Examples: i, l, h, n, m.

- **bowl** — vertical axis of a bowl or loop.  
  Examples: o, e, a, upper bowl of g, ə.

- **vertex** — vertical axis through a pointed apex or V‑shape.  
  Examples: v, w, y, x (top or bottom apex).

- **loop** — vertical axis of a looped structure.  
  Examples: lower loop of g, top loop of ʃ.

- **bbox** — vertical axis of the bounding box (fallback when no structural feature applies).  
  Examples: highly irregular glyphs, some fricatives.

---

### If `mode: "horizontal"`  
The mark is centered between **two horizontal aspects**: a left feature and a right feature.  
Specify:

```
left:  <horizontal-aspect-type>
right: <horizontal-aspect-type>
```

#### Horizontal aspect types  
A horizontal aspect is any feature that defines a **left or right boundary** whose midpoint with another boundary determines the alignment axis.

- **stem** — left or right boundary of a true vertical stem.  
  Examples: b, d, p, q.

- **pseudostem** — vertical bowl wall or loop wall acting as a stem‑like boundary.  
  Examples: b (right bowl wall), d (left bowl wall), ɮ (upper right wall).

- **crossbar_end** — left or right endpoint of a crossbar.  
  Examples: t (right crossbar end).

- **bowl** — left or right bowl boundary used as a horizontal aspect.  
  Rare but needed for asymmetric glyphs.  
  Example: ɮ below (right bowl boundary).

- **bbox** — left or right bounding‑box edge (fallback when no structural boundary applies).

---

## Notes on usage

- Above and below anchors may use **different modes** and **different aspect types** for the same glyph.  
  Example: ɮ uses horizontal centering above (stem + pseudostem) and horizontal centering below (stem + bowl).

- Vertical aspects are defined by **Y‑structure**, but their **X‑coordinate** is the centering axis.  
  This applies even in italic fonts, where strokes lean but alignment axes remain vertical.

- Horizontal aspects are defined by **left/right boundaries**, not literal horizontality.  
  They remain valid under slant, contrast, and stylistic variation.

- The extractor computes numeric midpoints from these semantic tags; the schema only encodes structural intent.

---

If you want to continue refining this, the next step is to add a compact table of canonical classifications for the Latin + IPA base set so the schema can be validated against real glyphs.


# More notes

The stem-midpoint $sm$ is the midpoint between two dominant vertical stems 
(useful for letterforms like h, n, u, b, d, p, q), 
or the midpoint of one dominant stem (useful for e.g. i, j, l), 
or one dominant central band (useful for ligatures like œ).
When the stem-midpoint is dominant, it is relevant for both the above-anchor and the below-anchor.
Define the anchor offsets $as\delta = ax - sm$ and $bs\delta = bx - sm$.

The bowl-midpoint ($acm$ and $bcm$) is the midpoint of the $X$ coordinate 
of the inner and outer extrema of a bowl, 
useful for bowl-dominated glyphs (e.g. c, o, e, a). 
(The letter $c$ in in the bowl-midpoint $cxm$ recalls its appropriateness for the c letterform.)
Note that these are calculated for the top bowl ($acm$) and bottom bowl ($bcm$) separately, when appropriate.
Define the anchor offsets $ac\delta = ax - acm$ and $bc\delta = bx - bcm$.

The vertex-midpoint ($avm$ and $bvm$) is the $X$ coordinate at the apex (top or bottom) 
of a vertex-shaped glyph (e.g. v, w, y).
Again, $avm$ and $bvm$ are determined separately, when appropriate.
Define the anchor offsets $av\delta = ax - avm$ and $bv\delta = bx - bvm$.

The normalized anchor offsets are defined by dividing the anchor offset by the bounding box witdh.

For each glyph, there is one kind of midpoint (stem, bowl, or vertex) 
that is most relevant to determining the above-anchor and below-anchor.
Any human (or LLM) can determine these midpoint values by examining the control points 
of the splineset of the glyph, when that mipoint is relevant for that glyph.
I hope to be able to produce an algorithm that can calculate each kind of midpoint.
Otherwise, I may have to ask an LLM to determine these relevant midpoint values per glyph, 
as anchor $X$ coordinates.
Note that a human (or LLM) can decide, per glyph, which midpoint (stem, bowl, apex) 
is relevant to which anchor  (above, below) regardless of the exact glyph splineset, 
but simply by knowing the glyph and font style (regular or italic).

When a glyph has significant asymmetry, the designer may intentionally 
offset the anchor from the semantic midpoint to avoid collisions (ascender/descender) 
or for optical balance; the table rows with $\delta$ and $\%$ quantify that offset.
