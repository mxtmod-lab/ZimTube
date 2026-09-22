# -*- coding: utf-8 -*-
"""ZimTube settings screen."""
from .base import BaseScreen
from zt import playback, settings
from zt.state import SCREEN_W

ROWS = (
    ("quality", "Chất lượng", ("auto", "240p", "360p", "480p", "720p")),
    ("autoplay", "Tự phát tiếp", None),
    ("audio_only", "Chỉ nghe / tắt màn hình", None),
    ("show_player_help", "Hiện hướng dẫn trước phát", None),
    ("save_history", "Lưu lịch sử", None),
)


class SettingsScreen(BaseScreen):
    def __init__(self, engine=None):
        super().__init__(engine); self.sel = 0; self.data = {}

    def on_enter(self, params=None):
        self.data = settings.load()

    def handle_input(self, inputs):
        if inputs.get("btn_b"):
            settings.save(self.data); self.engine.pop_screen(); return True
        if inputs.get("btn_up"):
            self.sel = (self.sel - 1) % len(ROWS); return True
        if inputs.get("btn_down"):
            self.sel = (self.sel + 1) % len(ROWS); return True
        if inputs.get("btn_left") or inputs.get("btn_right") or inputs.get("btn_a"):
            key, _, choices = ROWS[self.sel]
            if choices:
                cur = choices.index(self.data.get(key)) if self.data.get(key) in choices else 0
                step = -1 if inputs.get("btn_left") else 1
                self.data[key] = choices[(cur + step) % len(choices)]
            else:
                self.data[key] = not bool(self.data.get(key))
            settings.save(self.data); return True
        if inputs.get("btn_y"):
            playback.clear_progress(); playback.clear_watched()
            self.engine.toast("Đã xóa lịch sử và tiến độ"); return True
        return False

    def render(self, engine):
        self.draw_header(engine, "ZimTube", "Cài đặt")
        for i, (key, label, _) in enumerate(ROWS):
            y = 95 + i * 74
            if i == self.sel:
                engine.fill_rect(28, y - 12, SCREEN_W - 56, 58, 50, 32, 32)
                engine.draw_rect(28, y - 12, SCREEN_W - 56, 58, 255, 0, 0, 255, 2)
            engine.draw_text(label, engine.font_body, 48, y, 240, 240, 240)
            value = self.data.get(key)
            shown = ("Bật" if value else "Tắt") if isinstance(value, bool) else str(value)
            engine.draw_text(shown, engine.font_body, SCREEN_W - 190, y, 255, 90, 90)
        engine.draw_text("480p/720p tự hạ xuống 360p nếu video không có luồng phù hợp.",
                         engine.font_small, 38, 490, 130, 130, 130)
        self.draw_footer(engine, [("←/→", "Đổi"), ("A", "Bật/tắt"), ("Y", "Xóa LS"), ("B", "Lưu")])
