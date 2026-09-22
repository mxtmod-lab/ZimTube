# -*- coding: utf-8 -*-
import os

APP_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SDCARD_PATH = os.environ.get("SDCARD_PATH", "/mnt/SDCARD")
CACHE_DIR  = os.path.join(SDCARD_PATH, ".zimtube")

YT_CACHE_DIR           = os.path.join(CACHE_DIR, "thumbnails")
YT_HISTORY_FILE        = os.path.join(CACHE_DIR, "search_history.json")
YT_FEED_CACHE_FILE     = os.path.join(CACHE_DIR, "feed_cache.json")
YT_FEED_FALLBACK_FILE  = os.path.join(CACHE_DIR, "feed_fallback.json")
YT_FAVORITES_FILE      = os.path.join(CACHE_DIR, "favorites.json")
YT_FAVORITES_FALLBACK_FILE = os.path.join(CACHE_DIR, "favorites_fallback.json")
WATCHED_FILE           = os.path.join(CACHE_DIR, "watched.json")
YTDLP_PATH             = os.path.join(CACHE_DIR, "yt-dlp")

for _d in (CACHE_DIR, YT_CACHE_DIR):
    os.makedirs(_d, exist_ok=True)
