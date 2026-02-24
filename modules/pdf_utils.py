"""
modules/pdf_utils.py
PDF utility - Thai font registration helper
"""

import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

_font_registered = False
_font_name = 'Helvetica'


def get_thai_font():
    """Register and return a Thai-capable font name for ReportLab PDF.

    Searches for fonts in this priority order:
    1. THSarabunNew.ttf in project directory
    2. Leelawadee UI (Windows system font)
    3. Tahoma (Windows system font)
    4. Fallback to Helvetica (no Thai support)

    Returns:
        str: Registered font name
    """
    global _font_registered, _font_name

    if _font_registered:
        return _font_name

    # Search paths for Thai fonts
    project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    font_candidates = [
        # Project-bundled font
        (os.path.join(project_dir, 'THSarabunNew.ttf'), 'Sarabun'),
        (os.path.join(project_dir, 'fonts', 'THSarabunNew.ttf'), 'Sarabun'),
        # Windows system fonts - Leelawadee UI (modern Thai)
        ('C:/Windows/Fonts/LeelawUI.ttf', 'LeelawUI'),
        # Windows system fonts - Tahoma (supports Thai)
        ('C:/Windows/Fonts/tahoma.ttf', 'Tahoma'),
        # Windows system fonts - Leelawadee
        ('C:/Windows/Fonts/leelawad.ttf', 'Leelawadee'),
    ]

    for font_path, name in font_candidates:
        try:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont(name, font_path))
                _font_name = name
                _font_registered = True
                return _font_name
        except Exception:
            continue

    # Fallback - Helvetica (no Thai support)
    _font_registered = True
    _font_name = 'Helvetica'
    return _font_name
