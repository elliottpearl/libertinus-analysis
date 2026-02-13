from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

DATA_DIR = ROOT / "data"
FONTDATA_DIR = DATA_DIR / "fontdata"
DIAGNOSTICS_DIR = DATA_DIR / "diagnostics"
IPA_DIR = DATA_DIR / "ipa"

FONTS_DIR = ROOT / "fonts"

TEX_DIR = ROOT / "tex"
TEX_INPUT_DIR = TEX_DIR / "input"
