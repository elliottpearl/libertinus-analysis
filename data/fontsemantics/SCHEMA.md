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


