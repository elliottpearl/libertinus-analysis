# fontmetrics_extract_tags.py
#
# Compute first-pass semantic tags for glyph outlines.

from fontTools.pens.boundsPen import BoundsPen


# ------------------------------------------------------------
# Helpers for outline analysis
# ------------------------------------------------------------

def find_vertical_stems(glyph, stem_width=70, tolerance=15):
    """
    Return list of x positions of vertical stems.
    A stem is approximated as a vertical segment with thickness ~ stem_width.
    """
    stems = []
    pen = BoundsPen(glyph.font)
    glyph.draw(pen)
    if pen.bounds is None:
        return stems

    xMin, _, xMax, _ = pen.bounds
    width = xMax - xMin

    # If width is close to stem width, treat as single stem
    if abs(width - stem_width) < tolerance:
        stems.append((xMin + xMax) / 2)

    return stems


def find_bowl_centroids(glyph):
    """
    Very rough heuristic: treat each closed contour as a bowl.
    Compute centroid of contour bbox.
    NOTE: This relies on glyph._glyph.coordinates.contours, which is
    specific to the fontTools glyph implementation used here.
    """
    bowls = []
    # Defensive: if the attribute is missing, just return empty
    if not hasattr(glyph, "_glyph") or not hasattr(glyph._glyph, "coordinates"):
        return bowls
    if not hasattr(glyph._glyph.coordinates, "contours"):
        return bowls

    for contour in glyph._glyph.coordinates.contours:
        xs = [pt[0] for pt in contour]
        ys = [pt[1] for pt in contour]
        if len(xs) > 2:
            cx = sum(xs) / len(xs)
            cy = sum(ys) / len(ys)
            bowls.append((cx, cy))
    return bowls


# ------------------------------------------------------------
# Main tag computation
# ------------------------------------------------------------

def compute_semantic_tags(glyph, bbox, width, lsb, rsb, style="roman"):
    """
    Compute boolean semantic tags for a glyph.
    """
    xMin, yMin, xMax, yMax = bbox
    bbox_center = (xMin + xMax) / 2

    tags = {
        "has_left_stem": False,
        "has_right_stem": False,
        "has_left_bowl": False,
        "has_right_bowl": False,
        "has_overhang_right": False,
        "is_symmetric": False,
        "is_multi_bowl": False,
        "is_italic_slanted": ("italic" in style.lower()),
    }

    # Stems
    stems = find_vertical_stems(glyph)
    for sx in stems:
        if sx < bbox_center:
            tags["has_left_stem"] = True
        if sx > bbox_center:
            tags["has_right_stem"] = True

    # Bowls
    bowls = find_bowl_centroids(glyph)
    if len(bowls) >= 2:
        tags["is_multi_bowl"] = True
    for cx, cy in bowls:
        if cx < bbox_center:
            tags["has_left_bowl"] = True
        if cx > bbox_center:
            tags["has_right_bowl"] = True

    # Overhang
    if rsb < 0 or xMax > width:
        tags["has_overhang_right"] = True

    # Symmetry (very rough)
    if abs(lsb - rsb) < 10:
        if not (tags["has_left_bowl"] ^ tags["has_right_bowl"]):
            if not (tags["has_left_stem"] ^ tags["has_right_stem"]):
                tags["is_symmetric"] = True

    return tags
