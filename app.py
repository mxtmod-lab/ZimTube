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


def main():
    engine = ZimTubeEngine()
    engine.init_sdl()
    if not engine.init_fonts():
        sys.exit(1)

    engine.register_screen("home",     HomeScreen(engine))
    engine.register_screen("search",   SearchScreen(engine))
    engine.register_screen("watch",    WatchScreen(engine))
    engine.register_screen("keyboard", KeyboardScreen(engine))

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
