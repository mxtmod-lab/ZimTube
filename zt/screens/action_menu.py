# -*- coding: utf-8 -*-
"""Context action menu opened by the TrimUI bottom function button."""
from .base import BaseScreen
from zt.state import SCREEN_W, SCREEN_H
from zt.version import APP_VERSION


class ActionMenuScreen(BaseScreen):
    def __init__(self, engine=None):
        super().__init__(engine)
        self.source = "home"
        self.sel = 0
        self.items = []
        self.show_guide = False

    def on_enter(self, params=None):
        self.source = (params or {}).get("source", "home")
        self.sel = 0
        self.show_guide = False
        self.items = [
            ("download", "Tải offline", "Tải video đang chọn về thẻ nhớ"),
        ]
        if self.source == "watch":
            self.items.append(
                ("player_help", "Hướng dẫn nút xem", "Xem các nút điều khiển player")
            )
        self.items.extend([
            ("library", "Thư viện", "Lịch sử và nội dung đã tải"),
            ("settings", "Cài đặt", "Chất lượng, tự phát và audio-only"),
            ("update", "Kiểm tra cập nhật", f"Phiên bản hiện tại: v{APP_VERSION}"),
            ("guide", "Hướng dẫn giao diện", "Cách đổi tab và di chuyển danh sách"),
        ])

    def handle_input(self, inputs):
        if inputs.get("btn_menu") or inputs.get("btn_b"):
            if self.show_guide:
                self.show_guide = False
            else:
                self.engine.pop_screen()
            return True
        if self.show_guide:
            return False
        if inputs.get("btn_up"):
            self.sel = (self.sel - 1) % len(self.items); return True
        if inputs.get("btn_down"):
            self.sel = (self.sel + 1) % len(self.items); return True
        if inputs.get("btn_a"):
            self._activate(self.items[self.sel][0]); return True
        return False

    def _activate(self, action):
        source_screen = self.engine.get_screen(self.source)
        if action == "download" and source_screen:
            if self.source == "watch":
                video = source_screen.video
            else:
                videos = getattr(source_screen, "videos", [])
                index = getattr(source_screen, "sel", 0)
                video = videos[index] if videos and index < len(videos) else {}
            if video:
                self.engine.push_screen("downloads", {"video": video})
            else:
                self.engine.toast("Chưa chọn được video để tải")
        elif action == "player_help" and source_screen:
            self.engine.push_screen("player_help", {
                "video": source_screen.video, "queue": source_screen.queue,
                "index": source_screen.index, "context": source_screen.context,
            })
        elif action == "library":
            self.engine.push_screen("library")
        elif action == "settings":
            self.engine.push_screen("settings")
        elif action == "update":
            self.engine.push_screen("update")
        elif action == "guide":
            self.show_guide = True

    def render(self, engine):
        engine.fill_rect(0, 0, SCREEN_W, SCREEN_H, 8, 8, 10, 255)
        engine.fill_rect(135, 62, SCREEN_W - 270, SCREEN_H - 124, 24, 24, 27, 255)
        engine.draw_rect(135, 62, SCREEN_W - 270, SCREEN_H - 124, 255, 0, 0, 255, 3)
        if self.show_guide:
            self._draw_guide(engine); return
        engine.draw_text("CHỨC NĂNG", engine.font_title, SCREEN_W // 2, 88,
                         255, 255, 255, center_x=True)
        engine.draw_text("Nút MENU / PLAY GAME", engine.font_small,
                         SCREEN_W // 2, 122, 150, 150, 150, center_x=True)
        spacing = 61 if len(self.items) >= 6 else 68
        start_y = 147
        for i, (_, title, subtitle) in enumerate(self.items):
            y = start_y + i * spacing
            if i == self.sel:
                engine.fill_rect(175, y - 8, SCREEN_W - 350, 55, 62, 30, 32)
                engine.draw_rect(175, y - 8, SCREEN_W - 350, 55, 255, 0, 0, 255, 2)
            engine.draw_text(title, engine.font_body, 198, y, 245, 245, 245)
            engine.draw_text(subtitle, engine.font_small, 198, y + 26,
                             145, 145, 145, max_w=SCREEN_W - 410)
        self.draw_footer(engine, [("A", "Mở"), ("↑/↓", "Chọn"), ("MENU/B", "Đóng")])

    def _draw_guide(self, engine):
        engine.draw_text("HƯỚNG DẪN GIAO DIỆN", engine.font_title,
                         SCREEN_W // 2, 92, 255, 255, 255, center_x=True)
        rows = [
            ("L1 / R1", "Đổi tab hoặc video trước / sau"),
            ("D-pad ← / →", "Di chuyển đúng chiều trong danh sách"),
            ("D-pad ↑ / ↓", "Di chuyển lên / xuống"),
            ("A", "Mở mục đang chọn"), ("B", "Quay lại"),
            ("MENU", "Mở / đóng bảng chức năng này"),
        ]
        for i, (button, action) in enumerate(rows):
            y = 158 + i * 58
            engine.fill_rect(185, y - 7, 170, 40, 255, 0, 0, 220)
            engine.draw_text(button, engine.font_small, 270, y + 4,
                             255, 255, 255, center_x=True)
            engine.draw_text(action, engine.font_body, 390, y + 2, 225, 225, 225)
        self.draw_footer(engine, [("MENU/B", "Quay lại")])
