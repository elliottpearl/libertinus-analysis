# font_patching_gsub.py
"""
GSUB-patching stage of the patching pipeline.

Rebuilds GSUB from a human-curated .fea file, while preserving GPOS.
"""

from fontTools.feaLib.builder import Builder


def patch_gsub_ccmp(ttfont, font_key: str) -> None:
    """
    Patch GSUB using the human-curated ccmp.fea file for the given font_key.

    This preserves the original behavior:
    - Save original GPOS
    - Run feaLib Builder on ccmp.fea (which rebuilds GSUB and nukes GPOS)
    - Restore original GPOS
    """

    ccmp_fea_path = f"data/fea/{font_key}/ccmp.fea"

    # Save original GPOS so Builder can't destroy it
    original_gpos = ttfont["GPOS"]

    try:
        builder = Builder(ttfont, ccmp_fea_path)
        builder.build()  # This rebuilds GSUB *and nukes GPOS*
        # Restore original GPOS
        ttfont["GPOS"] = original_gpos
        print(f"Applied GSUB features from {ccmp_fea_path}")
    except Exception as e:
        print(f"WARNING: Failed to apply GSUB features from {ccmp_fea_path}: {e}")
