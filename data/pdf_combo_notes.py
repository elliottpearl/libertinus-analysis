"""
Notes from reading the PDFs scanned by run_pdf_combo_sheet.py in context,
keyed by the PDF's file stem.

notes:   {(style, base + marks): note}, appended to that combo's row.
special: [(caption, page, [(label, [(char, PDF font name), ...]), ...])],
         reproductions of problems the patch does not cover.
checked: LaTeX paragraph on combos checked in context that are not font problems.
"""

R, I = "LibertinusSerif-Regular", "LibertinusSerif-Italic"
STACK = ("A second above mark on a precomposed letter that already has one. Italic ö and ä have no above "
         "anchor in either font (stage 9 inherits an above anchor only for letters without an above mark), "
         "so the grave is not anchored and lands on the diaeresis; regular ä has a stacking anchor, and so "
         "does italic ā (ā́ in 614.pdf is anchored). Not covered by the patch.")


def chars(s, font):
    return [(c, font) for c in s]


PDF_NOTES = {
    "614": {
        "notes": {
            ("italic", "č̠̭"):
                "probably a typo for /č̭/: the only U+0320 in the book; the same list on p.~113 "
                "has /č̭/ [ʧ], and the unaspirated diacritic is U+032D (/k̭/, /ṱ/)",
        },
        "special": [
            ("Tie bar U+0361 (double inverted breve) is not in the mark-to-base lookup of either font: "
             "it is placed by its drawn outline, so its position depends on the first letter's advance.", 131,
             [("as printed", chars("∼t͡ʃ", R)),
              ("t͡s", chars("t͡s", R)),
              ("p.~131, ɟøzæt͡ʃːi", chars("ɟøzæt͡ʃːi", R)),
              ("k͡p, d͡ʒ", chars("k͡p d͡ʒ", R))]),
            ("A mark cited on its own after a space (“marked in the transcription by the diacritic ̭”). "
             "In the PDF the mark sits in the space, much as in the NBSP row, so this is not a visible problem; "
             "but U+0020 has no anchors in either font, and only an anchored base guarantees the placement: "
             "the patch gives NBSP x-height anchors for floating marks (U+25CC dotted circle is the other usual base).", 113,
             [("space + mark", chars("diacritic ̭):", R)),
              ("NBSP + mark", chars("diacritic  ̭):", R)),
              ("◌ + mark", chars("diacritic ◌̭):", R))]),
        ],
        "checked": (
            r"p.~163, example (16), \emph{*̆ḷə ḡawwāyā} `inside': an encoding typo. The PDF has a stray U+0306 "
            r"after the asterisk (the starred-form marker); the word begins with ḷ, which should not also carry "
            r"a breve. In print the breve falls on the asterisk and is nearly invisible, but it is in the text. "
            r"p.~85, (10), \emph{zīyāy, zīyā}: mutool reports the U+0304 of ī in the subset of "
            r"LibertinusSerif-Regular after an italic i, but the zero-width mark's own outline lands over the "
            r"i and hides its dot, so it looks right; the bold letters are deliberate. Not a font issue."),
    },
    "proofreading-613": {
        "mismatch": ("In semibold the PDF has the acute and grave on ɛ ɔ about 30 units higher than 7.051 "
                     "(y offset −37 against −68), within a unit of where the patch puts them (−38); the macron on n is 20 units lower."),
        "special": [
            (STACK, 297,
             [("as printed", chars("p-\u00f6\u0300y-n-\u014b", I)),
              ("regular", chars("p-\u00f6\u0300y-n-\u014b", R))]),
            ("Tie bar U+0361 is not in the mark-to-base lookup of either font; it is placed by its drawn "
             "outline (as in 614.pdf).", 36,
             [("as printed", chars("ed\u0361\u0292a", I)),
              ("regular", chars("ed\u0361\u0292a", R))]),
            ("Combining overline U+0305 is not in the mark-to-base lookup either (it is drawn to join up "
             "across letters); it sits where its outline is drawn, which here is over the m.", 293,
             [("as printed", chars("na-tm\u0305anmat", I))]),
        ],
        "checked": (
            r"Encoding typos, not font problems. p.~93, (b), a starred example: \emph{ŋwàʼnyə̀ ̀ piŋ} has a second "
            r"grave after a space, which prints as a loose grave after ə̀. p.~95, \emph{pe ́ exclude such DPs}: a space "
            r"between e and U+0301, which prints as a loose acute; \emph{pé} is meant (as on the next line). "
            r"The PDF also sets some IPA in the TIPA fonts (tipa8--10), which this scan does not see."),
    },
    "proofreading-633": {
        "mismatch": ("In semibold the PDF has the dot above on u (Sȯu̇th) 31 units higher than 7.051 puts it."),
        "special": [
            (STACK + " Here in italic \\emph{die Jä̀gerey}, against the regular ä̀ after it.", 263,
             [("as printed", chars("J\u00e4\u0300gerey", I)),
              ("regular ä̀", chars("\u00e4\u0300", R))]),
        ],
    },
}
