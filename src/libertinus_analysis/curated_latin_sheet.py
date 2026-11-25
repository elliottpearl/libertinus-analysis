# curated_latin_sheet.py
"""
Test sheet for the review of the curated base anchors of A-Z a-z
(stage 7, data/fontanchors_human/{style}.py): tex/curated_latin_test_sheet.tex,
run by run_curated_latin_sheet.py after run_patch_font.py.

Rows: every (letter, class) whose final owner (data/anchor_provenance) is
"curated" in at least one style; each row shows all four styles, so that a
letter curated in one style can be compared with the others.

Two variant fonts per style are written to fonts/ by patch_font itself, with
the curated A-Z a-z base anchors of those rows left out of stage 7:
    *-patch-nocur.otf   what the other stages give if the curated entry is
                        removed: the designer's anchor (after stage 5), or
                        the stage-6 candidate where there is none;
    *-patch-cand.otf    the same, with the designer's anchor deleted in
                        stage 1 as well, so stage 6 sets the candidate
                        (the "delete + candidate" route).
The stem-axis rule (7b) still runs in both, so i j l m I T keep their stem X.
"""

import contextlib
import copy
import importlib
import io
import json
import re
import string
import tempfile
import unicodedata as ud
from pathlib import Path

from fontTools.ttLib import TTFont

from .font_context import FONTS
from . import font_patching as FP
from . import font_patching_anchors as FPA
from . import font_patching_derivedanchors as FPD
from . import font_patching_markaxis as FPM
from . import font_patching_precomposed_anchors as FPP
from . import font_patching_stemaxis as FPS
from .font_patching_dotanchors import find_mark_to_base_subtables

STYLES = ["regular", "italic", "semibold", "semibold_italic"]
LABEL = {"regular": "Regular", "italic": "Italic", "semibold": "Semibold", "semibold_italic": "Semibold italic"}
SHAPE = {"regular": "", "italic": r"\itshape", "semibold": r"\bfseries", "semibold_italic": r"\bfseries\itshape"}
LETTERS = [ord(c) for c in string.ascii_uppercase + string.ascii_lowercase]
MARKS = {0: [0x0302, 0x0303, 0x0304, 0x0308, 0x030C, 0x030A],
         2: [0x0325, 0x0331, 0x0330, 0x032D, 0x0324, 0x032F]}
VARIANTS = ("nocur", "cand")
NEAR = 10   # a variant within this of the current anchor, in X and Y, reproduces it
OUT = Path("tex/curated_latin_test_sheet.tex")
PROV = Path("data/anchor_provenance")


def curated_rows():
    """[(cp, cls)] whose final owner is curated in some style, above first."""
    rows = set()
    for st in STYLES:
        p = json.loads((PROV / f"{st}.json").read_text(encoding="utf-8"))
        for cp in LETTERS:
            for c, o in p.get(chr(cp), {}).items():
                if o == "curated":
                    rows.add((cp, int(c)))
    return sorted(rows, key=lambda r: (r[1], LETTERS.index(r[0])))


def _comments(style):
    """{(cp, cls): comment} from data/fontanchors_human/{style}.py: the entry's header comment and the class line's."""
    out, key, head = {}, None, []
    for line in Path(f"data/fontanchors_human/{style}.py").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*(0x[0-9A-Fa-f]+)\s*:\s*\{\s*(?:#\s*(.*))?$", line)
        if m:
            key, head = int(m.group(1), 16), [m.group(2)] if m.group(2) else []
            continue
        if key is None:
            continue
        m = re.match(r"^\s*([0-3])\s*:\s*\(([^)]*)\)\s*,?\s*(?:#\s*(.*))?$", line)
        if m:
            out[(key, int(m.group(1)))] = " ".join(head + ([m.group(3)] if m.group(3) else []))
            continue
        m = re.match(r"^\s*#\s*(.*)$", line)
        if m and not re.match(r"^\s*#\s*[0-3]\s*:", line) and not re.match(r"^\s*#\s*0x", line):
            if not any(k[0] == key for k in out):   # still in the header
                head.append(m.group(1))
            continue
        if re.match(r"^\s*\},?\s*$", line):
            key = None
    return out


@contextlib.contextmanager
def _without_curated(rows):
    """Patch load_human_anchors everywhere so that the rows' curated base anchors are left out."""
    original = FPA.load_human_anchors
    drop = set(rows)

    def load(font_key):
        human = copy.deepcopy(original(font_key))
        bases = human.get("bases", {})
        for cp in list(bases):
            for c in list(bases[cp]):
                if (cp, c) in drop:
                    del bases[cp][c]
            if not bases[cp]:
                del bases[cp]
        return human

    mods = [FP, FPA, FPD, FPM, FPP, FPS]
    saved = [(m, m.load_human_anchors) for m in mods]
    for m in mods:
        m.load_human_anchors = load
    try:
        yield
    finally:
        for m, f in saved:
            m.load_human_anchors = f


def _build_variants(rows):
    """Write the two variant fonts per style; return {(style, variant): provenance}."""
    prov = {}
    saved_dir = FP.PROVENANCE_DIR
    with tempfile.TemporaryDirectory() as tmp, _without_curated(rows):
        FP.PROVENANCE_DIR = Path(tmp)
        try:
            for st in STYLES:
                src = TTFont(str(FONTS[st]["path"]))
                cmap = src.getBestCmap()
                patch = FONTS[st + "_patch"]["path"]
                for v in VARIANTS:
                    extra = frozenset((cmap[cp], c) for cp, c in rows if cp in cmap) if v == "cand" else frozenset()
                    out = patch.with_name(f"{patch.stem}-{v}.otf")
                    with contextlib.redirect_stdout(io.StringIO()):
                        FP.patch_font(st, output_path=out, extra_deletions=extra)
                    prov[(st, v)] = json.loads((Path(tmp) / f"{st}.json").read_text(encoding="utf-8"))
                    print(f"wrote {out}")
        finally:
            FP.PROVENANCE_DIR = saved_dir
    return prov


def _anchors(path, lookup_index):
    f = TTFont(str(path))
    cmap = f.getBestCmap()
    sub = find_mark_to_base_subtables(f, lookup_index)[0]
    bc = sub.BaseCoverage.glyphs
    out = {}
    for cp in LETTERS:
        g = cmap.get(cp)
        if g in bc:
            for c, a in enumerate(sub.BaseArray.BaseRecord[bc.index(g)].BaseAnchor):
                if a is not None:
                    out[(cp, c)] = (a.XCoordinate, a.YCoordinate)
    return out, cmap


def _ch(cp):
    return f'\\char"{cp:04X}'


def _esc(s):
    return (s.replace("\\", r"\textbackslash{}").replace("_", r"\_").replace("%", r"\%").replace("&", r"\&")
            .replace("#", r"\#").replace("$", r"\$").replace("~", r"\~{}").replace("^", r"\^{}"))


def _samples(fam, st, cp, marks, cmap=None, precomposed=False):
    box = []
    for m in marks:
        if precomposed:
            pc = ud.normalize("NFC", chr(cp) + chr(m))
            s = _ch(ord(pc)) if len(pc) == 1 and ord(pc) in cmap else ""
        else:
            s = f"{_ch(cp)}\\cgj{_ch(m)}"
        box.append(rf"\makebox[1.15em][c]{{{s}}}")
    return f"{{{fam}{SHAPE[st]}\\fontsize{{15}}{{19}}\\selectfont " + "".join(box) + "}"


def _near(a, b):
    return a is not None and b is not None and abs(a[0] - b[0]) <= NEAR and abs(a[1] - b[1]) <= NEAR


def _xy(a):
    return "--" if a is None else f"{a[0]},{a[1]}"


def _delta(a, ref):
    if a is None or ref is None:
        return ""
    dx, dy = a[0] - ref[0], a[1] - ref[1]
    if dx == 0 and dy == 0:
        return "="
    return f"{dx:+d}/{dy:+d}"


OWNER_ABBR = {"designer": "des", "normalized": "des (norm.)", "heuristic": "cand", "curated": "CUR",
              "stem": "stem", "derived": "derived", "precomposed": "precomp"}


def write_curated_latin_sheet():
    rows = curated_rows()
    prov = _build_variants(rows)
    owners = {st: json.loads((PROV / f"{st}.json").read_text(encoding="utf-8")) for st in STYLES}
    comments = {st: _comments(st) for st in STYLES}
    data, cmaps = {}, {}
    for st in STYLES:
        meta = FONTS[st + "_patch"]
        data[(st, "patch")], cmaps[st] = _anchors(meta["path"], meta["lookup_index"])
        for v in VARIANTS:
            data[(st, v)], _ = _anchors(meta["path"].with_name(f"{meta['path'].stem}-{v}.otf"), meta["lookup_index"])

    def owner(st, key, cp, c):
        o = (owners[st] if key == "patch" else prov[(st, key)]).get(chr(cp), {}).get(str(c))
        return OWNER_ABBR.get(o, o or "--")

    fam = {"patch": r"\FPatch", "nocur": r"\FNoCur", "cand": r"\FCand"}
    fonts = {k: {st: (FONTS[st + "_patch"]["path"].name if k == "patch"
                      else FONTS[st + "_patch"]["path"].with_name(f"{FONTS[st + '_patch']['path'].stem}-{k}.otf").name)
                 for st in STYLES} for k in fam}

    L = [r"""% Generated by run_curated_latin_sheet.py; do not edit.
\documentclass[10pt]{article}
\usepackage{fontspec}\usepackage{geometry}\usepackage{xcolor}\usepackage{longtable}\usepackage{array}
\geometry{a4paper,landscape,left=1cm,right=1cm,top=1cm,bottom=1.2cm}
\setlength{\parindent}{0pt}\setlength{\parskip}{2pt}
\setmainfont{LibertinusSerif-Regular.otf}[Path=../fonts/, BoldFont=LibertinusSerif-Semibold.otf, ItalicFont=LibertinusSerif-Italic.otf, BoldItalicFont=LibertinusSerif-SemiboldItalic.otf]
\newcommand{\cgj}{\char"034F }
\definecolor{dim}{RGB}{110,110,110}\definecolor{cur}{RGB}{190,0,0}\definecolor{ok}{RGB}{0,130,40}"""]
    for k, f in fam.items():
        fs = fonts[k]
        L.append(rf"\newfontfamily{f}[Path=../fonts/, UprightFont={fs['regular']}, BoldFont={fs['semibold']}, "
                 rf"ItalicFont={fs['italic']}, BoldItalicFont={fs['semibold_italic']}]{{Libertinus {k}}}")
    L.append(r"""\begin{document}
\section*{Test sheet: the curated base anchors of A--Z, a--z}
Every letter and class (above, below) whose anchor is curated (stage 7) in at least one style, shown in all four styles, so that a letter curated in one style can be compared with the others.
In each cell, four lines, each with the marks """ + " ".join(f"U+{m:04X}" for m in MARKS[0]) + r""" (above) or """ + " ".join(f"U+{m:04X}" for m in MARKS[2]) + r""" (below), composed with CGJ:
\begin{description}\setlength{\itemsep}{0pt}
\item[patch] the patched font, with the anchor's owner (\textcolor{cur}{\textbf{CUR}}: curated; des: designer; des (norm.): designer, Y moved in stage 5; cand: stage-6 candidate; stem: the stem-axis rule, 7b) and its (x, y);
\item[no curated] the patch with this curated entry removed: the designer's anchor, or the candidate where the designer has none; with its owner and its difference from the patch (dx/dy);
\item[candidate] the patch with the curated entry removed and the designer's anchor deleted in stage 1, so that stage 6 sets the candidate (the ``delete + candidate'' route);
\item[precomp.] the precomposed letter, where one exists for that mark (HarfBuzz uses it in real text; the criterion for a composed combination).
\end{description}
\textcolor{ok}{\textbf{≈}}: within """ + str(NEAR) + r""" units of the patch in X and Y (that stage reproduces the anchor). The stem-axis rule still runs in the variants, so the X of i j l m I T is on the stem in all three.
Capitals take the .cap accents through ccmp wherever they exist. The dot above and dot below are left out: the dot lookup (stage 9b) places them for some letters.
Section 1 is a summary in numbers; section 2 the samples; section 3 the reason each curated anchor gives in data/fontanchors\_human.
""")

    # 1. summary
    L.append(r"\section*{1. Summary}")
    L.append(r"Per style: owner in the patch; the patch's (x, y); the difference of the \emph{no curated} and \emph{candidate} variants from it. "
             r"\textcolor{ok}{≈}: within " + str(NEAR) + r" in X and Y.\par\smallskip")
    L.append(r"{\footnotesize\begin{longtable}{@{}l " + " l" * 4 + r"@{}}")
    L.append(r"letter & " + " & ".join(LABEL[st] for st in STYLES) + r" \\ \hline \endhead")
    for cp, c in rows:
        cells = []
        for st in STYLES:
            p = data[(st, "patch")].get((cp, c))
            o = owner(st, "patch", cp, c)
            oo = rf"\textcolor{{cur}}{{\textbf{{{o}}}}}" if o == "CUR" else o
            parts = [f"{oo} {_xy(p)}"]
            for v, lab in (("nocur", "nc"), ("cand", "ca")):
                a = data[(st, v)].get((cp, c))
                mark = r"\textcolor{ok}{≈}" if _near(a, p) else ""
                parts.append(f"{lab} {_delta(a, p) or _xy(a)}{mark}")
            cells.append("; ".join(parts))
        L.append(rf"{{\FPatch\normalsize {_ch(cp)}}} {'above' if c == 0 else 'below'} & " + " & ".join(cells) + r" \\")
    L.append(r"\end{longtable}}")

    # 2. samples
    L.append(r"\clearpage\section*{2. Samples}")
    L.append(r"\begin{longtable}{@{}>{\raggedright\arraybackslash}p{1.6cm} p{6.0cm} p{6.0cm} p{6.0cm} p{6.0cm}@{}}")
    L.append(r"letter & Regular & Italic & Semibold & Semibold italic \\ \hline \endhead")
    for cp, c in rows:
        cells = []
        for st in STYLES:
            p = data[(st, "patch")].get((cp, c))
            lines = []
            for key, lab in (("patch", "patch"), ("nocur", "no cur."), ("cand", "cand.")):
                a = data[(st, key)].get((cp, c))
                o = owner(st, key, cp, c)
                o = rf"\textcolor{{cur}}{{\textbf{{{o}}}}}" if o == "CUR" else o
                info = f"{o} {_xy(a)}" if key == "patch" else f"{o} {_delta(a, p) or _xy(a)}"
                if key != "patch" and _near(a, p):
                    info += r" \textcolor{ok}{\textbf{≈}}"
                lines.append(rf"\parbox[b]{{1.55cm}}{{\tiny {lab}\\ {info}}}{_samples(fam[key], st, cp, MARKS[c])}")
            pre = _samples(fam["patch"], st, cp, MARKS[c], cmaps[st], precomposed=True)
            lines.append(rf"\parbox[b]{{1.55cm}}{{\tiny precomp.}}{pre}")
            cells.append(r"\par\vspace{7pt}".join(lines))
        label = rf"{{\FPatch\fontsize{{20}}{{24}}\selectfont {_ch(cp)}}}\newline{{\scriptsize {'above' if c == 0 else 'below'}}}"
        L.append(label + " & " + " & ".join(cells) + r" \\[6pt] \hline")
    L.append(r"\end{longtable}")

    # 3. reasons
    L.append(r"\clearpage\section*{3. The curators' reasons}")
    L.append(r"The comments of each curated entry in data/fontanchors\_human/\{style\}.py (header and class line), for the rows of this sheet; "
             r"a dash where the anchor is not curated in that style.\par\smallskip")
    L.append(r"{\footnotesize\begin{longtable}{@{}p{1.2cm} p{6.1cm} p{6.1cm} p{6.1cm} p{6.1cm}@{}}")
    L.append(r"letter & " + " & ".join(LABEL[st] for st in STYLES) + r" \\ \hline \endhead")
    for cp, c in rows:
        cells = []
        for st in STYLES:
            if owner(st, "patch", cp, c) != "CUR":
                cells.append("--")
            else:
                cells.append(_esc(comments[st].get((cp, c), "(no comment)")) or "(no comment)")
        L.append(rf"{{\FPatch\normalsize {_ch(cp)}}} {'above' if c == 0 else 'below'} & " + " & ".join(cells) + r" \\[3pt]")
    L.append(r"\end{longtable}}")
    L.append(r"\end{document}")
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    return rows, data, owners, prov
