# -*- coding: utf-8 -*-
"""Playback backend and safe session handoff for ZimTube."""
import os

from . import playback
from .paths import APP_DIR, YT_SESSION_FILE


class PlayerBackend:
    name = "base"
    capabilities = {
        "seek_absolute": False,
        "audio_only": False,
        "quality_select": False,
        "speed": False,
    }

    def play(self, video, start=0.0, audio_only=False, duration=0.0,
             session=None):
        raise NotImplementedError


class RetroArchBackend(PlayerBackend):
    name = "retroarch"
    capabilities = {
        "seek_absolute": False,
        "audio_only": True,
        "quality_select": True,
        "speed": True,
    }

    def play(self, video, start=0.0, audio_only=False, duration=0.0,
             session=None):
        from .yt_player import play_video
        return play_video(
            video.get("id", ""),
            direct_title=video.get("title", ""),
            audio_only=audio_only,
            quality=getattr(session, "quality", "360p") if session else "360p",
            local_path=video.get("local_path"),
        )


def get_backend(name="retroarch"):
    return RetroArchBackend()


def build_session_command(session_path=None):
    session_path = session_path or YT_SESSION_FILE
    safe_path = str(session_path).replace('"', '\\"').replace('$', '\\$')
    return """#!/bin/sh
SDCARD_PATH="${SDCARD_PATH:-/mnt/SDCARD}"
APP_DIR="$SDCARD_PATH/Apps/ZimTube"
LOG_FILE="$SDCARD_PATH/ZimTube-yt.log"
export LD_LIBRARY_PATH="/mnt/SDCARD/System/lib:/usr/trimui/lib:$LD_LIBRARY_PATH"
PY3="python3"
if [ -f "$APP_DIR/python/bin/python3" ]; then
    PY3="$APP_DIR/python/bin/python3"
elif [ -f "$SDCARD_PATH/System/bin/python3" ]; then
    PY3="$SDCARD_PATH/System/bin/python3"
elif [ -f "$SDCARD_PATH/.zimtube/python/bin/python3" ]; then
    PY3="$SDCARD_PATH/.zimtube/python/bin/python3"
elif [ -f "$SDCARD_PATH/Apps/RetroHub/python/bin/python3" ]; then
    PY3="$SDCARD_PATH/Apps/RetroHub/python/bin/python3"
fi
cd "$APP_DIR" || exit 1
"$PY3" -m zt.yt_player --session "__SESSION__" >> "$LOG_FILE" 2>&1
exit $?
""".replace("__SESSION__", safe_path)


def launch_session(engine, session):
    try:
        if not playback.save_session(session):
            raise OSError("Không lưu được phiên phát")
        with open("/tmp/launch_game.sh", "w", encoding="utf-8") as f:
            f.write(build_session_command())
        os.chmod("/tmp/launch_game.sh", 0o755)
        engine.quit()
        return True
    except Exception as exc:
        if hasattr(engine, "toast"):
            engine.toast("Lỗi mở video: %s" % exc)
        return False
