# abandoned code; build report as a string; analyzes cap alt marks
import fontforge
import unicodedata

print("FontForge module:", fontforge)
print("FontForge version:", getattr(fontforge, "version", None))
print("FontForge dir:", getattr(fontforge, "__file__", None))



from data.ipa.ipa_unicode import (
    PRECOMPOSED_CAPITAL_VOWELS,
    PRECOMPOSED_SMALL_VOWELS,
    PRECOMPOSED_CAPITAL_CONSONANTS,
    PRECOMPOSED_SMALL_CONSONANTS,
)

PRECOMPOSED_ALL = set(
    PRECOMPOSED_CAPITAL_VOWELS +
    PRECOMPOSED_SMALL_VOWELS +
    PRECOMPOSED_CAPITAL_CONSONANTS +
    PRECOMPOSED_SMALL_CONSONANTS
)

TOLERANCE = 1.0

ANCHOR_INDEX = {
    "above": 0,
    "right": 1,
    "below": 2,
    "kombor": 3,
    "belowright": 4,
    "ogonek": 4,
    "cedilla": 5,
    "middle": 6,
}

def normalize_anchor_name(name):
    if not name:
        return ""
    n = name.strip().lower()
    n = n.replace(" ", "").replace("_", "")
    return n

def classify_component(glyph):
    # Unicode-based classification
    cat = None
    if glyph.unicode is not None:
        try:
            cat = unicodedata.category(chr(glyph.unicode))
        except Exception:
            pass

    kinds = {a[1] for a in glyph.anchorPoints}

    # Existing mark logic
    if cat == "Mn" or "mark" in kinds:
        return "mark"

    # NEW: treat all .cap glyphs as marks
    if glyph.glyphname.endswith(".cap"):
        return "mark"

    # Existing base logic
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

def unicode_name_lower(codepoint):
    try:
        name = unicodedata.name(chr(codepoint))
    except ValueError:
        return "UNKNOWN"
    name = name.lower()
    name = name.replace("latin small letter", "Latin small letter")
    name = name.replace("latin capital letter", "Latin capital letter")
    name = name.replace("with", "with")
    return name

def get_anchor_index_for_glyph(glyph):
    for n, k, ax, ay in glyph.anchorPoints:
        key = normalize_anchor_name(n)
        if key in ANCHOR_INDEX:
            return ANCHOR_INDEX[key]
    return 0

def inverse_transform_point(x, y, transform):
    a, b, c, d, tx, ty = transform
    return (x - tx, y - ty)

def get_expected_marks(cp):
    """Return a set of expected combining mark codepoints from Unicode decomposition."""
    try:
        decomp = unicodedata.decomposition(chr(cp))
    except ValueError:
        return set()

    if not decomp:
        return set()

    parts = decomp.split()
    expected = set()

    for p in parts:
        if len(p) == 4:
            try:
                u = int(p, 16)
                if unicodedata.category(chr(u)) == "Mn":
                    expected.add(u)
            except Exception:
                pass

    return expected

def analyze(font):

    count_total = 0
    count_unicode = 0
    count_precomposed = 0

    for g in font.glyphs():
        count_total += 1
        if g.unicode is not None:
            count_unicode += 1
            if g.unicode in PRECOMPOSED_ALL:
                count_precomposed += 1

    for g in font.glyphs():
        if g.unicode in PRECOMPOSED_ALL:
            print("Sample glyph:", g.glyphname, f"U+{g.unicode:04X}")
            print("  references:", g.references)
            print("  anchorPoints:", g.anchorPoints)
            break

    print("DEBUG:", count_total, "glyphs total")
    print("DEBUG:", count_unicode, "glyphs with Unicode")
    print("DEBUG:", count_precomposed, "glyphs in PRECOMPOSED_ALL")
 
    print("DEBUG: glyphs in PRECOMPOSED_ALL with >=2 refs:",
          sum(1 for g in font.glyphs()
              if g.unicode in PRECOMPOSED_ALL and len(g.references) >= 2))





    lines = []

    for g in font.glyphs():
        if g.unicode is None or g.unicode not in PRECOMPOSED_ALL:
            continue

        refs = g.references
        if len(refs) < 2:
            continue

        cp = g.unicode
        char = chr(cp)
        name = unicode_name_lower(cp)
        lines.append(f"U+{cp:04X} {char}  {name}:")

        comp_info = []
        base_indices = []
        mark_indices = []
        other_indices = []

        for i, (refname, transform, *_) in enumerate(refs):
            refglyph = font[refname]
            cls = classify_component(refglyph)
            comp_info.append((i, refname, refglyph, cls, transform))

            if cls == "base":
                base_indices.append(i)
            elif cls == "mark":
                mark_indices.append(i)
            else:
                other_indices.append(i)

            uni = refglyph.unicode
            uni_str = f"U+{uni:04X}" if uni is not None else "U+----"
            lines.append(f"  component {i}: {refname} ({uni_str}) [{cls}]")

        expected_marks = get_expected_marks(cp)

        if expected_marks:
            actual_marks = {
                refglyph.unicode
                for (_, _, refglyph, cls, _) in comp_info
                if cls == "mark" and refglyph.unicode is not None
            }

            unexpected = actual_marks - expected_marks
            if unexpected:
                exp_str = ", ".join(f"U+{u:04X}" for u in expected_marks)
                act_str = ", ".join(f"U+{u:04X}" for u in actual_marks)
                lines.append(
                    f"  Combined with unexpected mark: expected {{{exp_str}}}, found {{{act_str}}}"
                )
                lines.append("")
                continue

        if len(base_indices) != 1:
            lines.append("  No implied anchors (no single base component)")
            lines.append("")
            continue

        if len(mark_indices) == 0:
            lines.append("  No implied anchors (no mark components)")
            lines.append("")
            continue

        if len(other_indices) > 0:
            lines.append("  No implied anchors (mixed components)")
            lines.append("")
            continue

        transformed_positions = {}
        any_anchor_present = False

        for i, refname, refglyph, cls, transform in comp_info:
            if cls == "base":
                anchor = get_anchor(refglyph, "above", "base")
            elif cls == "mark":
                anchor = get_anchor(refglyph, "above", "mark")
            else:
                anchor = None

            if anchor is None:
                transformed_positions[refglyph.glyphname] = (False, None, transform)
            else:
                ax, ay = anchor
                a, b, c, d, tx, ty = transform
                x = a * ax + c * ay + tx
                y = b * ax + d * ay + ty
                transformed_positions[refglyph.glyphname] = (True, (x, y), transform)
                any_anchor_present = True

        if not any_anchor_present:
            lines.append("  Combined at implied anchors (no existing anchors)")
            lines.append("")
            continue

        base_i = base_indices[0]
        _, base_refname, base_refglyph, _, base_transform = comp_info[base_i]
        has_base_anchor, base_pos, _ = transformed_positions[base_refglyph.glyphname]

        if not has_base_anchor:
            lines.append("  Combined at implied anchors (base missing anchor)")
            lines.append("")
            continue

        implied_x, implied_y = base_pos

        composite_inconsistent = False
        max_dx = 0.0
        max_dy = 0.0

        for i, refname, refglyph, cls, transform in comp_info:
            has_anchor, pos, _ = transformed_positions[refglyph.glyphname]
            if not has_anchor:
                composite_inconsistent = True
                continue

            x, y = pos
            dx = implied_x - x
            dy = implied_y - y
            max_dx = max(max_dx, abs(dx))
            max_dy = max(max_dy, abs(dy))

            if abs(dx) > TOLERANCE or abs(dy) > TOLERANCE:
                composite_inconsistent = True

        if not composite_inconsistent:
            lines.append("  Combined at existing anchors")
            lines.append("")
            continue

        dx_report = int(round(max_dx))
        dy_report = int(round(max_dy))
        lines.append(
            f"  Combined at implied anchors, offset dx = {dx_report}, dy = {dy_report}"
        )

        for i, refname, refglyph, cls, transform in comp_info:
            has_anchor, pos, _ = transformed_positions[refglyph.glyphname]
            if not has_anchor:
                continue

            gx, gy = inverse_transform_point(implied_x, implied_y, transform)
            gx = int(round(gx))
            gy = int(round(gy))
            idx = get_anchor_index_for_glyph(refglyph)

            uni = refglyph.unicode
            uni_str = f"0x{uni:04X}" if uni is not None else "NONE"
            lines.append(f"  {uni_str}: {{ # {refglyph.glyphname}")
            lines.append(f"    {idx}: ({gx},{gy}),")
            lines.append("  },")

        lines.append("")

    return "\n".join(lines)
