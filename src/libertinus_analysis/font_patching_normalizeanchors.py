# font_patching_normalizeanchors.py
"""
Anchor-normalization stage of the Libertinus patching pipeline (stage 5).

Runs before the heuristic and curated anchor stages, so every above or below
base anchor it sees is the designer's. Bad anchors are already deleted (stage 1).

    Semibold capitals: the designer set their above-anchors near 805, 45 below
    the other styles, and compensated only in the .cap marks, so that a mark
    without a capital form crashed into the capital. Capitals (Unicode category
    Lu, and alternates such as R.alt) with an above-anchor in CAP_BAND move to
    the capital reference, 850. Stage 4 adds the same 45 to the .cap mark
    anchors, so those marks stay where they were.

    Every anchor: Y within SNAP_TOLERANCE of a reference for its class (above:
    ascender, capital, x-height; below: baseline, descender) snaps to it.

An anchor farther from every reference is not moved. Some are legitimate
(the clearance rule above a tall glyph, stacked marks on a precomposed glyph);
others should probably be flagged as bad. They are reported with the audit's
verdict, and the audit only covers encoded glyphs.
"""

import unicodedata

from .font_patching_deleteanchors import load_anchor_audit
from .font_patching_precomposed_anchors import find_mark_to_base_subtables
from .fontmetrics_helpers import ANCHOR_Y_REF_OPT

ABOVE = 0
BELOW = 2

REFERENCES = {ABOVE: ("asc", "cap", "xh"), BELOW: ("base", "desc")}

SNAP_TOLERANCE = 5

CAP_STYLES = {"semibold"}

# Designer heights of semibold capitals: 802-808, and 833 for Ɔ Ọ Ụ.
CAP_BAND = (800, 835)


def _is_capital(glyph_name, codepoints):
    codepoint = codepoints.get(glyph_name.split(".")[0])
    return codepoint is not None and unicodedata.category(chr(codepoint)) == "Lu"


def normalize_anchor_y(ttfont, font_key, lookup_index):
    """
    Move semibold's capitals to the capital reference, then snap the above and
    below anchors within SNAP_TOLERANCE of a reference.

    Returns: list of report lines.
    """
    subtables = find_mark_to_base_subtables(ttfont, lookup_index)
    if not subtables:
        return [f"No MarkToBase (LookupType 4) subtables found in lookup {lookup_index}; SKIPPED"]
    sub = subtables[0]

    refs = ANCHOR_Y_REF_OPT[font_key]
    codepoints = {glyph: cp for cp, glyph in ttfont.getBestCmap().items()}
    audit = load_anchor_audit(font_key)

    report = []
    capitals = snapped = far = 0
    for glyph_name, record in zip(sub.BaseCoverage.glyphs, sub.BaseArray.BaseRecord):
        for anchor_class, names in REFERENCES.items():
            anchor = record.BaseAnchor[anchor_class]
            if anchor is None:
                continue
            y = anchor.YCoordinate

            if (anchor_class == ABOVE and font_key in CAP_STYLES
                    and CAP_BAND[0] <= y <= CAP_BAND[1]
                    and _is_capital(glyph_name, codepoints)):
                anchor.YCoordinate = refs["cap"]
                report.append(f"{glyph_name}: capital above anchor y {y} -> {refs['cap']}")
                capitals += 1
                continue

            nearest = min((refs[name] for name in names), key=lambda ref: abs(ref - y))
            deviation = abs(nearest - y)
            if deviation == 0:
                continue
            if deviation <= SNAP_TOLERANCE:
                anchor.YCoordinate = nearest
                report.append(f"{glyph_name}: class {anchor_class} y {y} -> {nearest}")
                snapped += 1
            else:
                verdict = audit.get(glyph_name, {}).get(anchor_class, {}).get("verdict", "not flagged")
                if glyph_name not in codepoints:
                    verdict = "unencoded"
                report.append(f"FAR {glyph_name}: class {anchor_class} y {y}, "
                              f"{deviation} from {nearest}; audit: {verdict}")
                far += 1

    report.append(f"capital above anchors moved: {capitals}; anchors snapped: {snapped}; "
                  f"farther than {SNAP_TOLERANCE} from a reference: {far}")
    return report
