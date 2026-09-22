# -*- coding: utf-8 -*-
"""
Home Screen — YouTube-style thumbnail grid (3 columns).
Tabs: Trending | Yêu thích | Lịch sử | [search queries]
"""
import os, threading, time
from .base import BaseScreen
from zt import yt
from zt.paths import YT_CACHE_DIR
from zt.state import SCREEN_W, SCREEN_H

COLS = 3
ROWS_VISIBLE = 3
CARD_W = (SCREEN_W - 40) // COLS           # ~328
CARD_H = 196                               # thumb 160 + text area 36
CARD_GAP = 10
THUMB_H = 152
GRID_X = 20
GRID_Y = 106   # below header + tab bar
TAB_Y  = 58
TAB_H  = 44


class HomeScreen(BaseScreen):
    def __init__(self, engine=None):
        super().__init__(engine)
        self.tabs = []
        self.tab_idx = 0
        self.videos = []
        self.sel = 0           # flat index
        self.scroll_row = 0
        self.loading = False
        self.loading_more = False
        self.has_more = False
        self._load_gen = 0
        self._thumb_threads = {}

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def on_enter(self, params=None):
        self._build_tabs()
        if params and "tab" in params:
            t = params["tab"]
            if t in self.tabs:
                self.tab_idx = self.tabs.index(t)
        self._load_tab()

    def on_resume(self):
        self.engine.mark_dirty()

    # ── Tabs ──────────────────────────────────────────────────────────────

    def _build_tabs(self):
        tabs = ["🔥 Trending"]
        favs = yt.load_favorites()
        if favs:
            tabs.append("♥ Yêu thích")
        history = yt.load_search_history() or []
        for q in history[:6]:
            if q not in tabs:
                tabs.append(q)
        if "Nhạc Việt" not in tabs:
            tabs.append("Nhạc Việt")
        if "Game" not in tabs:
            tabs.append("Game")
        self.tabs = tabs
        if self.tab_idx >= len(self.tabs):
            self.tab_idx = 0

    def _current_query(self):
        if not self.tabs:
            return "Trending"
        return self.tabs[self.tab_idx]

    # ── Loading ───────────────────────────────────────────────────────────

    def _load_tab(self):
        self.loading = True
        self.videos = []
        self.sel = 0
        self.scroll_row = 0
        self.has_more = False
        self.engine.mark_dirty()
        gen = self._load_gen + 1
        self._load_gen = gen
        q = self._current_query()
        threading.Thread(target=self._bg_load, args=(q, gen), daemon=True).start()

    def _bg_load(self, query, gen):
        try:
            if "Trending" in query or "🔥" in query:
                videos = yt.get_trending(limit=18)
            elif "Yêu thích" in query or "♥" in query:
                videos = yt.load_favorites()
            else:
                videos = yt.search_youtube(query, limit=18)
        except Exception:
            videos = []
        if gen != self._load_gen:
            return
        self.videos = videos
        self.loading = False
        self.engine.mark_dirty()
        # Preload thumbnails for first 9 visible
        for v in videos[:9]:
            self._ensure_thumb(v)

    def _ensure_thumb(self, video):
        vid_id = video.get("id", "")
        if not vid_id:
            return
        path = os.path.join(YT_CACHE_DIR, f"{vid_id}.jpg")
        if os.path.exists(path):
            self.engine.mark_dirty()
            return
        if vid_id in self._thumb_threads:
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
        if self.loading:
            return False

        n = len(self.videos)
        if n == 0 and not inputs.get("btn_x") and not inputs.get("btn_b"):
            return False

        dirty = False

        if inputs.get("btn_left"):
            # Switch tab left
            self.tab_idx = (self.tab_idx - 1) % len(self.tabs)
            self._load_tab(); return True

        if inputs.get("btn_right"):
            # Switch tab right
            self.tab_idx = (self.tab_idx + 1) % len(self.tabs)
            self._load_tab(); return True

        if inputs.get("btn_up") and n:
            if self.sel >= COLS:
                self.sel -= COLS
                self._clamp_scroll(); dirty = True

        if inputs.get("btn_down") and n:
            if self.sel + COLS < n:
                self.sel += COLS
            elif self.sel < n - 1:
                self.sel = n - 1
            self._clamp_scroll(); dirty = True
            # Load more when near bottom
            row = self.sel // COLS
            total_rows = (n + COLS - 1) // COLS
            if row >= total_rows - 2 and self.has_more and not self.loading_more:
                self._load_more()

        # Navigate within row
        if inputs.get("btn_l") and n:
            row = self.sel // COLS
            col = self.sel % COLS
            if col > 0:
                self.sel -= 1; dirty = True

        if inputs.get("btn_r") and n:
            row = self.sel // COLS
            col = self.sel % COLS
            if col < COLS - 1 and self.sel + 1 < n:
                self.sel += 1; dirty = True

        if inputs.get("btn_a") and n and self.sel < n:
            self.engine.push_screen("watch", {
                "video": self.videos[self.sel],
                "queue": self.videos,
                "index": self.sel,
                "context": self._current_query(),
            })
            return True

        if inputs.get("btn_x"):
            # Open search keyboard
            self.engine.push_screen("keyboard", {"callback_screen": "home"})
            return True

        if inputs.get("btn_y"):
            # Add to search history and reload
            self.engine.push_screen("keyboard", {"callback_screen": "home"})
            return True

        if inputs.get("btn_b"):
            self.engine.quit()
            return True

        return dirty

    def _clamp_scroll(self):
        row = self.sel // COLS
        if row < self.scroll_row:
            self.scroll_row = row
        elif row >= self.scroll_row + ROWS_VISIBLE:
            self.scroll_row = row - ROWS_VISIBLE + 1

    def _load_more(self):
        self.loading_more = True
        q = self._current_query()
        gen = self._load_gen
        threading.Thread(target=self._bg_more, args=(q, gen), daemon=True).start()

    def _bg_more(self, query, gen):
        token = yt.get_continuation_token(query)
        if not token:
            self.loading_more = False
            return
        try:
            more, new_token = yt.fetch_more_youtube(query, token)
        except Exception:
            more, new_token = [], None
        if gen != self._load_gen:
            return
        if new_token:
            yt.set_continuation_token(query, new_token)
        else:
            self.has_more = False
        self.videos.extend(more)
        for v in more[:6]:
            self._ensure_thumb(v)
        self.loading_more = False
        self.engine.mark_dirty()

    # ── Render ────────────────────────────────────────────────────────────

    def render(self, engine):
        self._draw_header(engine)
        self._draw_tabs(engine)

        if self.loading:
            self._draw_loading(engine)
        elif not self.videos:
            self._draw_empty(engine)
        else:
            self._draw_grid(engine)

        self.draw_footer(engine, [
            ("A", "Xem"), ("X", "Tìm kiếm"),
            ("L/R", "Tab"), ("B", "Thoát"),
        ])

    def _draw_header(self, engine):
        from zt.engine import HEADER_BG
        engine.fill_rect(0, 0, SCREEN_W, 56, *HEADER_BG[:3])
        engine.fill_rect(0, 52, SCREEN_W, 4, 255, 0, 0)
        # Red play-button badge
        engine.fill_rect(12, 13, 38, 28, 255, 0, 0, 255)
        engine.fill_rect(16, 17, 28, 20, 180, 0, 0, 255)
        engine.draw_text("▶", engine.font_small, 22, 18, 255, 255, 255)
        engine.draw_text("ZimTube", engine.font_title, 58, 14, 255, 255, 255)
        # Search hint top-right
        hint = "X = Tìm kiếm"
        engine.draw_text(hint, engine.font_small,
                         SCREEN_W - 16 - engine.text_width(hint, engine.font_small),
                         20, 100, 100, 100)

    def _draw_tabs(self, engine):
        from zt.engine import HEADER_BG, ACCENT
        engine.fill_rect(0, TAB_Y, SCREEN_W, TAB_H, 18, 18, 18)
        x = 16
        for i, tab in enumerate(self.tabs):
            tw = engine.text_width(tab, engine.font_small)
            pad = 16
            bw = tw + pad * 2
            if i == self.tab_idx:
                engine.fill_rect(x, TAB_Y + 4, bw, TAB_H - 8, 255, 0, 0, 220)
                engine.draw_text(tab, engine.font_small, x + pad, TAB_Y + 13, 255, 255, 255)
            else:
                engine.fill_rect(x, TAB_Y + 4, bw, TAB_H - 8, 35, 35, 35)
                engine.draw_text(tab, engine.font_small, x + pad, TAB_Y + 13, 180, 180, 180)
            x += bw + 6
            if x > SCREEN_W - 60:
                break

    def _draw_loading(self, engine):
        msg = "Đang tải..."
        engine.draw_text(msg, engine.font_title,
                         SCREEN_W // 2 - engine.text_width(msg, engine.font_title) // 2,
                         SCREEN_H // 2 - 20, 170, 170, 170)

    def _draw_empty(self, engine):
        msg = "Không có video. Thử tìm kiếm (X)."
        engine.draw_text(msg, engine.font_body,
                         SCREEN_W // 2 - engine.text_width(msg, engine.font_body) // 2,
                         SCREEN_H // 2 - 14, 120, 120, 120)

    def _draw_grid(self, engine):
        n = len(self.videos)
        for row_off in range(ROWS_VISIBLE):
            row = self.scroll_row + row_off
            for col in range(COLS):
                idx = row * COLS + col
                if idx >= n:
                    break
                x = GRID_X + col * (CARD_W + CARD_GAP)
                y = GRID_Y + row_off * (CARD_H + CARD_GAP)
                self._draw_card(engine, idx, x, y)

        # Loading-more indicator
        if self.loading_more:
            engine.draw_text("Đang tải thêm...", engine.font_small,
                             SCREEN_W // 2 - 60, GRID_Y + ROWS_VISIBLE * (CARD_H + CARD_GAP) + 6,
                             100, 100, 100)

    def _draw_card(self, engine, idx, x, y):
        video = self.videos[idx]
        is_sel = (idx == self.sel)

        # Card background
        if is_sel:
            engine.fill_rect(x, y, CARD_W, CARD_H, 40, 40, 40)
            engine.draw_rect(x, y, CARD_W, CARD_H, 255, 0, 0, 255, 3)
        else:
            engine.fill_rect(x, y, CARD_W, CARD_H, 22, 22, 22)
            engine.draw_rect(x, y, CARD_W, CARD_H, 50, 50, 50, 255, 1)

        # Thumbnail
        vid_id = video.get("id", "")
        thumb_path = os.path.join(YT_CACHE_DIR, f"{vid_id}.jpg")
        tex = engine.load_texture(thumb_path)
        if tex:
            engine.draw_texture_fit(tex, x + 2, y + 2, CARD_W - 4, THUMB_H - 4)
        else:
            # Placeholder
            engine.fill_rect(x + 2, y + 2, CARD_W - 4, THUMB_H - 4, 30, 30, 30)
            engine.draw_text("▶", engine.font_title,
                             x + CARD_W // 2 - 12, y + THUMB_H // 2 - 14, 80, 80, 80)
            # Trigger download
            if vid_id and vid_id not in self._thumb_threads:
                self._ensure_thumb(video)

        # Duration badge
        dur = video.get("duration", "")
        if dur:
            dw = engine.text_width(dur, engine.font_small) + 8
            engine.fill_rect(x + CARD_W - dw - 4, y + THUMB_H - 22, dw, 18, 0, 0, 0, 200)
            engine.draw_text(dur, engine.font_small,
                             x + CARD_W - dw - 1, y + THUMB_H - 20, 255, 255, 255)

        # Title
        title = yt.clean_yt_text(video.get("title", ""))
        ty = y + THUMB_H + 4
        engine.draw_text(title, engine.font_small,
                         x + 6, ty, 220, 220, 220, max_w=CARD_W - 12)

        # Views + age
        views = video.get("views", "")
        age   = video.get("age", "")
        meta  = " · ".join(filter(None, [views, age]))
        if meta:
            engine.draw_text(meta, engine.font_small,
                             x + 6, ty + 20, 110, 110, 110, max_w=CARD_W - 12)
