"""
Test sheet of the base + combining mark combos found in a PDF set in the
original Libertinus Serif, original vs patched fonts.

    .venv/bin/python run_pdf_combo_sheet.py [PDF ...]   (default: data/legacy-fontdata/614.pdf)
    cd tex && xelatex pdf_combos_{stem}.tex && xelatex pdf_combos_{stem}.tex   (twice: longtable widths)

One report per PDF, tex/pdf_combos_{stem}.tex. Notes from reading a PDF in
context (typos, reproductions of what the patch does not cover) are in
data/pdf_combo_notes.py, keyed by the PDF's file stem.

Method: `mutool draw -F stext` dumps every glyph of the PDF with its font,
Unicode (ToUnicode) and origin (about a second for 366 pages). Each base +
following combining marks is a combo, keyed by the font name of the base
(LibertinusSerif-Regular/-Italic/-Semibold/-SemiboldItalic = the style).
Each distinct combo is shaped with HarfBuzz in the original and the patched
font of its style: the original's mark position is checked against the
position printed in the PDF (they agree when the PDF was set with the same
fonts), and the patch's move of each mark is measured. A combo is suspect if
the original font has no anchor for it (the mark is not attached and sits
where its outline is drawn, after the base's advance) or if the patch moves
a mark by at least MIN_MOVE units. One word per combo (the first in the PDF)
is set in the sheet, each character in the font the PDF used for it, with
the PDF page (1-based physical page, not the book's pagination).
"""
import re
import subprocess
import sys
import tempfile
import unicodedata as ud
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import uharfbuzz as hb
from fontTools.ttLib import TTFont

sys.path.insert(0, "src")
sys.path.insert(0, ".")
from libertinus_analysis.font_context import FONTS  # noqa: E402
from data.pdf_combo_notes import PDF_NOTES  # noqa: E402

PDFS = [Path(a) for a in sys.argv[1:]] or [Path("data/legacy-fontdata/614.pdf")]
MIN_MOVE = 10          # font units; smaller moves are listed, not set
STYLE = {"LibertinusSerif-Regular": "regular", "LibertinusSerif-Italic": "italic",
         "LibertinusSerif-Semibold": "semibold", "LibertinusSerif-SemiboldItalic": "semibold_italic"}
SHAPE = {"regular": r"\upshape\mdseries", "italic": r"\itshape\mdseries",
         "semibold": r"\upshape\bfseries", "semibold_italic": r"\itshape\bfseries"}
LABEL = {"regular": "Regular", "italic": "Italic", "semibold": "Semibold", "semibold_italic": "Semibold italic"}


def is_mark(c):
    return ud.category(c) in ("Mn", "Me")


# --- 1. read the PDF -------------------------------------------------------

# XML 1.0 forbids most C0 controls even as character references; mutool writes them.
BAD_REF = re.compile(rb"&#x(?:0*[0-8bcef]|0*1[0-9a-f]);", re.I)


def font_name(name):
    """LibertinusSerif-Regular from e.g. ABCDEF+LibertinusSerif-Regular-Identity-H."""
    return re.sub(r"-Identity-[HV]$", "", name.split("+")[-1])


def read_pdf(pdf):
    """Yield (page, [(char, font, x, y, size), ...]) per text line, and set PAGES."""
    global PAGES
    with tempfile.TemporaryDirectory() as tmp:
        xml = Path(tmp) / "p.xml"
        subprocess.run(["mutool", "draw", "-q", "-F", "stext", "-o", str(xml), str(pdf)],
                       check=True, stderr=subprocess.DEVNULL)
        xml.write_bytes(BAD_REF.sub(b"\xef\xbf\xbd", xml.read_bytes()))
        page, font, size, line = 0, None, None, []
        for ev, el in ET.iterparse(xml, events=("start", "end")):
            if ev == "start":
                if el.tag == "page":
                    page += 1
                elif el.tag == "font":
                    font, size = font_name(el.get("name")), float(el.get("size"))
            elif el.tag == "char":
                for ch in el.get("c"):
                    line.append((ch, font, float(el.get("x")), float(el.get("y")), size))
                el.clear()
            elif el.tag == "line":
                yield page, line
                line = []
            elif el.tag == "page":
                el.clear()
        PAGES = page


PAGES = 0


def collect(pdf):
    """combos[(font, base, marks, markfonts)] = {n, pages, pdf_dx, pdf_dy, word, page}."""
    combos = defaultdict(lambda: {"n": 0, "pages": [], "pdf": set(), "word": None, "page": None})
    for page, line in read_pdf(pdf):
        words, cur = [], []
        for t in line:
            if t[0].isspace():
                if cur:
                    words.append(cur)
                cur = []
            else:
                cur.append(t)
        if cur:
            words.append(cur)
        for w in words:
            i = 0
            while i < len(w):
                if not is_mark(w[i][0]):
                    i += 1
                    continue
                j = i
                while j < len(w) and is_mark(w[j][0]):
                    j += 1
                base = w[i - 1] if i > 0 else (" ", w[i][1], None, None, None)
                key = (base[1], base[0], "".join(m[0] for m in w[i:j]), "|".join(sorted({m[1] for m in w[i:j]})))
                e = combos[key]
                e["n"] += 1
                if page not in e["pages"]:
                    e["pages"].append(page)
                if base[2] is not None:
                    m = w[i]
                    e["pdf"].add((round((m[2] - base[2]) * 1000 / m[4]), round((base[3] - m[3]) * 1000 / m[4])))
                if e["word"] is None:
                    word = [(c, f) for c, f, *_ in w]
                    while len(word) > j and word[-1][0] in ",.":
                        word.pop()
                    e["word"] = word
                    e["page"] = page
                i = j
    return combos


# --- 2. shape --------------------------------------------------------------

_fonts = {}


def font(key):
    if key not in _fonts:
        p = str(FONTS[key]["path"])
        st = TTFont(p)["GPOS"].table.LookupList.Lookup[FONTS[key]["lookup_index"]].SubTable[0]
        _fonts[key] = (hb.Font(hb.Face(hb.Blob.from_file_path(p))), getattr(st, "ExtSubTable", st))
    return _fonts[key]


def shape(key, text):
    f, _ = font(key)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(f, buf, {})
    out, pen = [], 0
    for i, p in zip(buf.glyph_infos, buf.glyph_positions):
        out.append((f.glyph_to_string(i.codepoint), pen + p.x_offset, p.y_offset))
        pen += p.x_advance
    return out


CLASS_NAME = {0: "above", 2: "below"}


def missing_anchor(key, base, mark):
    _, st = font(key)
    if mark == ".notdef":
        return "mark missing from the font"
    mg, bg = st.MarkCoverage.glyphs, st.BaseCoverage.glyphs
    if mark not in mg:
        return "mark not in the mark-to-base lookup"
    cls = st.MarkArray.MarkRecord[mg.index(mark)].Class
    if base not in bg or not st.BaseArray.BaseRecord[bg.index(base)].BaseAnchor[cls]:
        return f"base has no {CLASS_NAME.get(cls, f'class {cls}')} anchor"
    return None


def analyse(combos):
    rows = []
    for (bfont, base, marks, mfonts), e in combos.items():
        style = STYLE.get(bfont)
        if not style or mfonts != bfont or base == " ":
            continue
        o, p = shape(style, base + marks), shape(style + "_patch", base + marks)
        if len(o) != len(p) or len(o) < 2:
            continue
        moves = [(p[k][1] - o[k][1], p[k][2] - o[k][2]) for k in range(1, len(o))]
        miss_o = missing_anchor(style, o[0][0], o[1][0])
        miss_p = missing_anchor(style + "_patch", p[0][0], p[1][0])
        pdf_ok = any(abs(dx - o[1][1]) <= 2 and abs(dy - o[1][2]) <= 2 for dx, dy in e["pdf"])
        rows.append(dict(style=style, base=base, marks=marks, n=e["n"], pages=e["pages"],
                         word=e["word"], page=e["page"], moves=moves, orig=(o[1][1], o[1][2]),
                         miss_o=miss_o, miss_p=miss_p, pdf_ok=pdf_ok,
                         size=max(abs(a) + abs(b) for a, b in moves)))
    return rows


# --- 3. LaTeX --------------------------------------------------------------

def tex_chars(s):
    return "".join(r"\ " if c == " " else f'\\char"{ord(c):04X}' for c in s)


def tex_word(word, fam):
    """Word as runs of characters, each run in the shape of the PDF font."""
    out, run, cur = [], "", None
    for c, f in word:
        st = STYLE.get(f, "regular")
        if st != cur and run:
            out.append(f"{{{SHAPE[cur]}{tex_chars(run)}}}")
            run = ""
        cur = st
        run += c
    if run:
        out.append(f"{{{SHAPE[cur]}{tex_chars(run)}}}")
    return f"{{{fam}{''.join(out)}}}"


def cps(s):
    return " ".join(f"U+{ord(c):04X}" for c in s)


def cell_pair(word):
    o, p = tex_word(word, r"\Orig"), tex_word(word, r"\Patch")
    ov = rf"\rlap{{\color{{patchred}}{p}}}{o}"
    return f"{o} & {p} & {ov}"


def row(r, notes):
    combo = tex_chars(r["base"] + r["marks"])
    if r["miss_o"]:
        note = "not anchored: " + r["miss_o"]
    else:
        note = "anchored"
    if r["miss_p"]:
        note += "; patch: " + r["miss_p"]
    if (r["style"], r["base"] + r["marks"]) in notes:
        note += r"; \textbf{note:} " + notes[(r["style"], r["base"] + r["marks"])]
    mv = "; ".join(f"({dx:+d},\\,{dy:+d})" for dx, dy in r["moves"])
    pages = ", ".join(map(str, r["pages"][:6])) + (", …" if len(r["pages"]) > 6 else "")
    pdf = "" if r["pdf_ok"] else r" \textsuperscript{†}"
    return (f"{{\\Orig{SHAPE[r['style']]}{combo}}} {{\\tiny {cps(r['base'] + r['marks'])}}} & "
            f"{r['page']}{pdf} & {cell_pair(r['word'])} & "
            f"{{\\footnotesize {mv}}} & {{\\footnotesize {r['n']}× (pp.~{pages}); {note}}} \\\\")


def report(pdf):
    cfg = PDF_NOTES.get(pdf.stem, {})
    out = Path(f"tex/pdf_combos_{pdf.stem}.tex")
    combos = collect(pdf)
    rows = analyse(combos)
    suspect = [r for r in rows if (r["miss_o"] and not r["miss_p"]) or r["size"] >= MIN_MOVE]
    rest = [r for r in rows if r not in suspect and not (r["miss_o"] and r["miss_p"])]
    order = ["regular", "italic", "semibold", "semibold_italic"]
    suspect.sort(key=lambda r: (order.index(r["style"]), -r["size"]))
    total = sum(e["n"] for k, e in combos.items() if k[0] in STYLE)
    styles = sorted({r["style"] for r in rows}, key=order.index)
    bad = [r for r in rows if not r["pdf_ok"]]
    if not bad:
        pdf_match = ("The original reproduces the mark position printed in the PDF in every case "
                     "(a † would mark one that does not), so the PDF was set with these original fonts (7.051).")
    else:
        bad_styles = " and ".join(sorted({LABEL[r["style"]].lower() for r in bad}))
        pdf_match = (f"The original reproduces the mark position printed in the PDF except in {len(bad)} combo{'s' if len(bad) > 1 else ''}, "
                     f"marked †, all in {bad_styles}: the PDF was set with another release of that font, so its "
                     f"``original'' column is 7.051, not what the book printed. " + cfg.get("mismatch", ""))
    absent = [LABEL[s].lower() for s in order if s not in styles]

    L = [r"""% Generated by run_pdf_combo_sheet.py; do not edit.
\documentclass[10pt]{article}
\usepackage[table]{xcolor}
\usepackage{fontspec}
\usepackage{longtable}
\usepackage{array}
\usepackage{geometry}
\geometry{a4paper, landscape, left=1.2cm, right=1.2cm, top=1.3cm, bottom=1.3cm}
\setlength{\parindent}{0pt}
\definecolor{patchred}{RGB}{215,40,40}
\setmainfont{Libertinus Serif}[Path = ../fonts/, UprightFont = LibertinusSerif-Regular.otf, ItalicFont = LibertinusSerif-Italic.otf, BoldFont = LibertinusSerif-Semibold.otf, BoldItalicFont = LibertinusSerif-SemiboldItalic.otf]
\newfontfamily\Orig[Path = ../fonts/, UprightFont = LibertinusSerif-Regular.otf, ItalicFont = LibertinusSerif-Italic.otf, BoldFont = LibertinusSerif-Semibold.otf, BoldItalicFont = LibertinusSerif-SemiboldItalic.otf]{Libertinus Serif}
\newfontfamily\Patch[Path = ../fonts/, UprightFont = LibertinusSerif-Regular-patch.otf, ItalicFont = LibertinusSerif-Italic-patch.otf, BoldFont = LibertinusSerif-Semibold-patch.otf, BoldItalicFont = LibertinusSerif-SemiboldItalic-patch.otf]{Libertinus Serif Patch}
\newcommand\sheetbig{\fontsize{17}{22}\selectfont\rule[-10pt]{0pt}{33pt}}
\begin{document}
\section*{Test sheet: combining-mark combos in """ + pdf.name.replace("_", r"\_") + r""", original vs patched}
""" + f"""The PDF has {total} base\\,+\\,mark sequences in Libertinus Serif ({len(rows)} distinct{'; none in ' + ' or '.join(absent) if absent else ''}).
Every one was shaped with HarfBuzz in the original and the patched font of its style. {pdf_match}
A combo is listed if the original font has no anchor for it (the mark is not anchored and is drawn after the base's advance) or the patch moves a mark by at least {MIN_MOVE} units.
Each is shown in the first word of the PDF that has it, every character in the style the PDF set it in. Page = physical page of the PDF (1--{PAGES}), not the book's pagination.
Columns: original, patched, and the two overlaid (patched in \\textcolor{{patchred}}{{red}} over the original in black; only marks that move show red). Move = patched minus original mark position, (x, y) in font units, per mark.
""" + r"""
\renewcommand\arraystretch{1}
\begin{longtable}{l r >{\sheetbig}l >{\sheetbig}l >{\sheetbig}l l >{\raggedright\arraybackslash}p{6.3cm}}
combo & page & \normalsize original & \normalsize patched & \normalsize overlay & move & occurrences \\ \hline \endhead"""]
    cur = None
    for r in suspect:
        if r["style"] != cur:
            cur = r["style"]
            L.append(rf"\multicolumn{{7}}{{l}}{{\textbf{{{LABEL[cur]}}}}} \\")
        L.append(row(r, cfg.get("notes", {})))
    L.append(r"\end{longtable}")

    if cfg.get("special"):
        L.append(r"\section*{Not covered by the patch: reproductions}")
    for caption, page, items in cfg.get("special", []):
        L.append(rf"\subsection*{{p.~{page}}}{caption}\par\smallskip")
        L.append(r"\begin{tabular}{l >{\sheetbig}l >{\sheetbig}l >{\sheetbig}l}variant & \normalsize original & \normalsize patched & \normalsize overlay \\ \hline")
        for label, word in items:
            L.append(rf"{label} & {cell_pair(word)} \\")
        L.append(r"\end{tabular}\par\medskip")

    if cfg.get("checked"):
        L.append(r"\subsection*{Checked in context: not font problems}" + cfg["checked"] + r"\par\medskip")
    L.append(rf"\section*{{Other combos (moved under {MIN_MOVE} units, not set)}}\small")
    L.append(", ".join(rf"{LABEL[r['style']]} {{\Orig{SHAPE[r['style']]}{tex_chars(r['base'] + r['marks'])}}} "
                       rf"p.~{r['page']} ({r['n']}×)" for r in sorted(rest, key=lambda r: -r["n"])) + ".")
    L.append(r"\end{document}")
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"{pdf.name}: {PAGES} pages, {total} sequences, {len(suspect)} suspect combos of {len(rows)}; wrote {out}")
    return suspect, rest, [r for r in rows if r["miss_o"] and r["miss_p"]]


if __name__ == "__main__":
    for pdf in PDFS:
        report(pdf)
