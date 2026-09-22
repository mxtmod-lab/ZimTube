# -*- coding: utf-8 -*-
"""Offline downloader with progress and cancellation."""
import shutil
import threading
from .base import BaseScreen
from zt import yt
from zt.paths import YT_DOWNLOAD_DIR
from zt.state import SCREEN_W


class DownloadsScreen(BaseScreen):
    def __init__(self, engine=None):
        super().__init__(engine)
        self.video = {}; self.kind = "video"; self.running = False
        self.cancelled = False; self.progress = (0, 0, 0, 0); self.error = ""

    def on_enter(self, params=None):
        self.video = (params or {}).get("video") or {}
        self.kind = "video"; self.error = ""

    def handle_input(self, inputs):
        if inputs.get("btn_b"):
            if self.running:
                self.cancelled = True; self.engine.toast("Đang hủy tải…")
            else:
                self.engine.pop_screen()
            return True
        if not self.running and (inputs.get("btn_left") or inputs.get("btn_right")):
            self.kind = "audio" if self.kind == "video" else "video"; return True
        if not self.running and inputs.get("btn_a"):
            self._start(); return True
        return False

    def _start(self):
        if not self.video.get("id"):
            self.engine.toast("Video không hợp lệ"); return
        try:
            free = shutil.disk_usage(YT_DOWNLOAD_DIR).free
            if free < 100 * 1024 * 1024:
                self.engine.toast("Không đủ dung lượng trống"); return
        except OSError:
            pass
        self.running = True; self.cancelled = False; self.error = ""
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        func = yt.download_audio_stream if self.kind == "audio" else yt.download_video_stream
        _, _, err = func(self.video.get("id"), self._progress, lambda: self.cancelled)
        self.running = False; self.error = err or ""
        self.engine.toast(err if err else "Đã tải xong")
        self.engine.mark_dirty()

    def _progress(self, pct, cur, total, speed):
        self.progress = (pct, cur, total, speed); self.engine.mark_dirty()

    def render(self, engine):
        self.draw_header(engine, "ZimTube", "Tải offline")
        title = yt.clean_yt_text(self.video.get("title", "Chọn tải xuống"))
        engine.draw_text(title, engine.font_title, 40, 92, 245, 245, 245, max_w=SCREEN_W - 80)
        engine.draw_text("Loại:", engine.font_body, 70, 175, 180, 180, 180)
        label = "Video 360p" if self.kind == "video" else "Audio-only"
        engine.fill_rect(210, 157, 220, 50, 255, 0, 0)
        engine.draw_text(label, engine.font_body, 320, 172, 255, 255, 255, center_x=True)
        pct, cur, total, speed = self.progress
        engine.fill_rect(70, 265, SCREEN_W - 140, 28, 45, 45, 45)
        engine.fill_rect(70, 265, int((SCREEN_W - 140) * max(0, min(100, pct)) / 100), 28, 255, 0, 0)
        status = (f"{pct}%  •  {cur:.1f}/{total:.1f} MB  •  {speed:.1f} MB/s"
                  if self.running else (self.error or "A để bắt đầu tải"))
        engine.draw_text(status, engine.font_body, SCREEN_W // 2, 320,
                         220, 220, 220, center_x=True)
        engine.draw_text("Lưu tại: " + YT_DOWNLOAD_DIR, engine.font_small, 70, 385,
                         110, 110, 110, max_w=SCREEN_W - 140)
        hints = [("B", "Hủy")] if self.running else [("←/→", "Video/Audio"), ("A", "Tải"), ("B", "Lại")]
        self.draw_footer(engine, hints)
