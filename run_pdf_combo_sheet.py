"""
Test sheet of the base + combining mark combos found in a PDF set in the
original Libertinus Serif, original vs patched fonts.

    .venv/bin/python run_pdf_combo_sheet.py [PDF[+PDF...] ...]
        (default: data/legacy-fontdata/proofreading-614-1.pdf+proofreading-614-2.pdf)
    cd tex && xelatex pdf_combos_{stem}.tex && xelatex pdf_combos_{stem}.tex   (twice: longtable widths)

One report per argument, tex/pdf_combos_{stem}.tex. PDFs joined by "+" are the
parts of one book and make one report; its stem is their common prefix
(proofreading-614-1 + proofreading-614-2 -> proofreading-614). Notes from
reading a PDF in context (typos, reproductions of what the patch does not
cover) are in data/pdf_combo_notes.py, keyed by the report's stem.

Pages are cited by the book's pagination, read from the printed folios (a
number or roman numeral alone on a line in the top or bottom 12% of the
page). A page without a folio takes its number from its neighbours (see
page_labels); a page outside the book's pagination (covers, a part's
placeholder titles of the other part, an index page printed without a folio)
is cited by its physical page, as "PDF 3". In a book of several parts, a page is
"part:page" (1:93), since the parts' paginations overlap (part 1's back
matter has the numbers of part 2's first chapters).

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
its page.
"""
import os
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

REPORTS = sys.argv[1:] or ["data/legacy-fontdata/proofreading-614-1.pdf+proofreading-614-2.pdf"]
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


ROMAN = re.compile(r"^[ivxlc]+$")
FOLIO_MARGIN = 0.12    # a folio is in the top or bottom 12% of the page
MAX_BACKFILL = 3       # unnumbered pages before a new run of folios that take its numbers


def roman_value(r):
    v = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100}
    return sum(-v[a] if v[a] < v[b] else v[a] for a, b in zip(r, r[1:] + "i"))


def roman(n):
    out = ""
    for v, r in ((100, "c"), (90, "xc"), (50, "l"), (40, "xl"), (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")):
        while n >= v:
            out, n = out + r, n - v
    return out


def page_labels(folios):
    """Book page per physical page (index 0 = page 1) from the printed folios (None where absent).

    A page without a folio between two pages of the same run (same numbering, same
    offset) takes that run's number. Where the run changes, the up to MAX_BACKFILL
    pages before the next run take its numbers if they are at least 1 (a part title,
    its blank verso, the unnumbered first page of a chapter); the rest of the gap
    (e.g. placeholder part titles of another part), and pages before the first folio
    or after the last, get None.
    """
    seq = []  # (kind, physical index - value) per page with a folio
    for i, f in enumerate(folios):
        seq.append(None if f is None else ("r", roman_value(f) - i) if ROMAN.match(f) else ("d", int(f) - i))
    known = [i for i, k in enumerate(seq) if k]
    labels = [None] * len(folios)
    for i in range(len(folios)):
        prev = max((j for j in known if j <= i), default=None)
        nxt = min((j for j in known if j >= i), default=None)
        if prev is None or nxt is None:
            continue
        kind, off = seq[nxt]
        if seq[prev] != seq[nxt] and (nxt - i > MAX_BACKFILL or off + i < 1):
            continue
        labels[i] = str(off + i) if kind == "d" else roman(off + i)
    return labels


def read_pdf(pdf):
    """Yield (page, [(char, font, x, y, size), ...]) per text line; return the book page labels."""
    folios = []
    with tempfile.TemporaryDirectory() as tmp:
        xml = Path(tmp) / "p.xml"
        subprocess.run(["mutool", "draw", "-q", "-F", "stext", "-o", str(xml), str(pdf)],
                       check=True, stderr=subprocess.DEVNULL)
        xml.write_bytes(BAD_REF.sub(b"\xef\xbf\xbd", xml.read_bytes()))
        page, font, size, line, height = 0, None, None, [], 0
        for ev, el in ET.iterparse(xml, events=("start", "end")):
            if ev == "start":
                if el.tag == "page":
                    page += 1
                    height = float(el.get("height"))
                    folios.append(None)
                elif el.tag == "font":
                    font, size = font_name(el.get("name")), float(el.get("size"))
            elif el.tag == "char":
                for ch in el.get("c"):
                    line.append((ch, font, float(el.get("x")), float(el.get("y")), size))
                el.clear()
            elif el.tag == "line":
                y0, y1 = (float(v) for v in el.get("bbox").split()[1::2])
                text = "".join(t[0] for t in line).strip()
                if (y1 < FOLIO_MARGIN * height or y0 > (1 - FOLIO_MARGIN) * height) and \
                        (text.isdigit() or ROMAN.match(text)):
                    folios[-1] = text
                yield page, line
                line = []
            elif el.tag == "page":
                el.clear()
    return page_labels(folios)


LABELS = {}   # part (1-based) -> [book page label or None per physical page]
MULTI = False  # the report has several parts: cite part:page


def cite(where):
    """Book page of (part, physical page): 93, xii, 1:93, or PDF 3 / 1:PDF 3 outside the pagination."""
    part, page = where
    lab = LABELS[part][page - 1] or f"PDF {page}"
    return f"{part}:{lab}" if MULTI else lab


def lines(pdfs):
    """Yield ((part, page), line) over the parts in order, and fill LABELS."""
    for part, pdf in enumerate(pdfs, 1):
        it = read_pdf(pdf)
        while True:
            try:
                page, line = next(it)
            except StopIteration as stop:
                LABELS[part] = stop.value
                break
            yield (part, page), line


def collect(pdfs):
    """combos[(font, base, marks, markfonts)] = {n, pages, pdf_dx, pdf_dy, word, page}; pages are (part, page)."""
    combos = defaultdict(lambda: {"n": 0, "pages": [], "pdf": set(), "word": None, "page": None})
    for page, line in lines(pdfs):
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
    pages = ", ".join(map(cite, r["pages"][:6])) + (", …" if len(r["pages"]) > 6 else "")
    pdf = "" if r["pdf_ok"] else r" \textsuperscript{†}"
    return (f"{{\\Orig{SHAPE[r['style']]}{combo}}} {{\\tiny {cps(r['base'] + r['marks'])}}} & "
            f"{cite(r['page'])}{pdf} & {cell_pair(r['word'])} & "
            f"{{\\footnotesize {mv}}} & {{\\footnotesize {r['n']}× (pp.~{pages}); {note}}} \\\\")


def parts(arg):
    """The PDFs of one report ("a.pdf+b.pdf": b.pdf in a.pdf's directory) and the report's stem."""
    first, *rest = arg.split("+")
    pdfs = [Path(first)] + [Path(first).parent / r for r in rest]
    stem = pdfs[0].stem
    if rest:
        stem = os.path.commonprefix([q.stem for q in pdfs]).rstrip("-_ ")
    return pdfs, stem


def title(stem):
    m = re.fullmatch(r"proofreading-(\d+)", stem)
    return f"volume {m.group(1)}" if m else stem.replace("_", r"\_") + ".pdf"


def report(arg):
    global MULTI
    pdfs, stem = parts(arg)
    MULTI = len(pdfs) > 1
    LABELS.clear()
    cfg = PDF_NOTES.get(stem, {})
    out = Path(f"tex/pdf_combos_{stem}.tex")
    combos = collect(pdfs)
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
    npages = [len(LABELS[k]) for k in sorted(LABELS)]
    if MULTI:
        src = (f"The book is in {len(pdfs)} PDFs (" + ", ".join(
            f"part~{k}: {q.name.replace('_', chr(92) + '_')}, {n} pages" for k, (q, n) in enumerate(zip(pdfs, npages), 1))
            + "). Together they have")
        pagenote = ("Page = the book's printed page number, as part:page (1:93), since the parts' paginations overlap "
                    "(the back matter of part~1 has the numbers of the first chapters of part~2).")
    else:
        src = "The PDF has"
        pagenote = "Page = the book's printed page number (not the PDF's physical page)."

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
\section*{Test sheet: combining-mark combos in """ + title(stem) + r""", original vs.\ patched}
""" + f"""{src} {total} base\\,+\\,mark sequences in Libertinus Serif ({len(rows)} distinct{'; none in ' + ' or '.join(absent) if absent else ''}).
Every one was shaped with HarfBuzz in the original and the patched font of its style. {pdf_match}
A combo is listed if the original font has no anchor for it (the mark is not anchored and is drawn after the base's advance) or the patch moves a mark by at least {MIN_MOVE} units.
Each is shown in the first word of the PDF that has it, every character in the style the PDF set it in. {pagenote}
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
        L.append(rf"\subsection*{{p.~{page}}}{caption}\par\smallskip")  # page: as the notes cite it
        L.append(r"\begin{tabular}{l >{\sheetbig}l >{\sheetbig}l >{\sheetbig}l}variant & \normalsize original & \normalsize patched & \normalsize overlay \\ \hline")
        for label, word in items:
            L.append(rf"{label} & {cell_pair(word)} \\")
        L.append(r"\end{tabular}\par\medskip")

    if cfg.get("checked"):
        L.append(r"\subsection*{Checked in context: not font problems}" + cfg["checked"] + r"\par\medskip")
    L.append(rf"\section*{{Other combos (moved under {MIN_MOVE} units, not set)}}\small")
    L.append(", ".join(rf"{LABEL[r['style']]} {{\Orig{SHAPE[r['style']]}{tex_chars(r['base'] + r['marks'])}}} "
                       rf"p.~{cite(r['page'])} ({r['n']}×)" for r in sorted(rest, key=lambda r: -r["n"])) + ".")
    L.append(r"\end{document}")
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"{stem}: {'+'.join(map(str, npages))} pages, {total} sequences, {len(suspect)} suspect combos of {len(rows)}; wrote {out}")
    return suspect, rest, [r for r in rows if r["miss_o"] and r["miss_p"]]


if __name__ == "__main__":
    for arg in REPORTS:
        report(arg)
