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
its page and line. The word is cut at punctuation before and after the combo
("(Tȁkı̋." -> "Tȁkı̋") and at brackets, slashes and
quotes inside it ("ɔ̏‶/‶/∅/w(ȍ" -> "ɔ̏"), and a character smaller than the line's text and off its
baseline is set as a superscript or subscript, as printed (tɕiɛ̃²¹³⁻²¹). The line
is the rank of the text line's baseline among the page's distinct baselines,
counted from the top (the baseline of its largest text, so a line of superscripted
tone numbers is not counted apart), leaving out the running header (bottom edge in the top
LINE_TOP of the page) and the folio: every text line counts, including table
rows, interlinear gloss lines and footnotes.
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
LINE_TOP = 0.09        # lines ending in the top 9% (running header, proofreading stamp) are not counted
BASELINE_MERGE = 3.0   # pt; text lines on baselines this close are one line
SCRIPT_SIZE = 0.9      # a character under this fraction of the line's size ...
SCRIPT_SHIFT = 0.12    # ... and at least this fraction of it off the baseline is a super/subscript
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


def mode(values):
    return max(set(values), key=values.count) if values else None


def baseline(line):
    """Baseline of the line's largest text (not of its super/subscripts); None for an empty line."""
    ref = max((round(t[4], 1) for t in line if not t[0].isspace()), default=None)
    return None if ref is None else mode([round(t[3], 1) for t in line if round(t[4], 1) == ref])


def number_lines(page_lines, height):
    """[(line number or None, line)] for one page: rank of the line's baseline from the top."""
    out, bases = [], []
    for y0, y1, line in page_lines:
        base = baseline(line)
        body = base is not None and y1 >= LINE_TOP * height
        out.append((base if body else None, line))
        if body:
            bases.append(base)
    ranks, last, n = {}, None, 0
    for b in sorted(set(bases)):
        if last is None or b - last > BASELINE_MERGE:
            n += 1
        ranks[b], last = n, b
    return [(ranks.get(b), line) for b, line in out]


def read_pdf(pdf):
    """Yield (page, line no., [(char, font, x, y, size), ...]) per text line; return the book page labels."""
    folios = []
    with tempfile.TemporaryDirectory() as tmp:
        xml = Path(tmp) / "p.xml"
        subprocess.run(["mutool", "draw", "-q", "-F", "stext", "-o", str(xml), str(pdf)],
                       check=True, stderr=subprocess.DEVNULL)
        xml.write_bytes(BAD_REF.sub(b"\xef\xbf\xbd", xml.read_bytes()))
        page, font, size, line, height, page_lines = 0, None, None, [], 0, []
        for ev, el in ET.iterparse(xml, events=("start", "end")):
            if ev == "start":
                if el.tag == "page":
                    page += 1
                    height = float(el.get("height"))
                    folios.append(None)
                    page_lines = []
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
                else:
                    page_lines.append((y0, y1, line))
                line = []
            elif el.tag == "page":
                for n, ln in number_lines(page_lines, height):
                    yield page, n, ln
                el.clear()
    return page_labels(folios)


LABELS = {}   # part (1-based) -> [book page label or None per physical page]
MULTI = False  # the report has several parts: cite part:page


def cite(where, line=None):
    """Book page of (part, physical page): 93, xii, 1:93, or PDF 3 / 1:PDF 3 outside the pagination; with ", l. 12"."""
    part, page = where
    lab = LABELS[part][page - 1] or f"PDF {page}"
    lab = f"{part}:{lab}" if MULTI else lab
    return f"{lab}, l.~{line}" if line else lab


def lines(pdfs):
    """Yield ((part, page), line) over the parts in order, and fill LABELS."""
    for part, pdf in enumerate(pdfs, 1):
        it = read_pdf(pdf)
        while True:
            try:
                page, n, line = next(it)
            except StopIteration as stop:
                LABELS[part] = stop.value
                break
            yield (part, page), n, line


def collect(pdfs):
    """combos[(font, base, marks, markfonts)] = {n, pages, pdf_dx, pdf_dy, word, page}; pages are (part, page)."""
    combos = defaultdict(lambda: {"n": 0, "pages": [], "pdf": set(), "word": None, "page": None, "line": None})
    for page, lineno, line in lines(pdfs):
        script = scripts(line)
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
                    word = [(t[0], t[1], script[id(t)]) for t in w]
                    a, b = 0, len(word)
                    for k in range(i - 1):
                        if is_split(word[k][0]):
                            a = k + 1
                    for k in range(len(word) - 1, j - 1, -1):
                        if is_split(word[k][0]):
                            b = k
                    while a < i - 1 and is_punct(word[a][0]):
                        a += 1
                    while b > j and is_punct(word[b - 1][0]):
                        b -= 1
                    e["word"] = word[a:b]
                    e["page"] = page
                    e["line"] = lineno
                i = j
    return combos


def is_punct(c):
    return ud.category(c)[0] == "P"


APOSTROPHES = "'\u2019\u02BC"


def is_split(c):
    """Punctuation that ends the sample word even inside a run without spaces: ɔ̏‶/‶/∅/w(ȍ -> ɔ̏.
    Hyphens, periods, = and apostrophes are morpheme or syllable boundaries in glosses and stay."""
    return (ud.category(c) in ("Ps", "Pe", "Pi", "Pf") and c not in APOSTROPHES) or c in "/|\"\u2033\u2036,;:!?"


def scripts(line):
    """{id(char tuple): "" | "sup" | "sub"}: smaller than the line's largest text and off its baseline."""
    # the largest size, not the most common: in a table cell like tɕiɛ̃²¹³⁻²¹ the scripts outnumber the text
    ref = max((round(t[4], 1) for t in line if not t[0].isspace()), default=None)
    if ref is None:
        return {}
    base = baseline(line)
    out = {}
    for t in line:
        pos = ""
        if t[4] < SCRIPT_SIZE * ref and not is_mark(t[0]):
            if t[3] < base - SCRIPT_SHIFT * ref:
                pos = "sup"
            elif t[3] > base + SCRIPT_SHIFT * ref:
                pos = "sub"
        out[id(t)] = pos
    # a mark is set with its base
    prev = ""
    for t in line:
        if is_mark(t[0]):
            out[id(t)] = prev
        prev = out[id(t)]
    return out


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


def unanchored(key, shaped, marks):
    """Why each mark of a shaped combo is not anchored ("U+0301: base has no above anchor; ..."), or None.

    Every mark is checked against the base: HarfBuzz attaches a mark to the base by mark-to-base
    (or to the previous mark by mark-to-mark, which needs the first mark anchored to the base)."""
    out = []
    for k, (g, *_) in enumerate(shaped[1:]):
        why = missing_anchor(key, shaped[0][0], g)
        if why:
            cp = f"U+{ord(marks[k]):04X}: " if len(shaped) > 2 and k < len(marks) else ""
            out.append(cp + why)
    return "; ".join(out) or None


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
        miss_o = unanchored(style, o, marks)
        miss_p = unanchored(style + "_patch", p, marks)
        pdf_ok = any(abs(dx - o[1][1]) <= 2 and abs(dy - o[1][2]) <= 2 for dx, dy in e["pdf"])
        rows.append(dict(style=style, base=base, marks=marks, n=e["n"], pages=e["pages"],
                         word=e["word"], page=e["page"], line=e["line"], moves=moves, orig=(o[1][1], o[1][2]),
                         miss_o=miss_o, miss_p=miss_p, pdf_ok=pdf_ok,
                         size=max(abs(a) + abs(b) for a, b in moves)))
    return rows


# --- 3. LaTeX --------------------------------------------------------------

def tex_chars(s):
    return "".join(r"\ " if c == " " else f'\\char"{ord(c):04X}' for c in s)


SCRIPT_TEX = {"": "{}", "sup": r"\textsuperscript{{{}}}", "sub": r"\textsubscript{{{}}}"}


def tex_word(word, fam):
    """Word as runs of characters, each run in the shape of the PDF font, super/subscripts as printed.

    word: [(char, PDF font) or (char, PDF font, "" | "sup" | "sub")]."""
    out, run, cur = [], "", None
    for c, f, *pos in word:
        key = (STYLE.get(f, "regular"), pos[0] if pos else "")
        if key != cur and run:
            out.append(SCRIPT_TEX[cur[1]].format(f"{{{SHAPE[cur[0]]}{tex_chars(run)}}}"))
            run = ""
        cur = key
        run += c
    if run:
        out.append(SCRIPT_TEX[cur[1]].format(f"{{{SHAPE[cur[0]]}{tex_chars(run)}}}"))
    return f"{{{fam}{''.join(out)}}}"


def cps(s):
    return " ".join(f"U+{ord(c):04X}" for c in s)


def cell_pair(word):
    o, p = tex_word(word, r"\Orig"), tex_word(word, r"\Patch")
    ov = rf"\rlap{{\color{{patchred}}{p}}}{o}"
    return f"{o} & {p} & {ov}"


def row(r, notes):
    combo = tex_chars(r["base"] + r["marks"])
    if r["miss_o"] and r["miss_p"]:
        note = r"\textbf{not anchored in either font:} " + r["miss_o"]
        if r["miss_p"] != r["miss_o"]:
            note += "; patch: " + r["miss_p"]
    elif r["miss_o"]:
        note = "not anchored in the original (" + r["miss_o"] + "); anchored in the patch"
    elif r["miss_p"]:
        note = r"anchored in the original; \textbf{not anchored in the patch:} " + r["miss_p"]
    else:
        note = "anchored"
    if (r["style"], r["base"] + r["marks"]) in notes:
        note += r"; \textbf{note:} " + notes[(r["style"], r["base"] + r["marks"])]
    mv = "; ".join(f"({dx:+d},\\,{dy:+d})" for dx, dy in r["moves"])
    pages = ", ".join(map(cite, r["pages"][:6])) + (", …" if len(r["pages"]) > 6 else "")
    pdf = "" if r["pdf_ok"] else r" \textsuperscript{†}"
    return (f"{{\\Orig{SHAPE[r['style']]}{combo}}} {{\\tiny {cps(r['base'] + r['marks'])}}} & "
            f"{cite(r['page'], r['line'])}{pdf} & {cell_pair(r['word'])} & "
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
    suspect = [r for r in rows if r["miss_o"] or r["miss_p"] or r["size"] >= MIN_MOVE]
    rest = [r for r in rows if r not in suspect]   # anchored in both fonts, moved under MIN_MOVE
    order = ["regular", "italic", "semibold", "semibold_italic"]
    # per style: not anchored in either font first (what the patch leaves to fix), then by the size of the move
    suspect.sort(key=lambda r: (order.index(r["style"]), not (r["miss_o"] and r["miss_p"]), -r["size"]))
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
A combo is listed if a mark is not anchored in the original or the patched font (it is then drawn where its outline lies, after the base's advance) or the patch moves a mark by at least {MIN_MOVE} units. In each style, combos anchored in neither font come first: those the patch does not fix.
Each is shown in the first word of the PDF that has it, without the punctuation around it, every character in the style the PDF set it in, super- and subscripts as printed. {pagenote}
Line = the text line on that page, counted from the top without the running header; every text line counts, including table rows, gloss lines and footnotes.
Columns: original, patched, and the two overlaid (patched in \\textcolor{{patchred}}{{red}} over the original in black; only marks that move show red). Move = patched minus original mark position, (x, y) in font units, per mark.
""" + r"""
\renewcommand\arraystretch{1}
\begin{longtable}{l r >{\sheetbig}l >{\sheetbig}l >{\sheetbig}l l >{\raggedright\arraybackslash}p{6.3cm}}
combo & page, line & \normalsize original & \normalsize patched & \normalsize overlay & move & occurrences \\ \hline \endhead"""]
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
    L.append(rf"\section*{{Other combos: anchored in both fonts, moved under {MIN_MOVE} units}}")
    L.append(r"No sample words for these; move = patched minus original position of each mark.\par\smallskip\small")
    L.append(", ".join(rf"{LABEL[r['style']]} {{\Orig{SHAPE[r['style']]}{tex_chars(r['base'] + r['marks'])}}} "
                       rf"p.~{cite(r['page'], r['line'])} ({r['n']}×; "
                       + "; ".join(f"{dx:+d},\\,{dy:+d}" for dx, dy in r["moves"]) + ")"
                       for r in sorted(rest, key=lambda r: -r["n"])) + ("." if rest else "None."))
    L.append(r"\end{document}")
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"{stem}: {'+'.join(map(str, npages))} pages, {total} sequences, {len(suspect)} suspect combos of {len(rows)}; wrote {out}")
    return suspect, rest, [r for r in rows if r["miss_o"] and r["miss_p"]]


if __name__ == "__main__":
    for arg in REPORTS:
        report(arg)
