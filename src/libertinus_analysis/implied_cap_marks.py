# implied_cap_marks.py
# Compute implied anchors for .cap marks using glyph-name-only precomposed lists.

import fontforge
import unicodedata

# --------------------------------------------------------------------
# 1. Glyph-name-only precomposed lists (from your reconciled cmap)
# --------------------------------------------------------------------

CAP_MARK_PRECOMPOSED = {
    "acute.cap": [
        "Aacute", "Eacute", "Iacute", "Oacute", "Uacute", "Yacute",
        "uni01F4", "Lacute", "Nacute", "Racute", "Sacute", "Zacute",
    ],

    "grave.cap": [
        "Agrave", "Egrave", "Igrave", "Ograve", "Ugrave", "Wgrave", 
        "Ygrave",
    ],

    "circumflex.cap": [
        "Acircumflex", "Ecircumflex", "Icircumflex", "Ocircumflex", 
        "Ucircumflex", "Hcircumflex", "Jcircumflex", "uni1E90",
    ],

    "breve.cap": [
        "Abreve", "Ebreve", "Ibreve", "Obreve", "Ubreve",
    ],

    "dotaccent.cap": [
        "Cdotaccent", "Edotaccent", "Gdotaccent", "uni1E22", "Idotaccent",
        "uni1E40", "uni1E44", "uni1E56", "uni1E58", "uni1E60", "uni1E6A", 
        "uni1E86", "uni1E8E", "Zdotaccent",
    ],

    "dieresis.cap": [
        "Adieresis", "Edieresis", "Idieresis", "Odieresis", "Udieresis",
        "Wdieresis", "Ydieresis",
    ],

    "hookabovecomb.cap": [
        "uni1EA2", "uni1EBA", "uni1EC8", "uni1ECE", "uni1EE6", "uni1EF6",
    ],

    "hungarumlaut.cap": [
        "Ohungarumlaut", "Uhungarumlaut",
    ],

    "caron.cap": [
        "Ccaron", "Dcaron", "Ecaron", "Gcaron", "uni021E", "uni01CF", 
        "uni01E8", "Ncaron", "Rcaron", "Scaron", "Tcaron", "Zcaron",
    ],

    "uni030F.cap": [
        "uni0200", "uni0204", "uni0208", "uni020C", "uni0210", "uni0214",
    ],

    "breveinvertedcmb.cap": [
        "uni0202", "uni0206", "uni020A", "uni020E", "uni0212", "uni0216",
    ],
}

# --------------------------------------------------------------------
# 2. Mark aliasing (minimal: only dotaccent.cap → uni0358)
# --------------------------------------------------------------------

MARK_ALIASES = {
    "dotaccent.cap": {"dotaccent.cap", "uni0358"},
}

def allowed_mark_names(mark_name):
    return MARK_ALIASES.get(mark_name, {mark_name})

# --------------------------------------------------------------------
# 3. Helpers
# --------------------------------------------------------------------

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
    """Override Epsilon → E, uni0405 → S."""
    name = base_glyph.glyphname

    if name == "Epsilon":
        e = font["E"]
        if e.anchorPoints:
            return e

    if name == "uni0405":
        s = font["S"]
        if s.anchorPoints:
            return s

    return base_glyph

# --------------------------------------------------------------------
# 4. Core analysis for one mark
# --------------------------------------------------------------------

def analyze_precomposed_for_mark(font, mark_name, glyph_names):
    entries = []
    warnings = []

    allowed = allowed_mark_names(mark_name)

    for gname in glyph_names:
        if gname not in font:
            warnings.append(f"{mark_name}: glyph '{gname}' missing from SFD")
            continue

        g = font[gname]
        refs = g.references

        if len(refs) != 2:
            warnings.append(f"{mark_name}: '{gname}' unexpected structure ({len(refs)} components)")
            continue

        base_ref = None
        mark_ref = None

        for refname, transform, *_ in refs:
            if refname not in font:
                warnings.append(f"{mark_name}: '{gname}' references missing glyph '{refname}'")
                continue

            refglyph = font[refname]
            cls = classify_component(refglyph)

            if cls == "base":
                base_ref = (refglyph, transform)
            elif cls == "mark":
                mark_ref = (refglyph, transform)
            else:
                warnings.append(f"{mark_name}: '{gname}' unexpected component '{refname}'")

        if not base_ref or not mark_ref:
            warnings.append(f"{mark_name}: '{gname}' missing base or mark")
            continue

        base_glyph, base_transform = base_ref
        mark_glyph, mark_transform = mark_ref

        # mark aliasing (dotaccent.cap → uni0358)
        if mark_glyph.glyphname not in allowed:
            warnings.append(
                f"{mark_name}: '{gname}' expected mark in {allowed}, found '{mark_glyph.glyphname}'"
            )
            continue

        # base override
        base_glyph = resolve_base_for_cap_analysis(font, base_glyph)

        # base anchor
        base_anchor = get_anchor(base_glyph, "above", "base")
        if base_anchor is None:
            warnings.append(f"{mark_name}: base '{base_glyph.glyphname}' has no 'above' anchor")
            continue

        ax, ay = base_anchor
        a, b, c, d, tx, ty = base_transform
        implied_x = a * ax + c * ay + tx
        implied_y = b * ax + d * ay + ty

        # convert to mark space
        mx, my = inverse_transform_point(implied_x, implied_y, mark_transform)

        entries.append((base_glyph.glyphname, mx, my))

    return entries, warnings

# --------------------------------------------------------------------
# 5. Full analysis
# --------------------------------------------------------------------

def compute_cap_mark_implied_anchors(font):
    results = {}
    all_warnings = {}

    for mark_name, glyph_names in CAP_MARK_PRECOMPOSED.items():
        entries, warnings = analyze_precomposed_for_mark(font, mark_name, glyph_names)
        results[mark_name] = entries
        all_warnings[mark_name] = warnings

    return results, all_warnings

# --------------------------------------------------------------------
# 6. Summary
# --------------------------------------------------------------------

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
