#!/usr/bin/env python3
"""
implied_cap_marks_fontforge.py

Analyze implied cap-mark anchors in an SFD font using FontForge’s Python API.

This script:

1. Loads an SFD file.
2. Uses CAP_MARK_PRECOMPOSED (precomposed glyphs grouped by mark type).
3. For each precomposed glyph:
   - Classifies structure (components, base_only, outline_only, missing).
   - Detects manually copied mark outlines via structural comparison.
   - Solves affine transforms when appropriate.
   - Computes implied anchors from the mark glyph’s "above" anchor.
4. Prints a human-readable report.

Eventually CAP_MARK_PRECOMPOSED will be imported from:
    from data.ipa.ipa_unicode import CAP_MARK_PRECOMPOSED
"""

import sys
import math

try:
    import fontforge
except ImportError:
    sys.stderr.write("Error: FontForge Python module is required.\n")
    sys.exit(1)


# ---------------------------------------------------------------------------
# CAP_MARK_PRECOMPOSED — full dictionary (to be moved to data.ipa.ipa_unicode)
# ---------------------------------------------------------------------------

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


EPS = 1e-3


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def load_font(path):
    try:
        return fontforge.open(path)
    except Exception as e:
        sys.stderr.write(f"Error opening font '{path}': {e}\n")
        sys.exit(1)


def classify_structure(g):
    if g is None:
        return "missing"
    refs = g.references
    contours = list(g.foreground)
    if len(refs) >= 2:
        return "components"
    elif len(refs) == 1:
        return "base_only"
    elif contours:
        return "outline_only"
    else:
        return "missing"


def extract_inline_outline(g):
    return list(g.foreground)


def contour_points(contour):
    return [(p.x, p.y, bool(p.on_curve), p.type) for p in contour]


def normalize_points(points):
    xs = [x for x,y in points]
    ys = [y for x,y in points]
    cx = sum(xs)/len(xs)
    cy = sum(ys)/len(ys)
    translated = [(x-cx, y-cy) for x,y in points]
    maxd = max(math.hypot(x,y) for x,y in translated) or 1.0
    return [(x/maxd, y/maxd) for x,y in translated]


def is_structurally_same(inline, canonical):
    if len(inline) != len(canonical):
        return False
    for c1, c2 in zip(inline, canonical):
        pts1 = contour_points(c1)
        pts2 = contour_points(c2)
        if len(pts1) != len(pts2):
            return False
        seq1 = [(oc,t) for _,_,oc,t in pts1]
        seq2 = [(oc,t) for _,_,oc,t in pts2]
        if seq1 != seq2:
            return False
        norm1 = normalize_points([(x,y) for x,y,_,_ in pts1])
        norm2 = normalize_points([(x,y) for x,y,_,_ in pts2])
        for (x1,y1),(x2,y2) in zip(norm1,norm2):
            if math.hypot(x1-x2, y1-y2) > EPS:
                return False
    return True


def pick_three_points(contours):
    pts = [(p.x,p.y) for c in contours for p in c]
    if len(pts) < 3:
        return None
    p_high = max(pts, key=lambda xy: xy[1])
    p_low  = min(pts, key=lambda xy: xy[1])
    cx = sum(x for x,y in pts)/len(pts)
    cy = sum(y for x,y in pts)/len(pts)
    p_far = max(pts, key=lambda xy: math.hypot(xy[0]-cx, xy[1]-cy))
    return [p_high, p_low, p_far]


def solve_affine_transform(src, dst):
    def solve_3x3(m, v):
        det = (
            m[0][0]*(m[1][1]*m[2][2] - m[1][2]*m[2][1])
            - m[0][1]*(m[1][0]*m[2][2] - m[1][2]*m[2][0])
            + m[0][2]*(m[1][0]*m[2][1] - m[1][1]*m[2][0])
        )
        if abs(det) < 1e-9:
            return None
        inv = [[0]*3 for _ in range(3)]
        inv[0][0] = (m[1][1]*m[2][2] - m[1][2]*m[2][1]) / det
        inv[0][1] = (m[0][2]*m[2][1] - m[0][1]*m[2][2]) / det
        inv[0][2] = (m[0][1]*m[1][2] - m[0][2]*m[1][1]) / det
        inv[1][0] = (m[1][2]*m[2][0] - m[1][0]*m[2][2]) / det
        inv[1][1] = (m[0][0]*m[2][2] - m[0][2]*m[2][0]) / det
        inv[1][2] = (m[0][2]*m[1][0] - m[0][0]*m[1][2]) / det
        inv[2][0] = (m[1][0]*m[2][1] - m[1][1]*m[2][0]) / det
        inv[2][1] = (m[0][1]*m[2][0] - m[0][0]*m[2][1]) / det
        inv[2][2] = (m[0][0]*m[1][1] - m[0][1]*m[1][0]) / det
        return [sum(inv[i][j]*v[j] for j in range(3)) for i in range(3)]

    (x1,y1),(x2,y2),(x3,y3) = src
    (X1,Y1),(X2,Y2),(X3,Y3) = dst

    M = [[x1,y1,1],[x2,y2,1],[x3,y3,1]]
    sol_x = solve_3x3(M, [X1,X2,X3])
    sol_y = solve_3x3(M, [Y1,Y2,Y3])
    if sol_x is None or sol_y is None:
        return None
    a,c,tx = sol_x
    b,d,ty = sol_y
    return (a,b,c,d,tx,ty)


def apply_transform(points, T):
    a,b,c,d,tx,ty = T
    return [(a*x + c*y + tx, b*x + d*y + ty) for x,y in points]


def verify_transform(canon, inline, T):
    for c1,c2 in zip(canon, inline):
        pts1 = [(p.x,p.y) for p in c1]
        pts2 = [(p.x,p.y) for p in c2]
        if len(pts1) != len(pts2):
            return False
        transformed = apply_transform(pts1, T)
        for (xt,yt),(xi,yi) in zip(transformed, pts2):
            if math.hypot(xt-xi, yt-yi) > EPS:
                return False
    return True


def compute_implied_anchor(mark, T):
    anchors = mark.anchorPoints
    above = [a for a in anchors if a[0]=="above"]
    if not above:
        return None
    _, ax, ay, *_ = above[0]
    a,b,c,d,tx,ty = T
    return (a*ax + c*ay + tx, b*ax + d*ay + ty)


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def analyze_font(font):
    results = []

    for mark_name, pre_list in CAP_MARK_PRECOMPOSED.items():
        mark = font[mark_name] if mark_name in font else None

        for pre_name in pre_list:
            g = font[pre_name] if pre_name in font else None
            structure = classify_structure(g)
            notes = []
            T = None
            implied = None

            if mark is None:
                notes.append("missing_mark_glyph")
                results.append({
                    "pre": pre_name,
                    "mark": mark_name,
                    "structure": structure,
                    "transform": None,
                    "anchor": None,
                    "notes": notes,
                })
                continue

            if structure == "components":
                refs = g.references
                if len(refs) >= 2:
                    T = refs[1][1]
                    implied = compute_implied_anchor(mark, T)
                else:
                    notes.append("missing_mark_component")

            elif structure in ("base_only","outline_only"):
                inline = extract_inline_outline(g)
                canonical = list(mark.foreground)

                if is_structurally_same(inline, canonical):
                    src = pick_three_points(canonical)
                    dst = pick_three_points(inline)
                    if src and dst:
                        T = solve_affine_transform(src, dst)
                        if T and verify_transform(canonical, inline, T):
                            notes.append("manual_copy")
                            implied = compute_implied_anchor(mark, T)
                        else:
                            notes.append("affine_failed")
                    else:
                        notes.append("insufficient_points")
                else:
                    notes.append("malformed")

            else:
                notes.append("missing_precomposed")

            results.append({
                "pre": pre_name,
                "mark": mark_name,
                "structure": structure,
                "transform": T,
                "anchor": implied,
                "notes": notes,
            })

    return results


def print_report(results):
    for r in results:
        print(f"Glyph: {r['pre']}")
        print(f"  Mark:      {r['mark']}")
        print(f"  Structure: {r['structure']}")
        if r["transform"]:
            a,b,c,d,tx,ty = r["transform"]
            print(f"  Transform: a={a:.6f}, b={b:.6f}, c={c:.6f}, d={d:.6f}, tx={tx:.3f}, ty={ty:.3f}")
        else:
            print("  Transform: none")
        if r["anchor"]:
            ax,ay = r["anchor"]
            print(f"  Anchor:    ({ax:.3f}, {ay:.3f})")
        else:
            print("  Anchor:    none")
        print(f"  Notes:     {', '.join(r['notes']) if r['notes'] else 'none'}")
        print()


def main(argv):
    if len(argv) < 2:
        sys.stderr.write("Usage: implied_cap_marks_fontforge.py font.sfd\n")
        sys.exit(1)

    font = load_font(argv[1])
    results = analyze_font(font)
    print_report(results)


if __name__ == "__main__":
    main(sys.argv)
