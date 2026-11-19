"""
Heavier semibold rings: draft fonts and test sheet (see ring_drafts.py).

    .venv/bin/python run_ring_draft_sheet.py
    cd tex && xelatex ring_draft_sheet.tex
"""
import sys

sys.path.insert(0, "src")
sys.path.insert(0, ".")
from libertinus_analysis.ring_drafts import FACTORS, draft_rings, light_stroke  # noqa: E402

FILE = {"semibold": "Semibold", "semibold_italic": "SemiboldItalic"}
LIGHT_FILE = {"semibold": "Regular", "semibold_italic": "Italic"}
LABEL = {"semibold": "Semibold", "semibold_italic": "Semibold italic"}
CGJ = "͏"
# isolated marks on a dotted circle, the precomposed glyphs, then composed combos (CGJ keeps them composed)
SAMPLES = ["◌̊", "◌̥", "˚", "å", "Å", "ů", "Ů", "ǻ", "Ǻ", "ḁ", "Ḁ", "ẘ", "ẙ",
           "a" + CGJ + "̊", "u" + CGJ + "̊", "n̥", "m̥", "ŋ̊", "l̥", "ɖ̥", "a" + CGJ + "̥"]
CONTEXT = "Ångström åker till Brno, Růžena; [n̥ m̥ ŋ̊ l̥ ɹ̥ d̥ ɖ̥ ḁ ẘ]"


def tex(s):
    return "".join(r"\ " if c == " " else f'\\char"{ord(c):04X}' for c in s)


def _recording(font_path, name):
    from fontTools.pens.recordingPen import RecordingPen
    from fontTools.ttLib import TTFont
    pen = RecordingPen()
    TTFont(font_path).getGlyphSet()[name].draw(pen)
    return pen.value


def _clip_contours(rec, box):
    """Contours of rec whose on-curve points all lie in box (x0, y0, x1, y1)."""
    out, cur = [], []
    for op, args in rec:
        cur.append((op, args))
        if op == "closePath":
            pts = [p for o, a in cur if o != "closePath" for p in a[-1:]]
            if all(box[0] <= x <= box[2] and box[1] <= y <= box[3] for x, y in pts):
                out += cur
            cur = []
    return out


def tikz_outline(rec, scale=0.028, box=None):
    """FontForge-like outline view: filled outline, on-curve points (squares), off-curve
    points (circles) on their handles, every point labelled (x,y). If box is given, the
    glyph is clipped to it and only the points inside are drawn."""
    def c(p):
        return f"({p[0] * scale:.3f},{p[1] * scale:.3f})"
    path, pts, handles, cur = [], [], [], None
    for op, args in rec:
        if op == "moveTo":
            path.append(f"{c(args[0])}"); cur = args[0]; pts.append(("on", args[0]))
        elif op == "lineTo":
            path.append(f"-- {c(args[0])}"); cur = args[0]; pts.append(("on", args[0]))
        elif op == "curveTo":
            c1, c2, end = args
            path.append(f".. controls {c(c1)} and {c(c2)} .. {c(end)}")
            handles += [(cur, c1), (end, c2)]
            pts += [("off", c1), ("off", c2), ("on", end)]
            cur = end
        elif op == "closePath":
            path.append("-- cycle")
    inside = (lambda p: True) if box is None else (lambda p: box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3])
    out = [r"\begin{tikzpicture}"]
    if box is not None:
        out.append(rf"\clip {c((box[0], box[1]))} rectangle {c((box[2], box[3]))};")
    out.append(r"\fill[black!12, even odd rule] " + " ".join(path) + ";")
    out.append(r"\draw[black!70, line width=0.4pt] " + " ".join(path) + ";")
    for a, b in handles:
        if inside(a) or inside(b):
            out.append(rf"\draw[draft!70, line width=0.3pt] {c(a)} -- {c(b)};")
    seen = set()
    for kind, p in pts:
        if not inside(p) or (kind, p) in seen:
            continue
        seen.add((kind, p))
        if kind == "on":
            out.append(rf"\fill[black] {c((p[0] - 2.2 / scale * 0.028, p[1] - 2.2 / scale * 0.028))} rectangle {c((p[0] + 2.2 / scale * 0.028, p[1] + 2.2 / scale * 0.028))};")
            out.append(rf"\node[font=\fontsize{{4.5}}{{5}}\selectfont, anchor=south west, inner sep=0.6pt] at {c(p)} {{{p[0]:.0f},{p[1]:.0f}}};")
        else:
            out.append(rf"\draw[draft, fill=white, line width=0.3pt] {c(p)} circle (0.55pt);")
            out.append(rf"\node[font=\fontsize{{4.5}}{{5}}\selectfont, text=draft, anchor=north east, inner sep=0.6pt] at {c(p)} {{{p[0]:.0f},{p[1]:.0f}}};")
    out.append(r"\end{tikzpicture}")
    return "\n".join(out)


def point_table(rec):
    """The contours as text: one line per contour, on-curve points bold, off-curve plain."""
    lines, cur = [], []
    for op, args in rec:
        if op == "moveTo":
            cur = [rf"\textbf{{{args[0][0]:.0f},{args[0][1]:.0f}}}"]
        elif op == "curveTo":
            cur += [f"{p[0]:.0f},{p[1]:.0f}" for p in args[:2]] + [rf"\textbf{{{args[2][0]:.0f},{args[2][1]:.0f}}}"]
        elif op == "lineTo":
            cur.append(rf"\textbf{{{args[0][0]:.0f},{args[0][1]:.0f}}}")
        elif op == "closePath":
            lines.append(r"\ ".join(cur))
    return r"\par ".join(lines)


def main():
    rows = {}
    for style in FILE:
        rows[style] = {"light": light_stroke(style)}
        for f in FACTORS:
            path = f"fonts/LibertinusSerif-{FILE[style]}-ring{round(f * 100)}.otf"
            _, rep = draft_rings(style, f, path)
            rows[style][f] = rep
            skipped = [n for n, old, new in rep if new is None]
            print(f"{path}: {len(rep) - len(skipped)} glyphs redrawn" + (f"; not found: {skipped}" if skipped else ""))

    L = [r"""% Generated by run_ring_draft_sheet.py; do not edit.
\documentclass[10pt]{article}
\usepackage{fontspec}
\usepackage{xcolor}
\usepackage{array}
\usepackage{tikz}
\usepackage{geometry}
\geometry{a4paper, landscape, left=1.2cm, right=1.2cm, top=1.2cm, bottom=1.2cm}
\setlength{\parindent}{0pt}
\definecolor{draft}{RGB}{20,70,190}
\setmainfont{Libertinus Serif}[Path = ../fonts/, UprightFont = LibertinusSerif-Regular.otf, ItalicFont = LibertinusSerif-Italic.otf, BoldFont = LibertinusSerif-Semibold.otf, BoldItalicFont = LibertinusSerif-SemiboldItalic.otf]"""]
    fam = {}
    for style in FILE:
        fam[(style, "light")] = f"LibertinusSerif-{LIGHT_FILE[style]}-patch.otf"
        fam[(style, "designer")] = f"LibertinusSerif-{FILE[style]}-patch.otf"
        for f in FACTORS:
            fam[(style, f)] = f"LibertinusSerif-{FILE[style]}-ring{round(f * 100)}.otf"
    macro = {}
    for k, (key, file) in enumerate(fam.items()):
        name = "\\F" + "abcdefghijklmnop"[k]
        macro[key] = name
        L.append(rf"\newfontfamily{name}[Path = ../fonts/]{{{file}}}")
    L.append(r"""\begin{document}
\section*{Test sheet: heavier rings in the semibold styles (draft)}
The designer's semibold rings are no heavier than the light styles' (U+0325 is lighter), where other fonts' bold rings are 13--60\,\% heavier than their regular
(stroke at the sides / at the top, regular → bold: Noto Serif 54/49 → 61/55, Pagella ring above 38/36 → 50/50, Junicode 47/33 → 67/40, Gentium Plus 90/76 → 135/121 in 2048 units),
and the designer's own semibold dot above is 24\,\% and diaeresis 15\,\% heavier than regular's.
The drafts redraw every ring of the semibold styles (U+030A, U+0325, U+02DA, å Å ů Ů ǻ Ǻ ḁ Ḁ ẘ ẙ and the small caps) rather than scaling the designer's:
two Bézier ellipses (four on-curve points at the extremes, handles 0.5523 × the radius), the outer at the designer's centre and outer size,
the inner inset by the target stroke, sheared at 11.5° about the centre in semibold italic, every point a whole unit.
Target stroke = 1.15 or 1.25 × the light style's ring stroke (regular's 40/32 for semibold, italic's 37/27 for semibold italic), never lighter than the designer's.
The small caps aring.sc and uring.sc are redrawn too, but cannot be shown: the patched fonts' GSUB has only ccmp (no smcp). In Å and Ǻ the ring is merged with the apex (and Ǻ's acute), so only the counter is redrawn, inset by what the stroke gains.
Rows: the light style (patched), the designer's semibold (patched), and the two drafts in \textcolor{draft}{blue}. Composed combos use CGJ where a precomposed glyph exists.

\medskip
\begin{tabular}{l l l l l}
style & light style's ring & designer's (U+030A; U+0325) & draft × 1.15 & draft × 1.25 \\ \hline""")
    for style in FILE:
        lsx, lsy = rows[style]["light"]
        des = {n: old for n, old, _ in rows[style][FACTORS[0]] if old not in (None, "counter")}
        new = [{n: v for n, o, v in rows[style][f] if o not in (None, "counter")}["uni030A"] for f in FACTORS]
        L.append(f"{LABEL[style]} & {lsx:.0f}/{lsy:.0f} & {des['uni030A'][0]}/{des['uni030A'][1]}; "
                 f"{des['uni0325'][0]}/{des['uni0325'][1]} & {new[0][0]}/{new[0][1]} & {new[1][0]}/{new[1][1]} \\\\")
    L.append(r"\end{tabular}")

    for style in FILE:
        L.append(rf"\section*{{{LABEL[style]}}}")
        for size, text, big in ((26, None, False), (60, None, True)):
            L.append(rf"\begin{{tabular}}{{>{{\small}}l l}}")
            for key, lab in (("light", "light style"), ("designer", "designer"), *((f, f"draft × {f}") for f in FACTORS)):
                samples = SAMPLES[:2] + ["å", "ů", "ḁ", "Å", "n̥"] if big else SAMPLES
                body = r"\ ".join(tex(s) for s in samples)
                colour = r"\color{draft}" if isinstance(key, float) else ""
                L.append(rf"{lab} & {{{macro[(style, key)]}{colour}\fontsize{{{size}}}{{{size * 1.3:.0f}}}\selectfont {body}}} \\")
            L.append(r"\end{tabular}\par\medskip")
        L.append(r"\begin{tabular}{>{\small}l l}")
        for key, lab in (("light", "light style"), ("designer", "designer"), *((f, f"draft × {f}") for f in FACTORS)):
            colour = r"\color{draft}" if isinstance(key, float) else ""
            L.append(rf"{lab} & {{{macro[(style, key)]}{colour}\fontsize{{14}}{{18}}\selectfont {tex(CONTEXT)}}} \\")
        L.append(r"\end{tabular}\par")
        L.append(r"\clearpage")
    L.append(r"\section*{Control points}")
    L.append(r"Each ring as FontForge's outline view shows it: on-curve points as black squares, off-curve points as "
             r"\textcolor{draft}{blue circles} on their handles, every point labelled with its coordinates; the contours are also "
             r"listed below each figure (on-curve bold, each followed by the off-curve points of the curve that leaves it, start point first). "
             r"Outer contours run counter-clockwise from the left extreme, inner ones clockwise from the top, as the designer's. "
             r"Å: the glyph clipped to its ring, where only the counter is redrawn.\par\medskip")
    for style in FILE:
        designer = f"fonts/LibertinusSerif-{FILE[style]}-patch.otf"
        versions = [("designer", designer)] + [(f"draft × {f}", f"fonts/LibertinusSerif-{FILE[style]}-ring{round(f * 100)}.otf") for f in FACTORS]
        for glyph, label in (("uni030A", "U+030A ring above"), ("uni0325", "U+0325 ring below"), ("Aring", "Å (ring merged with the apex)")):
            L.append(rf"\subsection*{{{LABEL[style]}: {label}}}")
            L.append(r"\begin{tabular}{" + "p{8.4cm}" * len(versions) + "}")
            L.append(" & ".join(v for v, _ in versions) + r" \\")
            figs, tabs = [], []
            for _, path in versions:
                rec = _recording(path, glyph)
                if glyph == "Aring":
                    counter = _clip_contours(rec, (-1000, 600, 2000, 1000))   # the only contour wholly above 600
                    xs = [p[0] for o, a in counter for p in a]
                    ys = [p[1] for o, a in counter for p in a]
                    box = (min(xs) - 110, min(ys) - 75, max(xs) + 110, max(ys) + 50)
                    figs.append(tikz_outline(rec, 0.034, box))
                    tabs.append(r"{\fontsize{6}{7.5}\selectfont " + point_table(counter) + "}")
                else:
                    figs.append(tikz_outline(rec, 0.034))
                    tabs.append(r"{\fontsize{6}{7.5}\selectfont " + point_table(rec) + "}")
            L.append(" & ".join(figs) + r" \\")
            L.append(" & ".join(tabs) + r" \\")
            L.append(r"\end{tabular}")
            L.append(r"\clearpage")
    L.append(r"\end{document}")
    open("tex/ring_draft_sheet.tex", "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("wrote tex/ring_draft_sheet.tex")


if __name__ == "__main__":
    main()
