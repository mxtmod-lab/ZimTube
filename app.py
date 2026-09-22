# -*- coding: utf-8 -*-
"""ZimTube - Standalone YouTube App for TrimUI Handhelds."""

import os, sys

# Vendor SDL2 path
VENDOR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor")
if os.path.isdir(VENDOR_PATH):
    sys.path.insert(0, VENDOR_PATH)

_LIBS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libs")
os.environ["PYSDL2_DLL_PATH"] = os.environ.get("PYSDL2_DLL_PATH") or \
    f"{_LIBS}:/usr/trimui/lib:/usr/lib64:/usr/lib"

from zt.engine import ZimTubeEngine
from zt.screens.home import HomeScreen
from zt.screens.search import SearchScreen
from zt.screens.watch import WatchScreen
from zt.screens.keyboard import KeyboardScreen
from zt.screens.library import LibraryScreen
from zt.screens.downloads import DownloadsScreen
from zt.screens.settings_screen import SettingsScreen
from zt.screens.player_help import PlayerHelpScreen
from zt.screens.action_menu import ActionMenuScreen
from zt.screens.update_screen import UpdateScreen
from zt import updater


def main():
    engine = ZimTubeEngine()
    engine.init_sdl()
    if not engine.init_fonts():
        sys.exit(1)

    engine.register_screen("home",        HomeScreen(engine))
    engine.register_screen("search",      SearchScreen(engine))
    engine.register_screen("watch",       WatchScreen(engine))
    engine.register_screen("keyboard",    KeyboardScreen(engine))
    engine.register_screen("library",     LibraryScreen(engine))
    engine.register_screen("downloads",   DownloadsScreen(engine))
    engine.register_screen("settings",    SettingsScreen(engine))
    engine.register_screen("player_help", PlayerHelpScreen(engine))
    engine.register_screen("action_menu", ActionMenuScreen(engine))
    engine.register_screen("update",      UpdateScreen(engine))

    update_message = updater.consume_result()
    if update_message:
        engine.toast(update_message, 7)

    error_marker = "/tmp/yt_last_error.txt"
    if os.path.exists(error_marker):
        try:
            with open(error_marker, "r", encoding="utf-8") as f:
                message = f.read().strip()
            if message:
                engine.toast(message, 6)
            os.remove(error_marker)
        except OSError:
            pass

    engine.run()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback, time
        err = traceback.format_exc()
        sys.stderr.write(f"\n[ZimTube Crash]\n{err}\n")
        try:
            p = os.path.join(os.environ.get("SDCARD_PATH", "/mnt/SDCARD"), "ZimTube-loi.txt")
            with open(p, "a") as f:
                f.write(f"\n[Crash {time.strftime('%Y-%m-%d %H:%M:%S')}]\n{err}\n")
        except Exception:
            pass
        raise
