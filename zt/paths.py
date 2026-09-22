# -*- coding: utf-8 -*-
import os

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _detect_sdcard_path():
    env_sd = os.environ.get("SDCARD_PATH")
    if env_sd and os.path.isdir(env_sd):
        return os.path.abspath(env_sd)
    parent = os.path.dirname(APP_DIR)
    if os.path.basename(parent).lower() == "apps":
        card_candidate = os.path.dirname(parent)
        if os.path.isdir(card_candidate):
            return os.path.abspath(card_candidate)
    for candidate in ["/mnt/SDCARD", "/mnt/mmc", "/userdata", "/roms", "/mnt/sdcard"]:
        if os.path.isdir(candidate):
            return candidate
    return env_sd if env_sd else os.path.expanduser("~")

SDCARD_PATH = _detect_sdcard_path()

def _get_cache_dir():
    primary = os.path.join(SDCARD_PATH, ".zimtube")
    try:
        os.makedirs(os.path.join(primary, "thumbnails"), exist_ok=True)
        return primary
    except Exception:
        fallback = os.path.join(os.path.expanduser("~"), ".zimtube")
        try:
            os.makedirs(os.path.join(fallback, "thumbnails"), exist_ok=True)
            return fallback
        except Exception:
            tmp = "/tmp/.zimtube"
            os.makedirs(os.path.join(tmp, "thumbnails"), exist_ok=True)
            return tmp

CACHE_DIR = _get_cache_dir()
YT_CACHE_DIR           = os.path.join(CACHE_DIR, "thumbnails")
YT_HISTORY_FILE        = os.path.join(CACHE_DIR, "search_history.json")
YT_FEED_CACHE_FILE     = os.path.join(CACHE_DIR, "feed_cache.json")
YT_FEED_FALLBACK_FILE  = os.path.join(CACHE_DIR, "feed_fallback.json")
YT_FAVORITES_FILE      = os.path.join(CACHE_DIR, "favorites.json")
YT_FAVORITES_FALLBACK_FILE = os.path.join(CACHE_DIR, "favorites_fallback.json")
WATCHED_FILE           = os.path.join(CACHE_DIR, "watched.json")
YT_SESSION_FILE        = os.path.join(CACHE_DIR, "session.json")
YT_PROGRESS_FILE       = os.path.join(CACHE_DIR, "progress.json")
YT_WATCHED_FILE        = os.path.join(CACHE_DIR, "watched.json")
YT_SETTINGS_FILE       = os.path.join(CACHE_DIR, "settings.json")
YT_DOWNLOAD_INDEX_FILE = os.path.join(CACHE_DIR, "downloads.json")
YT_PLAYER_RESULT_FILE  = os.path.join(CACHE_DIR, "player_result.json")
YTDLP_PATH             = os.path.join(CACHE_DIR, "yt-dlp")

# Offline media must survive a reboot; never place user downloads under /tmp.
YT_DOWNLOAD_DIR = os.path.join(SDCARD_PATH, "Videos", "ZimTube")
try:
    os.makedirs(YT_DOWNLOAD_DIR, exist_ok=True)
except Exception:
    YT_DOWNLOAD_DIR = os.path.join(CACHE_DIR, "downloads")
    try:
        os.makedirs(YT_DOWNLOAD_DIR, exist_ok=True)
    except Exception:
        pass
