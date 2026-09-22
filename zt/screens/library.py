# -*- coding: utf-8 -*-
"""Continue-watching, history, and offline library."""
from .base import BaseScreen
from zt import playback, yt
from zt.player import launch_session
from zt.state import SCREEN_W, SCREEN_H

TABS = ("Lịch sử", "Đã tải")


class LibraryScreen(BaseScreen):
    def __init__(self, engine=None):
        super().__init__(engine)
        self.tab = 0
        self.sel = 0
        self.items = []

    def on_enter(self, params=None):
        self._reload()

    def on_resume(self):
        self._reload()

    def _reload(self):
        if self.tab == 0:
            self.items = playback.load_watched()
        else:
            self.items = yt.load_downloads()
        self.sel = min(self.sel, max(0, len(self.items) - 1))
        self.engine.mark_dirty()

    def handle_input(self, inputs):
        if inputs.get("btn_b"):
            self.engine.pop_screen(); return True
        if inputs.get("btn_l"):
            self.tab = (self.tab - 1) % len(TABS); self.sel = 0; self._reload(); return True
        if inputs.get("btn_r"):
            self.tab = (self.tab + 1) % len(TABS); self.sel = 0; self._reload(); return True
        if inputs.get("btn_up") and self.sel > 0:
            self.sel -= 1; return True
        if inputs.get("btn_down") and self.sel + 1 < len(self.items):
            self.sel += 1; return True
        if inputs.get("btn_y") and self.items:
            item = self.items[self.sel]
            if self.tab == 1:
                yt.delete_download(item.get("id"), item.get("kind"))
            else:
                playback.remove_watched(item.get("id")); playback.clear_progress(item.get("id"))
            self._reload(); return True
        if inputs.get("btn_a") and self.items:
            item = dict(self.items[self.sel])
            if self.tab == 1:
                item["local_path"] = item.get("local_path")
            sess = playback.PlaybackSession([item], audio_only=item.get("kind") == "audio")
            launch_session(self.engine, sess); return True
        return False

    def render(self, engine):
        self.draw_header(engine, "ZimTube", "Thư viện")
        x = 20
        for i, tab in enumerate(TABS):
            w = engine.text_width(tab, engine.font_small) + 28
            engine.fill_rect(x, 66, w, 38, *(255, 0, 0) if i == self.tab else (40, 40, 40))
            engine.draw_text(tab, engine.font_small, x + 14, 77, 255, 255, 255)
            x += w + 10
        if not self.items:
            engine.draw_text("Chưa có nội dung", engine.font_body, SCREEN_W // 2, 240,
                             120, 120, 120, center_x=True)
        else:
            start = max(0, self.sel - 5)
            for row, item in enumerate(self.items[start:start + 11]):
                idx = start + row; y = 118 + row * 47
                if idx == self.sel:
                    engine.fill_rect(18, y - 4, SCREEN_W - 36, 42, 55, 32, 32)
                    engine.draw_rect(18, y - 4, SCREEN_W - 36, 42, 255, 0, 0, 255, 2)
                title = yt.clean_yt_text(item.get("title") or item.get("id", ""))
                engine.draw_text(title, engine.font_body, 30, y + 4, 235, 235, 235, max_w=SCREEN_W - 190)
                if self.tab == 1:
                    engine.draw_text(item.get("kind", "video"), engine.font_small,
                                     SCREEN_W - 100, y + 7, 160, 160, 160)
        self.draw_footer(engine, [("A", "Phát"), ("Y", "Xóa"), ("L/R", "Tab"), ("B", "Lại")])
