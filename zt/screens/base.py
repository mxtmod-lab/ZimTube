# -*- coding: utf-8 -*-
"""Base screen class for ZimTube."""


class BaseScreen:
    def __init__(self, engine=None):
        self.engine = engine

    def on_enter(self, params=None):
        pass

    def on_exit(self):
        pass

    def on_resume(self):
        pass

    def handle_input(self, inputs) -> bool:
        """Return True if UI needs redraw."""
        return False

    def render(self, engine):
        pass

    # ── Common drawing helpers ────────────────────────────────────────────

    def draw_header(self, engine, title="ZimTube", subtitle=""):
        from zt.engine import HEADER_BG, ACCENT, TEXT_PRIMARY, TEXT_SECONDARY
        from zt.state import SCREEN_W
        engine.fill_rect(0, 0, SCREEN_W, 56, *HEADER_BG[:3])
        # Red accent bar
        engine.fill_rect(0, 52, SCREEN_W, 4, 255, 0, 0)
        # Logo: red circle + ZimTube text
        engine.fill_rect(12, 10, 36, 36, 255, 0, 0)
        engine.draw_text("▶", engine.font_body, 12, 10, 255, 255, 255)
        engine.draw_text("ZimTube", engine.font_title, 56, 14, 255, 255, 255)
        if subtitle:
            engine.draw_text(subtitle, engine.font_small,
                             SCREEN_W - 16 - engine.text_width(subtitle, engine.font_small),
                             20, 170, 170, 170)

    def draw_footer(self, engine, hints):
        """hints: list of (button_label, action_text)"""
        from zt.engine import FOOTER_BG
        from zt.state import SCREEN_W, SCREEN_H
        fh = 36
        engine.fill_rect(0, SCREEN_H - fh, SCREEN_W, fh, *FOOTER_BG[:3])
        engine.fill_rect(0, SCREEN_H - fh, SCREEN_W, 1, 60, 60, 60)
        x = 16
        for btn, action in hints:
            engine.fill_rect(x, SCREEN_H - fh + 6, 24, 22, 60, 60, 60)
            engine.draw_text(btn, engine.font_small, x + 4, SCREEN_H - fh + 10, 255, 255, 255)
            x += 30
            engine.draw_text(action, engine.font_small, x, SCREEN_H - fh + 10, 170, 170, 170)
            x += engine.text_width(action, engine.font_small) + 24
