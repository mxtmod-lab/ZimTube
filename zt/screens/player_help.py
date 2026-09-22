# -*- coding: utf-8 -*-
"""Player controls shown before handoff."""
from .base import BaseScreen
from zt import playback, settings
from zt.player import launch_session
from zt.state import SCREEN_W

CONTROLS = (
    ("A", "Tạm dừng / tiếp tục"),
    ("B", "Thoát video, về ZimTube"),
    ("Y", "Bật / tắt tốc độ ×2"),
    ("← / →", "Tua lùi / tới 10 giây"),
    ("↓ / ↑", "Tua lùi / tới 60 giây"),
    ("L1 / R1", "Giảm / tăng âm lượng"),
    ("X", "Mở Quick Menu RetroArch"),
)


class PlayerHelpScreen(BaseScreen):
    def __init__(self, engine=None):
        super().__init__(engine); self.session = None

    def on_enter(self, params=None):
        params = params or {}; self.session = params.get("session")
        if not self.session and params.get("video"):
            opts = settings.load()
            self.session = playback.PlaybackSession(
                params.get("queue") or [params["video"]], params.get("index", 0),
                context=params.get("context", ""), quality=opts["quality"],
                audio_only=opts["audio_only"], autoplay=opts["autoplay"])

    def handle_input(self, inputs):
        if inputs.get("btn_b"):
            self.engine.pop_screen(); return True
        if inputs.get("btn_y"):
            data = settings.load(); data["show_player_help"] = False; settings.save(data)
            self.engine.toast("Đã tắt hướng dẫn lần sau"); return True
        if inputs.get("btn_a") and self.session:
            launch_session(self.engine, self.session); return True
        return False

    def render(self, engine):
        self.draw_header(engine, "ZimTube", "Điều khiển khi xem")
        engine.draw_text("NÚT ĐIỀU KHIỂN VIDEO", engine.font_title, SCREEN_W // 2, 76,
                         255, 255, 255, center_x=True)
        for i, (button, action) in enumerate(CONTROLS):
            y = 125 + i * 56
            engine.fill_rect(110, y - 8, 105, 40, 255, 0, 0, 220)
            engine.draw_text(button, engine.font_body, 162, y + 2, 255, 255, 255, center_x=True)
            engine.draw_text(action, engine.font_body, 245, y + 2, 225, 225, 225)
        self.draw_footer(engine, [("A", "Bắt đầu"), ("Y", "Không hiện nữa"), ("B", "Hủy")])
