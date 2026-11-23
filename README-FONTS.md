# Font loading and fontspec

Fonts are in `fonts/` as `.otf` and `.ttf` fonts. 
This includes original fonts (Libertinus, Langscitinus, Gentium Plus, Noto Serif, Junicode Two Beta, TeX Gyre Pagella, STIX Two Text, Brill) and patches of Libertinus.
LSP uses the semibold Libertinus font for boldface.

LaTeX files are in `tex/`.  

Always include the extension `.otf` and `.ttf` in the font loading command in LaTeX.

```
\usepackage{fontspec}

% Load fonts
% always use `Path = ../fonts/,`
% always include extension e.g. `.otf`, `.ttf`

\setmainfont{Libertinus Serif}[
	Path = ../fonts/,
	UprightFont    = LibertinusSerif-Regular.otf,
	ItalicFont     = LibertinusSerif-Italic.otf,
	BoldFont       = LibertinusSerif-Semibold.otf,
	BoldItalicFont = LibertinusSerif-SemiboldItalic.otf
]

\newfontfamily\LibertinusSerifPatch[
	Path = ../fonts/,
	UprightFont    = LibertinusSerif-Regular-patch.otf,
	ItalicFont     = LibertinusSerif-Italic-patch.otf,
	BoldFont       = LibertinusSerif-Semibold-patch.otf,
	BoldItalicFont = LibertinusSerif-SemiboldItalic-patch.otf
]{Libertinus Serif Patch}

\newfontfamily\Gentium[
	Path = ../fonts/,
]{GentiumPlus-Regular.ttf}
```

```
\newfontfamily\STIXTwo[
	Path = ../fonts/,
	UprightFont    = STIXTwoText-Regular.ttf,
	ItalicFont     = STIXTwoText-Italic.ttf,
	BoldFont       = STIXTwoText-SemiBold.ttf,
	BoldItalicFont = STIXTwoText-SemiBoldItalic.ttf
]{STIX Two Text}

\newfontfamily\Brill[
	Path = ../fonts/,
	UprightFont    = Brill-Roman.ttf,
	ItalicFont     = Brill-Italic.ttf,
	BoldFont       = Brill-Bold.ttf,
	BoldItalicFont = Brill-BoldItalic.ttf
]{Brill}
```

## Font licenses

Each font's license and its license file are listed in `fonts/LICENSES.md`; the repository's own code is MIT (`LICENSE`). The fonts built from Libertinus (`-patch`, `-draft`, …) are Modified Versions and so OFL 1.1, and they are renamed internally from their file names (`LibertinusSerif-Regular-patch.otf` → family "Libertinus Serif Patch") by `font_naming.save_renamed`, which every font-writing path uses. STIX Two Text 2.13 is the static fonts from the variable-font download (Regular, Medium, SemiBold and Bold, each with an italic).

### Brill (not redistributable)

`fonts/Brill-*.ttf` (Brill 4.00 build 073) and the two Brill PDFs beside them (`Brill_typeface_end_user_license_agreement.pdf`, the EULA, version 2.06, 2014; `Brill_version_4_00_for_non_commercial_use.pdf`, the documentation) are under the Brill Fonts EULA. They are in `.gitignore` (`fonts/Brill*`) and must never be committed. Under the EULA:

- **No redistribution** of the fonts or the documentation (clauses 5, 11). Brill's website is the only source.
- **No modification and no derivative works** (clauses 8, 10). Use Brill only as an unmodified comparison font. Do not run the patch pipeline, drafts, subsetting to files, instancing or `ttx` dumps that write a converted font. Reading metrics and anchors in memory (fontTools) for analysis is fine. Do not write font data extracted from it (outlines) to committed files either. Measured numbers in reports are fine.
- **PDFs: subset embedding is allowed** (`fsType` 8, editable embedding). Non-commercial PDFs set in Brill may be distributed: the EULA's definition of "Commercial Product" explicitly allows embedding "in a PDF document or the like that is published on Licensee's website". Conditions: the PDF must be read-only (viewable and printable, not editable by third parties; clause 8), and it must not be sold or offered for any consideration. The EULA counts **Open Access publications as commercial**, and also any document prepared for a publisher other than Brill (for example, a Language Science Press book). Clause 7 also limits embedding to the licensee's "own personal Use", which sits uneasily with the website-publishing allowance; ask brill-typeface@brill.com if a PDF is to be published anywhere beyond this project.
- At most three computers (clause 6); never on an internet-accessible server or served as web fonts.
