# -*- coding: utf-8 -*-
"""Interactive version check and update download screen."""
import threading

from .base import BaseScreen
from zt import updater
from zt.state import SCREEN_W
from zt.version import APP_VERSION


class UpdateScreen(BaseScreen):
    def __init__(self, engine=None):
        super().__init__(engine)
        self.state = "idle"
        self.status = ""
        self.info = None
        self.progress = 0
        self.confirm = False

    def on_enter(self, params=None):
        self.state = "checking"
        self.status = "Đang kiểm tra phiên bản mới…"
        self.info = None
        self.progress = 0
        self.confirm = False
        threading.Thread(target=self._check_worker, daemon=True).start()

    def handle_input(self, inputs):
        if self.confirm:
            if inputs.get("btn_a"):
                self.confirm = False
                self.state = "downloading"
                self.status = "Đang tải và xác minh bản cập nhật…"
                threading.Thread(target=self._download_worker, daemon=True).start()
            elif inputs.get("btn_b"):
                self.confirm = False
                self.status = "Đã hủy cập nhật"
            return True
        if inputs.get("btn_b") and self.state not in ("checking", "downloading"):
            self.engine.pop_screen(); return True
        if inputs.get("btn_a"):
            if self.state == "available":
                self.confirm = True; return True
            if self.state in ("error", "latest"):
                self.on_enter(); return True
        return False

    def _check_worker(self):
        try:
            self.info = updater.check_latest()
            if self.info["newer"]:
                self.state = "available"
                size_mb = self.info["size"] / (1024 * 1024)
                self.status = f"Có bản v{self.info['latest']}  •  {size_mb:.1f} MB"
            else:
                self.state = "latest"
                self.status = "Anh đang dùng phiên bản mới nhất"
        except updater.UpdateError as exc:
            self.state = "error"; self.status = str(exc)
        except Exception:
            self.state = "error"; self.status = "Không thể kiểm tra cập nhật"
        self.engine.mark_dirty()

    def _download_worker(self):
        try:
            updater.download_release(self.info, self._on_progress)
            self.progress = 100
            self.state = "ready"
            self.status = "Đã xác minh. Đang khởi động lại để cài đặt…"
            self.engine.mark_dirty()
            self.engine.quit()
        except updater.UpdateError as exc:
            self.state = "error"; self.status = str(exc)
        except Exception:
            self.state = "error"; self.status = "Không thể chuẩn bị bản cập nhật"
        self.engine.mark_dirty()

    def _on_progress(self, current, total):
        self.progress = int(current * 100 / total) if total else 0
        self.engine.mark_dirty()

    def render(self, engine):
        self.draw_header(engine, "ZimTube", "Cập nhật phần mềm")
        engine.draw_text("PHIÊN BẢN HIỆN TẠI", engine.font_small,
                         70, 105, 135, 135, 135)
        engine.draw_text("v" + APP_VERSION, engine.font_title,
                         70, 135, 255, 255, 255)
        if self.info:
            engine.draw_text("PHIÊN BẢN MỚI NHẤT", engine.font_small,
                             SCREEN_W - 330, 105, 135, 135, 135)
            engine.draw_text("v" + self.info["latest"], engine.font_title,
                             SCREEN_W - 330, 135, 255, 80, 80)
        engine.fill_rect(60, 210, SCREEN_W - 120, 150, 27, 27, 30, 255)
        engine.draw_rect(60, 210, SCREEN_W - 120, 150, 65, 65, 68, 255, 2)
        engine.draw_text(self.status, engine.font_body, SCREEN_W // 2, 242,
                         235, 235, 235, center_x=True, max_w=SCREEN_W - 180)
        if self.state == "downloading":
            engine.fill_rect(110, 300, SCREEN_W - 220, 24, 55, 55, 55)
            engine.fill_rect(110, 300, int((SCREEN_W - 220) * self.progress / 100),
                             24, 255, 0, 0)
            engine.draw_text(f"{self.progress}%", engine.font_small,
                             SCREEN_W // 2, 333, 180, 180, 180, center_x=True)
        elif self.info and self.info.get("notes"):
            note = self.info["notes"].replace("\r", " ").replace("\n", " • ")
            engine.draw_text(note[:120], engine.font_small, 90, 300,
                             155, 155, 155, max_w=SCREEN_W - 180)
        if self.confirm:
            self._draw_confirm(engine)
        elif self.state == "available":
            self.draw_footer(engine, [("A", "Tải bản mới"), ("B", "Quay lại")])
        elif self.state in ("error", "latest"):
            self.draw_footer(engine, [("A", "Kiểm tra lại"), ("B", "Quay lại")])
        else:
            self.draw_footer(engine, [("B", "Quay lại sau khi xong")])

    def _draw_confirm(self, engine):
        x, y, w, h = 150, 165, SCREEN_W - 300, 245
        engine.fill_rect(0, 0, SCREEN_W, 540, 0, 0, 0, 190)
        engine.fill_rect(x, y, w, h, 28, 28, 31, 255)
        engine.draw_rect(x, y, w, h, 255, 0, 0, 255, 3)
        engine.draw_text("CÀI BẢN CẬP NHẬT?", engine.font_title,
                         SCREEN_W // 2, y + 38, 255, 255, 255, center_x=True)
        engine.draw_text("Ứng dụng sẽ tự khởi động lại sau khi tải xong.",
                         engine.font_body, SCREEN_W // 2, y + 100,
                         190, 190, 190, center_x=True)
        engine.draw_text("A  Cập nhật        B  Hủy", engine.font_body,
                         SCREEN_W // 2, y + 170, 255, 100, 100, center_x=True)
