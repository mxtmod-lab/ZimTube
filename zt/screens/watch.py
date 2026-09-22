# -*- coding: utf-8 -*-
"""Watch Screen — video detail + play button + related videos."""
import os, threading
from .base import BaseScreen
from zt import playback, settings, yt
from zt.player import launch_session
from zt.paths import YT_CACHE_DIR
from zt.state import SCREEN_W, SCREEN_H

FOCUS_PLAY = 0
FOCUS_FAV  = 1
FOCUS_LIST = 2


class WatchScreen(BaseScreen):
    def __init__(self, engine=None):
        super().__init__(engine)
        self.video = {}
        self.queue = []
        self.index = 0
        self.context = ""
        self.related = []
        self.focus = FOCUS_PLAY
        self.rel_sel = 0
        self.is_fav = False
        self.loading_meta = False
        self.starting = False
        self._gen = 0

    def on_enter(self, params=None):
        params = params or {}
        self.video  = params.get("video") or {}
        self.queue  = params.get("queue") or [self.video]
        self.index  = params.get("index", 0)
        self.context = params.get("context", "")
        self.related = []
        self.focus   = FOCUS_PLAY
        self.rel_sel = 0
        self.starting = False
        favs = yt.load_favorites()
        self.is_fav = yt.is_favorite(self.video.get("id", ""), favs)
        self._fetch_meta()

    def on_resume(self):
        self.engine.mark_dirty()

    def _fetch_meta(self):
        vid_id = self.video.get("id", "")
        if not vid_id:
            return
        self.loading_meta = True
        gen = self._gen + 1
        self._gen = gen
        threading.Thread(target=self._bg_meta, args=(vid_id, gen), daemon=True).start()

        # Ensure thumbnail
        thumb_path = os.path.join(YT_CACHE_DIR, f"{vid_id}.jpg")
        if not os.path.exists(thumb_path):
            url = self.video.get("thumbnail") or f"https://i.ytimg.com/vi/{vid_id}/mqdefault.jpg"
            threading.Thread(target=yt.fetch_thumbnail,
                             args=(url, YT_CACHE_DIR, vid_id), daemon=True).start()

    def _bg_meta(self, vid_id, gen):
        try:
            meta = yt.fetch_watch_metadata(vid_id)
            related = meta.get("related", [])[:8]
        except Exception:
            related = []
        if gen != self._gen:
            return
        self.related = related
        self.loading_meta = False
        self.engine.mark_dirty()
        for v in related[:4]:
            rid = v.get("id", "")
            if rid:
                rp = os.path.join(YT_CACHE_DIR, f"{rid}.jpg")
                if not os.path.exists(rp):
                    url = v.get("thumbnail") or f"https://i.ytimg.com/vi/{rid}/mqdefault.jpg"
                    threading.Thread(target=yt.fetch_thumbnail,
                                     args=(url, YT_CACHE_DIR, rid), daemon=True).start()

    # ── Input ─────────────────────────────────────────────────────────────

    def handle_input(self, inputs):
        dirty = False

        if inputs.get("btn_b"):
            self.engine.pop_screen(); return True

        if inputs.get("btn_up"):
            if self.focus == FOCUS_LIST and self.rel_sel > 0:
                self.rel_sel -= 1; dirty = True
            elif self.focus == FOCUS_LIST and self.rel_sel == 0:
                self.focus = FOCUS_PLAY; dirty = True
            elif self.focus == FOCUS_FAV:
                self.focus = FOCUS_PLAY; dirty = True

        if inputs.get("btn_down"):
            if self.focus == FOCUS_PLAY:
                self.focus = FOCUS_FAV; dirty = True
            elif self.focus == FOCUS_FAV:
                if self.related:
                    self.focus = FOCUS_LIST; self.rel_sel = 0; dirty = True
            elif self.focus == FOCUS_LIST:
                if self.rel_sel < len(self.related) - 1:
                    self.rel_sel += 1; dirty = True

        if inputs.get("btn_left") and self.focus in (FOCUS_PLAY, FOCUS_FAV):
            if self.focus == FOCUS_FAV:
                self.focus = FOCUS_PLAY; dirty = True

        if inputs.get("btn_right") and self.focus in (FOCUS_PLAY, FOCUS_FAV):
            if self.focus == FOCUS_PLAY:
                self.focus = FOCUS_FAV; dirty = True

        if inputs.get("btn_a"):
            if self.focus == FOCUS_PLAY:
                self._play()
                return True
            elif self.focus == FOCUS_FAV:
                self._toggle_fav(); dirty = True
            elif self.focus == FOCUS_LIST and self.related:
                self.engine.push_screen("watch", {
                    "video": self.related[self.rel_sel],
                    "queue": self.related,
                    "index": self.rel_sel,
                    "context": "related",
                })
                return True

        # Queue navigation: physical L1 = previous, R1 = next.
        if inputs.get("btn_l") and self.index > 0:
            self.index -= 1
            self.video = self.queue[self.index]
            self._fetch_meta(); dirty = True

        if inputs.get("btn_r") and self.index < len(self.queue) - 1:
            self.index += 1
            self.video = self.queue[self.index]
            self._fetch_meta(); dirty = True

        return dirty

    def _play(self):
        if self.starting:
            return
        vid_id = self.video.get("id", "")
        if not vid_id:
            self.engine.toast("Không có video ID!")
            return
        opts = settings.load()
        sess = playback.PlaybackSession(
            queue=self.queue or [self.video], index=self.index,
            mode="queue" if len(self.queue) > 1 else "single",
            context=self.context, audio_only=opts["audio_only"],
            quality=opts["quality"], autoplay=opts["autoplay"],
        )
        self.starting = True
        self.engine.toast("Đang chuẩn bị video…", 5)
        if opts.get("show_player_help"):
            self.engine.push_screen("player_help", {"session": sess})
            self.starting = False
        elif not launch_session(self.engine, sess):
            self.starting = False

    def _download(self):
        self.engine.push_screen("downloads", {"video": self.video})

    def _toggle_fav(self):
        favs = yt.load_favorites()
        self.is_fav, favs = yt.toggle_favorite(self.video, favs)
        yt.save_favorites(favs)
        self.engine.toast("♥ Đã thêm yêu thích" if self.is_fav else "Đã bỏ yêu thích")

    # ── Render ────────────────────────────────────────────────────────────

    def render(self, engine):
        self.draw_header(engine, subtitle=self.context)
        self._draw_content(engine)
        hints = [("A", "Phát"), ("MENU", "Chức năng"),
                 ("B", "Quay lại"), ("L/R", "Trước/Sau")]
        self.draw_footer(engine, hints)

    def _draw_content(self, engine):
        # Left panel: thumbnail + info + buttons (60% width)
        lw = int(SCREEN_W * 0.60)
        rw = SCREEN_W - lw - 10
        rx = lw + 10
        content_y = 64

        # ── Thumbnail ────────────────────────────────────────────────────
        vid_id = self.video.get("id", "")
        thumb_path = os.path.join(YT_CACHE_DIR, f"{vid_id}.jpg")
        thumb_h = 230
        tex = engine.load_texture(thumb_path)
        if tex:
            engine.draw_texture_fit(tex, 10, content_y, lw - 20, thumb_h)
        else:
            engine.fill_rect(10, content_y, lw - 20, thumb_h, 30, 30, 30)
            engine.draw_text("▶", engine.font_title,
                             10 + (lw - 20) // 2 - 14, content_y + thumb_h // 2 - 18,
                             80, 80, 80)

        # ── Title ────────────────────────────────────────────────────────
        title = yt.clean_yt_text(self.video.get("title", "Không có tiêu đề"))
        ty = content_y + thumb_h + 10
        engine.draw_text(title, engine.font_body, 10, ty, 240, 240, 240, max_w=lw - 20)
        engine.draw_text(title if len(title) < 40 else title[40:], engine.font_body,
                         10, ty + 24, 240, 240, 240, max_w=lw - 20)

        # ── Meta ─────────────────────────────────────────────────────────
        views = self.video.get("views", "")
        age   = self.video.get("age", "")
        meta  = " · ".join(str(x) for x in [views, age] if x)
        my = ty + 52
        engine.draw_text(meta, engine.font_small, 10, my, 110, 110, 110)


        # ── Buttons ──────────────────────────────────────────────────────
        by = my + 32
        # Play button
        play_sel = (self.focus == FOCUS_PLAY)
        bw = 180
        engine.fill_rect(10, by, bw, 44,
                         *(255, 0, 0) if play_sel else (50, 50, 50))
        engine.draw_rect(10, by, bw, 44, 255, 0, 0, 255, 2 if play_sel else 0)
        engine.draw_text("▶  PHÁT VIDEO", engine.font_body,
                         10 + bw // 2 - engine.text_width("▶  PHÁT VIDEO", engine.font_body) // 2,
                         by + 12, 255, 255, 255)

        # Fav button
        fav_sel = (self.focus == FOCUS_FAV)
        fx = 10 + bw + 16
        heart = "♥ Bỏ thích" if self.is_fav else "♡ Yêu thích"
        fw = 160
        engine.fill_rect(fx, by, fw, 44,
                         *(180, 0, 0) if (fav_sel and self.is_fav) else
                         (50, 50, 50) if not fav_sel else (60, 60, 60))
        engine.draw_rect(fx, by, fw, 44, 255, 0, 0, 255, 2 if fav_sel else 0)
        engine.draw_text(heart, engine.font_body,
                         fx + fw // 2 - engine.text_width(heart, engine.font_body) // 2,
                         by + 12, 220, 220, 220)

        # ── Right panel: related videos ───────────────────────────────────
        engine.draw_text("Video liên quan", engine.font_small, rx, content_y, 150, 150, 150)
        engine.fill_rect(rx, content_y + 22, rw, 1, 50, 50, 50)

        if self.loading_meta:
            engine.draw_text("Đang tải...", engine.font_small,
                             rx, content_y + 34, 80, 80, 80)
        else:
            for i, rv in enumerate(self.related[:6]):
                ry = content_y + 34 + i * 76
                is_rsel = (self.focus == FOCUS_LIST and i == self.rel_sel)
                if is_rsel:
                    engine.fill_rect(rx - 4, ry - 4, rw + 4, 72, 40, 40, 40)
                    engine.draw_rect(rx - 4, ry - 4, rw + 4, 72, 255, 0, 0, 255, 2)

                # Small thumbnail
                rid = rv.get("id", "")
                rp  = os.path.join(YT_CACHE_DIR, f"{rid}.jpg")
                rtex = engine.load_texture(rp)
                tw, th = 100, 60
                if rtex:
                    engine.draw_texture_fit(rtex, rx, ry, tw, th)
                else:
                    engine.fill_rect(rx, ry, tw, th, 35, 35, 35)
                    engine.draw_text("▶", engine.font_small,
                                     rx + tw // 2 - 8, ry + th // 2 - 10, 70, 70, 70)

                # Title + meta
                rt = yt.clean_yt_text(rv.get("title", ""))
                engine.draw_text(rt, engine.font_small,
                                 rx + tw + 8, ry + 4, 200, 200, 200,
                                 max_w=rw - tw - 12)
                rmeta = " · ".join(str(x) for x in [rv.get("views", ""), rv.get("age", "")] if x)
                engine.draw_text(rmeta, engine.font_small,
                                 rx + tw + 8, ry + 26, 100, 100, 100,
                                 max_w=rw - tw - 12)
                rdur = rv.get("duration", "")
                if rdur:
                    engine.draw_text(rdur, engine.font_small,
                                     rx + tw + 8, ry + 44, 80, 80, 80)
