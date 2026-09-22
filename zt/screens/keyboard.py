# -*- coding: utf-8 -*-
"""Virtual keyboard screen — D-pad navigation, search submit."""
from .base import BaseScreen
from zt.state import SCREEN_W, SCREEN_H
from zt import yt

_ROWS = [
    list("1234567890"),
    list("QWERTYUIOP"),
    list("ASDFGHJKL"),
    list("ZXCVBNM"),
    ["SPACE", "⌫", "OK"],
]
_LAYOUT_Y = 230
_KEY_W = 76
_KEY_H = 56
_KEY_GAP = 6


class KeyboardScreen(BaseScreen):
    def __init__(self, engine=None):
        super().__init__(engine)
        self.query = ""
        self.row = 1
        self.col = 0
        self.callback_screen = "home"
        self.callback_params = {}

    def on_enter(self, params=None):
        params = params or {}
        self.query = params.get("initial_query", "")
        self.callback_screen = params.get("callback_screen", "home")
        self.callback_params = params.get("callback_params", {})
        self.row = 1
        self.col = 0

    # ── Input ─────────────────────────────────────────────────────────────

    def handle_input(self, inputs):
        dirty = False
        cur_row = _ROWS[self.row]
        max_col = len(cur_row) - 1

        if inputs.get("btn_up"):
            if self.row > 0:
                self.row -= 1
                self.col = min(self.col, len(_ROWS[self.row]) - 1)
                dirty = True

        if inputs.get("btn_down"):
            if self.row < len(_ROWS) - 1:
                self.row += 1
                self.col = min(self.col, len(_ROWS[self.row]) - 1)
                dirty = True

        if inputs.get("btn_left"):
            if self.col > 0:
                self.col -= 1; dirty = True

        if inputs.get("btn_right"):
            if self.col < max_col:
                self.col += 1; dirty = True

        if inputs.get("btn_a"):
            key = _ROWS[self.row][self.col]
            if key == "OK":
                self._submit()
                return True
            elif key == "⌫":
                self.query = self.query[:-1]; dirty = True
            elif key == "SPACE":
                self.query += " "; dirty = True
            else:
                self.query += key; dirty = True

        if inputs.get("btn_b"):
            self.engine.pop_screen(); return True

        if inputs.get("btn_x"):
            self.query = self.query[:-1]; dirty = True

        if inputs.get("btn_start"):
            self._submit(); return True

        return dirty

    def _submit(self):
        q = self.query.strip()
        if not q:
            self.engine.pop_screen()
            return
        # Save to search history
        history = yt.load_search_history() or []
        if q in history:
            history.remove(q)
        history.insert(0, q)
        yt.save_search_history(history[:10])

        # Navigate to search results
        self.engine.pop_screen()
        # Reload home with new query tab
        params = dict(self.callback_params)
        params["query"] = q
        # Push search screen
        self.engine.push_screen("search", {"query": q})

    # ── Render ────────────────────────────────────────────────────────────

    def render(self, engine):
        self.draw_header(engine, subtitle="Tìm kiếm")

        # ── Search bar ────────────────────────────────────────────────────
        bar_y = 68
        bar_h = 48
        engine.fill_rect(20, bar_y, SCREEN_W - 40, bar_h, 28, 28, 28)
        engine.draw_rect(20, bar_y, SCREEN_W - 40, bar_h, 255, 0, 0, 255, 2)

        display = self.query + "█"
        engine.draw_text(display, engine.font_body, 32, bar_y + 12, 255, 255, 255,
                         max_w=SCREEN_W - 80)

        # ── Keyboard ──────────────────────────────────────────────────────
        for ri, row in enumerate(_ROWS):
            # Centre each row
            total_w = sum(self._key_w(k) for k in row) + _KEY_GAP * (len(row) - 1)
            start_x = (SCREEN_W - total_w) // 2
            x = start_x
            ry = _LAYOUT_Y + ri * (_KEY_H + _KEY_GAP)

            for ci, key in enumerate(row):
                kw = self._key_w(key)
                is_sel = (ri == self.row and ci == self.col)
                if is_sel:
                    engine.fill_rect(x, ry, kw, _KEY_H, 255, 0, 0, 255)
                elif key in ("OK", "SPACE", "⌫"):
                    engine.fill_rect(x, ry, kw, _KEY_H, 60, 60, 60)
                else:
                    engine.fill_rect(x, ry, kw, _KEY_H, 35, 35, 35)
                engine.draw_rect(x, ry, kw, _KEY_H, 70, 70, 70, 255, 1)

                label = key
                tw = engine.text_width(label, engine.font_body)
                engine.draw_text(label, engine.font_body,
                                 x + (kw - tw) // 2, ry + (_KEY_H - 24) // 2,
                                 255, 255, 255)
                x += kw + _KEY_GAP

        self.draw_footer(engine, [
            ("A", "Nhấn phím"), ("START", "Tìm"), ("B", "Hủy"), ("X", "Xóa"),
        ])

    def _key_w(self, key):
        if key == "SPACE":
            return _KEY_W * 3
        if key in ("OK",):
            return _KEY_W * 2
        if key == "⌫":
            return _KEY_W + _KEY_GAP
        return _KEY_W
