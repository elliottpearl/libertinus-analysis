# Font licenses

The repository's code is MIT (`../LICENSE`); the fonts in this directory are not.

| Files | Font, version | License | License text |
|---|---|---|---|
| `LibertinusSerif-{Regular,Italic,Semibold,SemiboldItalic}.otf`, `LibertinusSerif-*.sfd` | Libertinus Serif 7.051 (The Libertinus Project Authors) | OFL 1.1 | `LibertinusSerif-OFL.txt` |
| `LibertinusSerif-*-<build>.otf` (`-patch`, `-patch-nodot`, `-patch-dotcand`, `-draft`, `-draft-merged`, `-ring*`, `-stack*`, …) | Modified Versions of Libertinus Serif built by this repository | OFL 1.1 (required for Modified Versions) | `LibertinusSerif-OFL.txt` |
| `LangscitinusSerif-*.otf` | Langscitinus (Language Science Press's patch of Libertinus 6.11) | OFL 1.1 | `LangscitinusSerif-OFL.txt` |
| `GentiumPlus-*.ttf` | Gentium Plus 6.101 (SIL International) | OFL 1.1, Reserved Font Names "Gentium", "SIL" | `GentiumPlus-OFL.txt` |
| `NotoSerif-*.ttf` | Noto Serif 2.015 (The Noto Project Authors) | OFL 1.1 | `NotoSerif-OFL.txt` |
| `JunicodeTwoBeta-*.otf` | Junicode Two Beta 1.053 (Peter S. Baker) | OFL 1.1 | `JunicodeTwoBeta-OFL.txt` |
| `STIXTwoText-*.ttf` | STIX Two Text 2.13 (The STIX Fonts Project Authors) | OFL 1.1, Reserved Font Name "TM Math" | `STIXTwoText-OFL.txt` |
| `texgyrepagella-*.otf` | TeX Gyre Pagella (GUST e-foundry) | GUST Font License | `texgyrepagella-GUST-FONT-LICENSE.txt` |
| `Brill-*.ttf` (not in git) | Brill 4.00 build 073 (Koninklijke Brill NV) | Brill Fonts EULA 2.06 | not redistributable; see below |

Notes:

- `LibertinusSerif-OFL.txt`, `LangscitinusSerif-OFL.txt` and `STIXTwoText-OFL.txt` are the projects' own files, and `texgyrepagella-GUST-FONT-LICENSE.txt` is TeX Live's copy. `GentiumPlus-OFL.txt` is the full license text from the font's own name table (ID 13). `NotoSerif-OFL.txt` and `JunicodeTwoBeta-OFL.txt` are the copyright notice from each font's name table (ID 0) followed by the standard OFL 1.1 text.
- Libertinus's Reserved Font Names are "Linux Libertine", "Biolinum" and "STIX Fonts"; "Libertinus" is not reserved. The builds are still renamed internally (`src/libertinus_analysis/font_naming.py`: family "Libertinus Serif Patch", "Libertinus Serif Draft Merged", …; name ID 10 says it is a modified version), so that they are not taken for, or installed over, the original.
- Langscitinus still carries the internal name "Libertinus Serif" (6.11); that is upstream's to fix, and the copies here are unmodified.
- Documents made with the fonts (the PDFs in `../tex/`) are not subject to the OFL (condition 5).

## Brill

The Brill fonts and their two PDFs (`Brill_typeface_end_user_license_agreement.pdf`, `Brill_version_4_00_for_non_commercial_use.pdf`) are gitignored (`fonts/Brill*`). Download them from Brill and place them here. What the EULA allows and forbids (no redistribution, no modification or derivative works, PDFs with subset-embedded Brill may be distributed if non-commercial and read-only) is summarized in `../README-FONTS.md`, "Font licenses".
