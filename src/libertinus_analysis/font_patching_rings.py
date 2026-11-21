# font_patching_rings.py
"""
Heavier rings in the semibold styles (stage 2 of the Libertinus patching
pipeline, 2026-11-21).

The designer's semibold rings are no heavier than the light styles' (stroke
at the sides / top and bottom, de-slanted: regular 40/32, semibold 36/32 and
U+0325 32/27; italic 37/27, semibold italic 36/31), where other fonts' bold
rings are 13-60% heavier than their regular. Every ring of semibold and
semibold italic (U+030A, U+0325, U+02DA, å Å ů Ů ǻ Ǻ ḁ Ḁ ẘ ẙ and the small
caps) is redrawn by ring_drafts.redraw_rings: two Bezier ellipses at the
designer's centre and outer size, the inner inset by RING_FACTOR x the light
style's stroke; in Å Ǻ, where the ring is merged with the apex, only the
counter. The outer size is kept, so the mark anchors need no change.

The factors (2026-11-21) follow how much heavier the designer's own above
marks with a stroke are (grave, acute, circumflex, tilde, macron, breve,
double acute, caron; ink area, heavy over light style): median about 1.19 in
semibold, 1.14 in semibold italic. Semibold 1.25 gives the rings 1.16 times
regular's ink, semibold italic 1.20 gives them 1.15 times italic's
(ANCHOR-MODEL-HISTORY.md, "Heavier rings").

Runs before stage 3, so that a mark copied there with a ring in it would take
the style's new ring.
"""

from .ring_drafts import redraw_rings

RING_FACTOR = {"semibold": 1.25, "semibold_italic": 1.20}


def patch_rings(ttfont, font_key):
    """Redraw the rings of the semibold styles. Returns report lines."""
    factor = RING_FACTOR.get(font_key)
    if factor is None:
        return []
    report = []
    for name, old, new in redraw_rings(ttfont, font_key, factor):
        if new is None:
            raise ValueError(f"{name}: no ring found to redraw")
        if old == "counter":
            report.append(f"{name}: ring counter inset by {new[0]}/{new[1]} (ring x {factor})")
        else:
            report.append(f"{name}: ring redrawn, stroke {old[0]}/{old[1]} -> {new[0]}/{new[1]} (x {factor})")
    return report
