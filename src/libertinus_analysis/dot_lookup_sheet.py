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
    f.save(str(path.with_name(path.stem + "-nodot.otf")))

    f = TTFont(str(path))
    anchors, info, _ = D.dot_anchors(f, style + "_patch", main, letters=letters)
    D.build_dot_lookup(f, main, anchors, lines=(True, True))
    f.save(str(path.with_name(path.stem + "-dotcand.otf")))

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


def _tight_section():
    """
    Section 1 of the sheet: every dot (and vertical line, where it is in the
    dot lookup) of the patched font closer to its letter than the designer's
    closest dot, set large beside that designer letter.
    """
    data = D.load_dot_letters()
    lines_on = {0: data.LINE_ABOVE, 2: data.LINE_BELOW}
    L = [r"\section*{1. The tight cases in the patched font}",
         r"Every dot of the patched font's dot lookup (listed letters, their derived letters, and the precomposed letters that inherit) "
         r"whose gap to the letter is under MIN\_GAP, the gap of the designer's closest dot above among ḃ ḋ ḣ; and every vertical line in the dot lookup "
         r"whose gap is under its own gap on o. Each is set large beside the designer's letters for comparison: "
         r"the closest of ḃ ḋ ḣ, and ỵ (below). Gaps in font units (at 10\,pt, 10 units are 0.1\,pt); "
         r"under each large sample, the same at 11\,pt in a short word. "
         r"Within about 5 of MIN\_GAP is noise; under about 20 the dot can read as part of the letter.\par\medskip"]
    for st in STYLES:
        meta = FONTS[st + "_patch"]
        f = TTFont(str(meta["path"]))
        main = meta["lookup_index"]
        cmap = f.getBestCmap()
        need = D.min_gap(f)
        anchors, info, _ = D.dot_anchors(f, st + "_patch", main)
        sub = D.find_mark_to_base_subtables(f, main)[0]
        rec = sub.BaseArray.BaseRecord[sub.BaseCoverage.glyphs.index("o")].BaseAnchor
        o = D._Base(f, "o")
        refs = {0: min(D.GAP_LETTERS, key=lambda cp: D.designer_gap(f, cmap[cp], 0)), 2: 0x1EF5}
        ref_gap = {side: D.designer_gap(f, cmap[refs[side]], side) for side in (0, 2)}
        cases = {}   # (cp, side, mark) -> [gap, limit, source, [inheriting letters]]
        found = []
        for (g, side), (x, y) in anchors.items():
            d = info[(g, side)]
            if d["gap"] < need:
                found.append((d["cp"], side, D.DOT_MARK[side], d["gap"], need, d))
            if lines_on[side]:
                lm = D.LINE_MARK[side]
                lxy = D.main_mark_anchor(f, main, cmap[lm])
                lref = D.mark_gap(f, o, cmap[lm], lxy, (rec[side].XCoordinate, rec[side].YCoordinate))
                lg = D.mark_gap(f, D._Base(f, g), cmap[lm], lxy, (x, y))
                if lg < lref:
                    found.append((d["cp"], side, lm, lg, lref, d))
        # a precomposed letter that inherits the same gap as its base letter goes into the base's cell
        for cp, side, mark, gap, lim, d in sorted(found, key=lambda c: c[5]["source"] == "inherited"):
            if d["source"] == "inherited":
                base_cp = ord(d["note"].split("from ")[1][0])
                key = (base_cp, side, mark)
                if key in cases and abs(cases[key][0] - gap) <= 1:
                    cases[key][3].append(chr(cp))
                    continue
            cases[(cp, side, mark)] = [gap, lim, d["source"], []]
        cases = sorted(((k, v) for k, v in cases.items()), key=lambda kv: kv[1][0])
        big = rf"\FPatch{SHAPE[st]}\fontsize{{56}}{{64}}\selectfont "
        small = rf"\FPatch{SHAPE[st]}\fontsize{{11}}{{13}}\selectfont "

        def cell(text, ctx, label):
            return (rf"\begin{{tabular}}[b]{{@{{}}c@{{}}}}{{{big}{text}}}\\{{{small}{ctx}}}\\"
                    rf"{{\footnotesize\begin{{tabular}}{{@{{}}c@{{}}}}{label}\end{{tabular}}}}\end{{tabular}}\hspace{{1.2em}}")

        L.append(rf"\subsection*{{{LABEL[st]} (MIN\_GAP {need})}}")
        row = [cell(_tex_char(refs[0]), "a" + _tex_char(refs[0]) + "a", rf"designer {chr(refs[0])}: dot {ref_gap[0]}"),
               cell(_tex_char(refs[2]), "a" + _tex_char(refs[2]) + "a", rf"designer {chr(refs[2])}: dot {ref_gap[2]}")]
        for (cp, side, mark), (gap, lim, src, also) in cases:
            t = f"{_tex_char(cp)}\\cgj{_tex_char(mark)}"
            what = "dot" if mark in D.DOT_MARK.values() else "line"
            limit = f"MIN\\_GAP {lim}" if what == "dot" else f"{lim} on o"
            label = rf"{what} \textcolor{{under}}{{{gap}}} ({limit}); {src}"
            if also:
                label += r"\\ also " + " ".join(also)
            row.append(cell(t, "a" + t + "a", label))
        if not cases:
            row.append(r"{\footnotesize none}")
        L.append(r"{\raggedright\noindent" + "".join(row) + r"\par}\medskip")
    L.append(r"\clearpage")
    return L


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
\newfontfamily\FPatch[Path=../fonts/, UprightFont=LibertinusSerif-Regular-patch.otf, BoldFont=LibertinusSerif-Semibold-patch.otf, ItalicFont=LibertinusSerif-Italic-patch.otf, BoldItalicFont=LibertinusSerif-SemiboldItalic-patch.otf]{Libertinus Patch}
\begin{document}
\section*{Test sheet: the dot lookup (stage 9b)}
For the letters in data/dot\_letters.py the dot lookup puts the dot above (U+0307, with the vertical line U+030D) at the x-height reference and the dot below (U+0323) at the baseline reference, as the designer drew ḃ ḋ ḣ and ỵ, instead of the main lookup's ascender or descender reference.
$X$ is the designer's, from the precomposed letter (\emph{precomposed}); the base letter's, for a derived letter (\emph{derived}); or the centre of the letter's x-height body, pushed sideways until the dot is at least MIN\_GAP from the letter (\emph{model}), MIN\_GAP being the gap of the designer's closest dot in ḃ ḋ ḣ.
A letter is added only if its dot is clear in all four styles (gap at least MIN\_GAP$-$6, or the designer's own position) and sits over the letter's body.

\emph{What to look at.} Section 1: the dots of the patched font that are closer to their letter than MIN\_GAP, beside the designer's letters. Section 2: every candidate (a lowercase Latin or IPA letter whose main anchor is at the ascender or descender reference in some style), in groups; only the group \emph{Open} needs a decision. All samples use CGJ, so that no precomposed letter replaces them.
"""]

    L.extend(_tight_section())
    L.append(r"\clearpage\section*{2. The candidates, by group}")
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

    # what the patched font itself does: listed letters and their precomposed letters
    L.append(r"\section*{The patched font: listed letters and the precomposed letters that inherit}")
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
    L.append(r"\end{document}")
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
