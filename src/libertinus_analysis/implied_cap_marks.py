# implied_cap_marks.py
# Compute implied anchors for .cap marks using fonttools + FontForge.

import fontforge
from fontTools.ttLib import TTFont
import unicodedata

TOLERANCE = 1.0

# ------------------------------------------------------------
# 1. Curated dictionary of precomposed capital letters
# ------------------------------------------------------------

CAP_MARK_PRECOMPOSED = {
    "acute.cap": [
        0x00C1, 0x00C9, 0x00CD, 0x00D3, 0x00DA, 0x00DD,
        0x01F4, 0x1E30, 0x0139, 0x0143, 0x0154, 0x015A, 0x0179,
    ],

    "grave.cap": [
        0x00C0, 0x00C8, 0x00CC, 0x00D2, 0x00D9,
        0x1E80, 0x1EF2,
    ],

    "circumflex.cap": [
        0x00C2, 0x00CA, 0x00CE, 0x00D4, 0x00DB,
        0x1E90, 0x0124, 0x0134,
    ],

    "breve.cap": [
        0x0102, 0x0114, 0x012C, 0x014E, 0x016C,
    ],

    "dotaccent.cap": [
        0x0226, 0x1E02, 0x010A, 0x1E0A, 0x0116, 0x0120,
        0x1E22, 0x0130, 0x1E40, 0x1E44, 0x1E56,
        0x015A, 0x1E6A, 0x017B,
    ],

    "dieresis.cap": [
        0x00C4, 0x00CB, 0x00CF, 0x00D6, 0x00DC,
        0x1E84, 0x0178,
    ],

    "hookabovecomb.cap": [
        0x1EA2, 0x1EBA, 0x1EC8, 0x1ECE, 0x1EE6, 0x1EF6,
    ],

    "hungarumlaut.cap": [
        0x0150, 0x0170,
    ],

    "caron.cap": [
        0x010C, 0x010E, 0x011A, 0x01E6, 0x021E, 0x01CF,
        0x01E8, 0x013D, 0x0147, 0x0158, 0x0160, 0x0164, 0x017D,
        0x01EE,
    ],

    "uni030F.cap": [
        0x020E, 0x0212,
    ],

    "breveinvertedcmb.cap": [
        0x0202, 0x0206, 0x020A, 0x020E, 0x0212,
    ],
}

# ------------------------------------------------------------
# 2. Helpers
# ------------------------------------------------------------

def load_cmap(otf_path):
    """Return a dict: Unicode → glyph name."""
    tt = TTFont(otf_path)
    cmap = {}
    for table in tt["cmap"].tables:
        if table.isUnicode():
            cmap.update(table.cmap)
    return cmap


def classify_component(glyph):
    """Classify a glyph as base or mark."""
    cat = None
    if glyph.unicode is not None:
        try:
            cat = unicodedata.category(chr(glyph.unicode))
        except Exception:
            pass

    kinds = {a[1] for a in glyph.anchorPoints}

    if cat == "Mn" or "mark" in kinds:
        return "mark"

    if glyph.glyphname.endswith(".cap"):
        return "mark"

    if cat and cat.startswith("L"):
        return "base"
    if "base" in kinds or "basemark" in kinds:
        return "base"

    return "other"


def get_anchor(glyph, name, kind):
    for n, k, ax, ay in glyph.anchorPoints:
        if n == name and k == kind:
            return (ax, ay)
    return None


def inverse_transform_point(x, y, transform):
    a, b, c, d, tx, ty = transform
    return (x - tx, y - ty)


def resolve_base_for_cap_analysis(font, base_glyph):
    """Override Epsilon → E for cap-mark analysis."""
    if base_glyph.glyphname != "Epsilon":
        return base_glyph

    e = font["E"]
    if e.anchorPoints:
        return e

    return base_glyph

# ------------------------------------------------------------
# 3. Core analysis for one mark
# ------------------------------------------------------------

def analyze_precomposed_for_mark(font, cmap, mark_name, cps):
    entries = []
    warnings = []

    for cp in cps:
        if cp not in cmap:
            warnings.append(f"{mark_name}: U+{cp:04X} missing from cmap")
            continue

        glyph_name = cmap[cp]

        if glyph_name not in font:
            warnings.append(f"{mark_name}: U+{cp:04X} glyph '{glyph_name}' missing from SFD")
            continue

        g = font[glyph_name]
        refs = g.references

        if len(refs) != 2:
            warnings.append(f"{mark_name}: U+{cp:04X} '{glyph_name}' unexpected structure ({len(refs)} components)")
            continue

        base_ref = None
        mark_ref = None

        for refname, transform, *_ in refs:
            if refname not in font:
                warnings.append(f"{mark_name}: U+{cp:04X} '{glyph_name}' references missing glyph '{refname}'")
                continue

            refglyph = font[refname]
            cls = classify_component(refglyph)

            if cls == "base":
                base_ref = (refglyph, transform)
            elif cls == "mark":
                mark_ref = (refglyph, transform)
            else:
                warnings.append(f"{mark_name}: U+{cp:04X} '{glyph_name}' unexpected component '{refname}'")

        if not base_ref or not mark_ref:
            warnings.append(f"{mark_name}: U+{cp:04X} '{glyph_name}' missing base or mark")
            continue

        base_glyph, base_transform = base_ref
        mark_glyph, mark_transform = mark_ref

        # E/Epsilon override
        if base_glyph.glyphname == "Epsilon":
            warnings.append(f"{mark_name}: U+{cp:04X} '{glyph_name}' uses Epsilon → overriding with E")
            base_glyph = resolve_base_for_cap_analysis(font, base_glyph)

        # Check mark correctness
        if mark_glyph.glyphname != mark_name:
            warnings.append(
                f"{mark_name}: U+{cp:04X} '{glyph_name}' expected mark '{mark_name}', found '{mark_glyph.glyphname}'"
            )
            continue

        # Base anchor
        base_anchor = get_anchor(base_glyph, "above", "base")
        if base_anchor is None:
            warnings.append(
                f"{mark_name}: base '{base_glyph.glyphname}' has no 'above' anchor"
            )
            continue

        ax, ay = base_anchor
        a, b, c, d, tx, ty = base_transform
        implied_x = a * ax + c * ay + tx
        implied_y = b * ax + d * ay + ty

        # Convert to mark space
        mx, my = inverse_transform_point(implied_x, implied_y, mark_transform)

        entries.append((base_glyph.glyphname, mx, my))

    return entries, warnings

# ------------------------------------------------------------
# 4. Full analysis
# ------------------------------------------------------------

def compute_cap_mark_implied_anchors(font, cmap):
    results = {}
    all_warnings = {}

    for mark_name, cps in CAP_MARK_PRECOMPOSED.items():
        entries, warnings = analyze_precomposed_for_mark(font, cmap, mark_name, cps)
        results[mark_name] = entries
        all_warnings[mark_name] = warnings

    return results, all_warnings

# ------------------------------------------------------------
# 5. Final formatted output
# ------------------------------------------------------------

def summarize_cap_mark_results(results, warnings):
    lines = []

    for mark, entries in results.items():
        lines.append(f"{mark}:")

        for w in warnings.get(mark, []):
            lines.append(f"  WARNING: {w}")

        if not entries:
            lines.append("  (no usable data)\n")
            continue

        xs = [x for _, x, _ in entries]
        ys = [y for _, _, y in entries]

        avg_x = sum(xs) / len(xs)
        avg_y = sum(ys) / len(ys)

        bases = ", ".join(b for b, _, _ in entries)

        lines.append(f"  bases: {bases}")
        lines.append(f"  avg: ({avg_x:.1f}, {avg_y:.1f})")
        lines.append(f"  x-range: {min(xs):.1f} .. {max(xs):.1f}")
        lines.append(f"  y-range: {min(ys):.1f} .. {max(ys):.1f}")
        lines.append("")

    return "\n".join(lines)
