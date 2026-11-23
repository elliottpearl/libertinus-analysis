# dot_lookup_sheet.py
"""
Test sheet of the dot lookup (stage 9b, font_patching_dotanchors.py):
tex/dot_lookup_test_sheet.tex, run by run_dot_lookup_sheet.py after
run_patch_font.py.

Candidates: every lowercase letter of BASE_LATIN ∪ BASE_IPA whose main
above anchor is at the ascender reference, or below anchor at the descender
reference, in some style, plus the letters listed in data/dot_letters.py.
For each, in every style, the sheet sets the dot and the vertical line
(U+0307 / U+030D above, U+0323 / U+0329 below) with CGJ, as the main lookup
places them and as the dot lookup would, with the gap of each mark to the
letter (red under the style's MIN_GAP, the designer's closest dot in ḃ ḋ ḣ).

Two variant fonts per style are written to fonts/:
    *-nodot.otf     the patched font with the dot lookup left out of `mark`
                    (the main lookup's positions);
    *-dotcand.otf   the patched font with a dot lookup for every candidate,
                    the vertical lines in it too.
"""

import copy
import unicodedata as ud
from pathlib import Path

from fontTools.ttLib import TTFont

from .font_context import FONTS
from .fontmetrics_helpers import ANCHOR_Y_REF_OPT
from . import font_patching_dotanchors as D
from .font_naming import save_renamed

STYLES = ["regular", "italic", "semibold", "semibold_italic"]
LABEL = {"regular": "Regular", "italic": "Italic", "semibold": "Semibold", "semibold_italic": "Semibold italic"}
SHAPE = {"regular": "", "italic": r"\itshape", "semibold": r"\bfseries", "semibold_italic": r"\bfseries\itshape"}
OUT = Path("tex/dot_lookup_test_sheet.tex")


def _candidates():
    """{side: [codepoints]}: lowercase letters with a main anchor at the ascender / descender reference."""
    import sys
    sys.path.insert(0, ".")
    from data.ipa.ipa_unicode import unicode_groups as G
    data = D.load_dot_letters()
    cps = sorted(set(G["BASE_LATIN"]["items"]) | set(G["BASE_IPA"]["items"]))
    cps = [c for c in cps if ud.category(chr(c)) == "Ll"]
    out = {0: set(data.DOT_ABOVE), 2: set(data.DOT_BELOW)}
    for style in STYLES:
        meta = FONTS[style + "_patch"]
        f = TTFont(str(meta["path"]))
        cmap = f.getBestCmap()
        sub = D.find_mark_to_base_subtables(f, meta["lookup_index"])[0]
        bc = sub.BaseCoverage.glyphs
        for c in cps:
            g = cmap.get(c)
            if g not in bc:
                continue
            rec = sub.BaseArray.BaseRecord[bc.index(g)].BaseAnchor
            for side, test in ((0, lambda y: y >= 860), (2, lambda y: y <= -300)):
                a = rec[side] if side < len(rec) else None
                if a is not None and test(a.YCoordinate):
                    out[side].add(c)
    listed = {0: data.DOT_ABOVE, 2: data.DOT_BELOW}
    # listed letters first, in their order; then the rest by codepoint
    return {s: list(listed[s]) + sorted(out[s] - set(listed[s])) for s in (0, 2)}


def _variant_fonts(style, letters):
    """Write *-nodot.otf and *-dotcand.otf; return (info, anchors, min_gap, mark anchors) of the candidates."""
    meta = FONTS[style + "_patch"]
    path, main = meta["path"], meta["lookup_index"]

    f = TTFont(str(path))
    idx = D.dot_lookup_index(f, main)
    gpos = f["GPOS"].table
    for fr in gpos.FeatureList.FeatureRecord:
        if fr.FeatureTag == "mark" and idx in fr.Feature.LookupListIndex:
            fr.Feature.LookupListIndex.remove(idx)
            fr.Feature.LookupCount = len(fr.Feature.LookupListIndex)
    save_renamed(f, path.with_name(path.stem + "-nodot.otf"))

    f = TTFont(str(path))
    anchors, info, _ = D.dot_anchors(f, style + "_patch", main, letters=letters)
    D.build_dot_lookup(f, main, anchors, lines=(True, True))
    save_renamed(f, path.with_name(path.stem + "-dotcand.otf"))

    cmap = f.getBestCmap()
    marks = {cp: D.main_mark_anchor(f, main, cmap[cp]) for cp in (0x0307, 0x030D, 0x0323, 0x0329)}
    gaps = {}
    for (g, side), (x, y) in anchors.items():
        base = D._Base(f, g)
        for cp in (D.DOT_MARK[side], D.LINE_MARK[side]):
            gaps[(g, cp)] = D.mark_gap(f, base, cmap[cp], marks[cp], (x, y))
    # the vertical lines are judged by their own gap on o (main lookup), not by the dot's MIN_GAP
    sub = D.find_mark_to_base_subtables(f, main)[0]
    rec = sub.BaseArray.BaseRecord[sub.BaseCoverage.glyphs.index("o")].BaseAnchor
    o = D._Base(f, "o")
    line_ref = {side: D.mark_gap(f, o, cmap[D.LINE_MARK[side]], marks[D.LINE_MARK[side]],
                                 (rec[side].XCoordinate, rec[side].YCoordinate)) for side in (0, 2)}
    return info, anchors, D.min_gap(f), gaps, cmap, line_ref


def _tex_char(cp):
    return f'\\char"{cp:04X}'


def _sample(fam, style, cp, marks):
    s = r"\,\,".join(f"{_tex_char(cp)}\\cgj{_tex_char(m)}" for m in marks)
    return f"{{{fam}{SHAPE[style]}\\fontsize{{24}}{{30}}\\selectfont {s}}}"


TOL = 6   # a dot within this of MIN_GAP passes


def _passes(style_data, cp, side):
    """Whether the dot of cp is clear in this style: a position over the body, gap at least MIN_GAP - TOL or the designer's own."""
    info, anchors, need, gaps, cmap, line_ref = style_data
    d = info.get((cmap.get(cp), side))
    if d is None or (cmap.get(cp), side) not in anchors:
        return False
    return d["source"] == "precomposed" or d["gap"] >= need - TOL


def _cell(style_data, st, cp, side, marks):
    """One style's cell: main lookup -> dot lookup (dot, line), then gaps and source."""
    info, anchors, need, gaps, cmap, line_ref = style_data
    g = cmap.get(cp)
    d = info.get((g, side))
    sh = SHAPE[st]
    size = r"\fontsize{16}{19}\selectfont "
    main = "{\\FMain" + sh + size + f"{_tex_char(cp)}\\cgj{_tex_char(marks[0])}" + "}"
    if g is None or d is None:
        return r"{\scriptsize not in font}"
    if (g, side) not in anchors:
        return main + r"\ $\to$ --\newline{\scriptsize best gap " + str(max(d["gap"], 0)) + "}"
    dot = "{\\FDot" + sh + size + f"{_tex_char(cp)}\\cgj{_tex_char(marks[0])}\\,\\,{_tex_char(cp)}\\cgj{_tex_char(marks[1])}" + "}"
    src = d["source"] + (f", {d['note']}" if d["note"] and d["source"] != "precomposed" else "")
    src = src.replace("%", r"\%").replace("_", r"\_")
    info_line = (rf"{{\scriptsize dot {_gap(gaps.get((g, marks[0])), need)}, line {_gap(gaps.get((g, marks[1])), line_ref[side])}; "
                 rf"x {anchors[(g, side)][0]}, {src}}}")
    return main + r"\ $\to$ " + dot + r"\newline" + info_line


def _gap(g, need):
    if g is None:
        return "--"
    return f"\\textcolor{{under}}{{{g}}}" if g < need else str(g)


def write_dot_lookup_sheet():
    data = D.load_dot_letters()
    cands = _candidates()
    listed = {0: set(data.DOT_ABOVE), 2: set(data.DOT_BELOW)}
    per_style = {st: _variant_fonts(st, cands) for st in STYLES}

    L = [r"""% Generated by run_dot_lookup_sheet.py; do not edit.
\documentclass[10pt]{article}
\usepackage{fontspec}\usepackage{geometry}\usepackage{xcolor}\usepackage{longtable}\usepackage{array}
\geometry{a4paper,landscape,left=1cm,right=1cm,top=1cm,bottom=1.2cm}
\setlength{\parindent}{0pt}\setlength{\parskip}{2pt}
\setmainfont{LibertinusSerif-Regular.otf}[Path=../fonts/, BoldFont=LibertinusSerif-Semibold.otf, ItalicFont=LibertinusSerif-Italic.otf, BoldItalicFont=LibertinusSerif-SemiboldItalic.otf]
\newcommand{\cgj}{\char"034F }
\definecolor{dim}{RGB}{110,110,110}\definecolor{under}{RGB}{225,0,0}
\newfontfamily\FMain[Path=../fonts/, UprightFont=LibertinusSerif-Regular-patch-nodot.otf, BoldFont=LibertinusSerif-Semibold-patch-nodot.otf, ItalicFont=LibertinusSerif-Italic-patch-nodot.otf, BoldItalicFont=LibertinusSerif-SemiboldItalic-patch-nodot.otf]{Libertinus Main}
\newfontfamily\FDot[Path=../fonts/, UprightFont=LibertinusSerif-Regular-patch-dotcand.otf, BoldFont=LibertinusSerif-Semibold-patch-dotcand.otf, ItalicFont=LibertinusSerif-Italic-patch-dotcand.otf, BoldItalicFont=LibertinusSerif-SemiboldItalic-patch-dotcand.otf]{Libertinus Dot}
\newfontfamily\FOrig[Path=../fonts/, UprightFont=LibertinusSerif-Regular.otf, BoldFont=LibertinusSerif-Semibold.otf, ItalicFont=LibertinusSerif-Italic.otf, BoldItalicFont=LibertinusSerif-SemiboldItalic.otf]{Libertinus Orig}
\newfontfamily\FPatch[Path=../fonts/, UprightFont=LibertinusSerif-Regular-patch.otf, BoldFont=LibertinusSerif-Semibold-patch.otf, ItalicFont=LibertinusSerif-Italic-patch.otf, BoldItalicFont=LibertinusSerif-SemiboldItalic-patch.otf]{Libertinus Patch}
\begin{document}
\section*{Test sheet: the dot lookup (stage 9b)}
For the letters in data/dot\_letters.py the dot lookup puts the dot above (U+0307, with the vertical line U+030D) at the x-height reference and the dot below (U+0323) at the baseline reference, as the designer drew ḃ ḋ ḣ and ỵ, instead of the main lookup's ascender or descender reference.
$X$ is the designer's, from the precomposed letter (\emph{precomposed}); the base letter's, for a derived letter (\emph{derived}); or the centre of the letter's x-height body, pushed sideways until the dot is at least MIN\_GAP from the letter (\emph{model}), MIN\_GAP being the gap of the designer's closest dot in ḃ ḋ ḣ.
A letter is added only if its dot is clear in all four styles (gap at least MIN\_GAP$-$6, or the designer's own position) and sits over the letter's body.

\emph{What to look at.} Section 1: every candidate (a lowercase Latin or IPA letter whose main anchor is at the ascender or descender reference in some style), in groups; only the group \emph{Open} needs a decision, and red gaps are the tight cases. Section 2: the letters with a hook, above and below, for decisions consistent across them. Section 3: what the patched font does. All samples use CGJ, so that no precomposed letter replaces them.
"""]

    L.append(r"\section*{1. The candidates, by group}")
    L.append(r"Each row is one letter in the four styles. In each cell: the dot as the main lookup places it, an arrow, "
             r"then the dot and the vertical line as the dot lookup places them; under it, the dot's gap and the line's gap "
             r"(\textcolor{under}{red}: dot under MIN\_GAP, line under its gap on o) and where X comes from. "
             r"A dash means the dot finds no clear position over the letter's body in that style.\par")
    for side, title, marks in ((0, "Above: U+0307, U+030D", (0x0307, 0x030D)),
                               (2, "Below: U+0323, U+0329", (0x0323, 0x0329))):
        excl = data.EXCLUDED_ABOVE if side == 0 else data.EXCLUDED_BELOW
        groups = {"in": [], "open": [], "excluded": [], "some": [], "none": []}
        for cp in cands[side]:
            ok = [_passes(per_style[st], cp, side) for st in STYLES]
            if cp in listed[side]:
                groups["in"].append(cp)
            elif cp in excl:
                groups["excluded"].append(cp)
            elif all(ok):
                groups["open"].append(cp)
            elif any(ok):
                groups["some"].append(cp)
            else:
                groups["none"].append(cp)
        L.append(rf"\section*{{{title}}}")
        heads = {
            "in": "In the dot lookup (data/dot\\_letters.py)",
            "open": "Open: clear in all four styles, not yet decided",
            "excluded": "Excluded by decision (reason in data/dot\\_letters.py)",
            "some": "Not added: clear in some styles only (the rule needs all four)",
        }
        for key in ("in", "open", "excluded", "some"):
            L.append(rf"\subsection*{{{heads[key]}}}")
            if not groups[key]:
                L.append(r"None.\par")
                continue
            L.append(r"\begin{longtable}{@{}>{\raggedright\arraybackslash}p{2.4cm} p{6cm} p{6cm} p{6cm} p{6cm}@{}}")
            L.append(r"letter & Regular & Italic & Semibold & Semibold italic \\ \hline \endhead")
            for cp in groups[key]:
                label = rf"{{\FPatch\fontsize{{14}}{{16}}\selectfont {_tex_char(cp)}}} {{\scriptsize\color{{dim}}U+{cp:04X}}}"
                if key == "excluded":
                    label += r"\newline{\scriptsize\color{dim} " + excl[cp][1].replace("_", r"\_").replace("&", r"\&") + "}"
                cells = [_cell(per_style[st], st, cp, side, marks) for st in STYLES]
                L.append(label + " & " + " & ".join(cells) + r" \\[8pt]")
            L.append(r"\end{longtable}")
        L.append(r"\subsection*{No clear position over the body in any style}")
        L.append(r"{\FPatch\fontsize{14}{16}\selectfont " + r"\ \ ".join(_tex_char(c) for c in groups["none"]) + r"}\par")

    # a family view: every candidate whose name says it has a hook, both sides, with its status
    hooked = sorted({c for side in (0, 2) for c in cands[side] if "HOOK" in ud.name(chr(c), "")})
    L.append(r"\clearpage\section*{2. Letters with a hook, above and below}")
    L.append(r"Every candidate whose Unicode name has HOOK, so that the decisions on them can be made together. "
             r"Each letter has two rows, above and below, with its status on that side: "
             r"\emph{in} (in the dot lookup), \emph{excluded}, \emph{some} (clear in some styles only), \emph{open}, \emph{none} (no clear position), "
             r"or \emph{--} (not a candidate on that side: its main anchor is not at the ascender or descender reference).\par")
    L.append(r"\begin{longtable}{@{}>{\raggedright\arraybackslash}p{2.4cm} p{6cm} p{6cm} p{6cm} p{6cm}@{}}")
    L.append(r"letter & Regular & Italic & Semibold & Semibold italic \\ \hline \endhead")
    for cp in hooked:
        for side, marks in ((0, (0x0307, 0x030D)), (2, (0x0323, 0x0329))):
            excl = data.EXCLUDED_ABOVE if side == 0 else data.EXCLUDED_BELOW
            if cp not in cands[side]:
                status = "--"
            elif cp in listed[side]:
                status = "in"
            elif cp in excl:
                status = "excluded"
            else:
                ok = [_passes(per_style[st], cp, side) for st in STYLES]
                status = "open" if all(ok) else "some" if any(ok) else "none"
            label = (rf"{{\FPatch\fontsize{{14}}{{16}}\selectfont {_tex_char(cp)}}} {{\scriptsize\color{{dim}}U+{cp:04X}}}"
                     rf"\newline{{\scriptsize {'above' if side == 0 else 'below'}: \textbf{{{status}}}}}")
            cells = ([_cell(per_style[st], st, cp, side, marks) for st in STYLES] if status != "--" else [""] * 4)
            L.append(label + " & " + " & ".join(cells) + (r" \\[8pt]" if side == 0 else r" \\[14pt] \hline"))
    L.append(r"\end{longtable}")

    # what the patched font itself does: listed letters and their precomposed letters
    L.append(r"\clearpage\section*{3. The patched font: listed letters and the precomposed letters that inherit}")
    L.append(r"Each letter with the dot (CGJ), in the patched font, all four styles.\par\medskip")
    for st in STYLES:
        meta = FONTS[st + "_patch"]
        owners_path = Path("data/anchor_provenance") / f"{st}_dot.json"
        import json
        owners = json.loads(owners_path.read_text(encoding="utf-8")) if owners_path.exists() else {}
        f = TTFont(str(meta["path"]))
        rev = {v: k for k, v in f.getBestCmap().items()}
        for side, mark in ((0, 0x0307), (2, 0x0323)):
            cps = [rev[g] for g, cl in owners.items() if str(side) in cl and g in rev]
            s = r"\,\,".join(f"{_tex_char(c)}\\cgj{_tex_char(mark)}" for c in cps)
            L.append(rf"{{\footnotesize {LABEL[st]}, {'above' if side == 0 else 'below'}:}} "
                     rf"{{\FPatch{SHAPE[st]}\fontsize{{20}}{{26}}\selectfont {s}}}\par")
    # the dot outlines of stage 2 (font_patching_dotoutlines.py)
    L.append(r"\clearpage\section*{4. The dot outlines (stage 2)}")
    L.append(r"U+0323 and the dot of ṃ take the precomposed letters' dot (U+02D9's); U+0324 takes the diaeresis of U+0308 and ṳ; "
             r"in the italic styles the dot of ỵ moves right (italic +52, semibold italic +12), and composed y, ɏ, ƴ follow it. "
             r"Each new outline keeps the old one's top edge and axis. "
             r"\emph{Overlay}: the original in \textcolor{under}{red} under the patched font in black. Composed samples with CGJ; "
             r"the precomposed ạ ṳ ỵ beside them for comparison.\par\medskip")
    seq = [(0x1EA1, None), (0x61, 0x323), (0x1E43, None), (0x70, 0x323), (0x71, 0x323),
           (0x1E73, None), (0x75, 0x324), (0x61, 0x324), (0x1EF5, None), (0x79, 0x323), (0x24F, 0x323), (0x1B4, 0x323)]
    text = r"\,\,".join(_tex_char(b) + (r"\cgj" + _tex_char(m) if m else "") for b, m in seq)
    L.append(r"\begin{tabular}{@{}l l@{}}")
    for st in STYLES:
        sz = r"\fontsize{26}{34}\selectfont "
        L.append(rf"\multicolumn{{2}}{{@{{}}l}}{{\textbf{{{LABEL[st]}}}}} \\")
        L.append(rf"original & {{\FOrig{SHAPE[st]}{sz}{text}}} \\")
        L.append(rf"patched & {{\FPatch{SHAPE[st]}{sz}{text}}} \\")
        L.append(rf"overlay & {{{sz}\makebox[0pt][l]{{\color{{under}}\FOrig{SHAPE[st]} {text}}}\FPatch{SHAPE[st]} {text}}} \\[6pt]")
    L.append(r"\end{tabular}")
    L.append(r"\end{document}")
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
