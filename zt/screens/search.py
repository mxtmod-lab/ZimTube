# -*- coding: utf-8 -*-
"""Search results screen — list view of YouTube search results."""
import os, threading
from .base import BaseScreen
from zt import yt
from zt.paths import YT_CACHE_DIR
from zt.state import SCREEN_W, SCREEN_H

ITEM_H = 88
ITEMS_VISIBLE = 7
LIST_Y = 100


class SearchScreen(BaseScreen):
    def __init__(self, engine=None):
        super().__init__(engine)
        self.query = ""
        self.videos = []
        self.sel = 0
        self.scroll = 0
        self.loading = False
        self._gen = 0
        self._thumb_threads = {}

    def on_enter(self, params=None):
        params = params or {}
        q = params.get("query", "")
        if q and q != self.query:
            self.query = q
            self.videos = []
            self.sel = 0
            self.scroll = 0
            self._search()
        self.engine.mark_dirty()

    def on_resume(self):
        self.engine.mark_dirty()

    def _search(self):
        self.loading = True
        gen = self._gen + 1
        self._gen = gen
        threading.Thread(target=self._bg_search, args=(self.query, gen), daemon=True).start()

    def _bg_search(self, query, gen):
        try:
            videos = yt.search_youtube(query, limit=20)
        except Exception:
            videos = []
        if gen != self._gen:
            return
        self.videos = videos
        self.loading = False
        self.engine.mark_dirty()
        for v in videos[:ITEMS_VISIBLE]:
            self._ensure_thumb(v)

    def _ensure_thumb(self, video):
        vid_id = video.get("id", "")
        if not vid_id:
            return
        path = os.path.join(YT_CACHE_DIR, f"{vid_id}.jpg")
        if os.path.exists(path) or vid_id in self._thumb_threads:
            return
        self._thumb_threads[vid_id] = True

        def dl():
            url = video.get("thumbnail") or f"https://i.ytimg.com/vi/{vid_id}/mqdefault.jpg"
            yt.fetch_thumbnail(url, YT_CACHE_DIR, vid_id)
            self._thumb_threads.pop(vid_id, None)
            self.engine.mark_dirty()

        threading.Thread(target=dl, daemon=True).start()

    # ── Input ─────────────────────────────────────────────────────────────

    def handle_input(self, inputs):
        if inputs.get("btn_b"):
            self.engine.pop_screen(); return True

        if inputs.get("btn_x"):
            self.engine.push_screen("keyboard", {
                "callback_screen": "search",
                "initial_query": self.query,
            })
            return True

        if self.loading or not self.videos:
            return False

        n = len(self.videos)
        dirty = False

        if inputs.get("btn_up"):
            if self.sel > 0:
                self.sel -= 1
                if self.sel < self.scroll:
                    self.scroll = self.sel
                dirty = True

        if inputs.get("btn_down"):
            if self.sel < n - 1:
                self.sel += 1
                if self.sel >= self.scroll + ITEMS_VISIBLE:
                    self.scroll = self.sel - ITEMS_VISIBLE + 1
                dirty = True
                # Preload upcoming thumbnails
                for v in self.videos[self.sel:self.sel + 3]:
                    self._ensure_thumb(v)

        if inputs.get("btn_a") and self.sel < n:
            self.engine.push_screen("watch", {
                "video": self.videos[self.sel],
                "queue": self.videos,
                "index": self.sel,
                "context": self.query,
            })
            return True

        return dirty

    # ── Render ────────────────────────────────────────────────────────────

    def render(self, engine):
        self.draw_header(engine, subtitle=f'"{self.query}"')

        # Search bar (shows current query)
        engine.fill_rect(16, 62, SCREEN_W - 32, 34, 28, 28, 28)
        engine.draw_rect(16, 62, SCREEN_W - 32, 34, 60, 60, 60, 255, 1)
        engine.draw_text(f"🔍  {self.query}", engine.font_body, 28, 70, 180, 180, 180,
                         max_w=SCREEN_W - 100)
        engine.draw_text("X=Sửa", engine.font_small,
                         SCREEN_W - 80, 72, 80, 80, 80)

        if self.loading:
            engine.draw_text(f'Đang tìm "{self.query}"...', engine.font_body,
                             SCREEN_W // 2 - 130, SCREEN_H // 2 - 14, 150, 150, 150)
        elif not self.videos:
            engine.draw_text("Không tìm thấy kết quả.", engine.font_body,
                             SCREEN_W // 2 - 120, SCREEN_H // 2 - 14, 100, 100, 100)
        else:
            self._draw_list(engine)

        self.draw_footer(engine, [
            ("A", "Xem"), ("X", "Sửa tìm kiếm"), ("B", "Quay lại"),
        ])

    def _draw_list(self, engine):
        n = len(self.videos)
        for off in range(ITEMS_VISIBLE):
            idx = self.scroll + off
            if idx >= n:
                break
            y = LIST_Y + off * ITEM_H
            self._draw_item(engine, idx, y)

        # Scroll indicator
        if n > ITEMS_VISIBLE:
            total_h = SCREEN_H - LIST_Y - 40
            thumb_h = max(30, int(total_h * ITEMS_VISIBLE / n))
            thumb_y = LIST_Y + int(total_h * self.scroll / n)
            engine.fill_rect(SCREEN_W - 6, LIST_Y, 4, total_h, 40, 40, 40)
            engine.fill_rect(SCREEN_W - 6, thumb_y, 4, thumb_h, 180, 0, 0)

    def _draw_item(self, engine, idx, y):
        video = self.videos[idx]
        is_sel = (idx == self.sel)
        w = SCREEN_W - 12

        if is_sel:
            engine.fill_rect(6, y, w, ITEM_H - 4, 38, 38, 38)
            engine.draw_rect(6, y, w, ITEM_H - 4, 255, 0, 0, 255, 2)
        else:
            engine.fill_rect(6, y, w, ITEM_H - 4, 22, 22, 22)
            engine.fill_rect(6, y + ITEM_H - 5, w, 1, 40, 40, 40)

        # Thumbnail
        vid_id = video.get("id", "")
        tp = os.path.join(YT_CACHE_DIR, f"{vid_id}.jpg")
        tex = engine.load_texture(tp)
        tw, th = 120, 74
        tx, ty = 14, y + 6
        if tex:
            engine.draw_texture_fit(tex, tx, ty, tw, th)
        else:
            engine.fill_rect(tx, ty, tw, th, 32, 32, 32)
            engine.draw_text("▶", engine.font_body,
                             tx + tw // 2 - 10, ty + th // 2 - 12, 70, 70, 70)
            self._ensure_thumb(video)

        # Duration badge
        dur = video.get("duration", "")
        if dur:
            dw = engine.text_width(dur, engine.font_small) + 6
            engine.fill_rect(tx + tw - dw - 2, ty + th - 20, dw, 16, 0, 0, 0, 210)
            engine.draw_text(dur, engine.font_small,
                             tx + tw - dw, ty + th - 18, 255, 255, 255)

        # Title
        title = yt.clean_yt_text(video.get("title", ""))
        info_x = tx + tw + 14
        info_w = w - tw - 24
        engine.draw_text(title, engine.font_body, info_x, y + 8, 230, 230, 230,
                         max_w=info_w)
        engine.draw_text(title[40:] if len(title) > 40 else "", engine.font_body,
                         info_x, y + 32, 200, 200, 200, max_w=info_w)

        # Channel + meta
        chan  = yt.clean_yt_text(video.get("channel", ""))
        views = video.get("views", "")
        age   = video.get("age", "")
        meta  = " · ".join(filter(None, [chan, views, age]))
        engine.draw_text(meta, engine.font_small, info_x, y + 56, 110, 110, 110,
                         max_w=info_w)

        # Number badge
        engine.draw_text(str(idx + 1), engine.font_small,
                         SCREEN_W - 32, y + (ITEM_H - 20) // 2, 70, 70, 70)
