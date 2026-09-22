# -*- coding: utf-8 -*-
"""Font loader for ZimTube."""
import os
import sdl2.sdlttf as ttf

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Font search order
_FONT_PATHS = [
    os.path.join(APP_DIR, "assets", "font.ttf"),
    os.path.join(APP_DIR, "assets", "NotoSans.ttf"),
    # Fallback: borrow from ZimRetroHub if installed
    os.path.join(os.environ.get("SDCARD_PATH", "/mnt/SDCARD"),
                 "Apps", "RetroHub", "assets", "font.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/usr/trimui/res/SourceHanSans.otf",
]


def find_font():
    for p in _FONT_PATHS:
        if os.path.exists(p):
            return p
    return None


def load_fonts():
    """Return (font_title, font_body, font_small) or None on failure."""
    ttf.TTF_Init()
    path = find_font()
    if not path:
        return None
    f_title = ttf.TTF_OpenFont(path.encode(), 26)
    f_body  = ttf.TTF_OpenFont(path.encode(), 20)
    f_small = ttf.TTF_OpenFont(path.encode(), 16)
    if not f_title or not f_body or not f_small:
        return None
    return f_title, f_body, f_small
