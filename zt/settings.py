# -*- coding: utf-8 -*-
"""Persistent user settings for ZimTube."""
import json
import os
import threading

from .paths import YT_SETTINGS_FILE

_LOCK = threading.Lock()
DEFAULTS = {
    "quality": "360p",
    "autoplay": True,
    "audio_only": False,
    "show_player_help": True,
    "save_history": True,
    "download_kind": "video",
    "cache_limit_mb": 250,
}
VALID_QUALITIES = ("auto", "240p", "360p", "480p", "720p")


def load():
    data = {}
    try:
        with open(YT_SETTINGS_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
            if isinstance(raw, dict):
                data = raw
    except Exception:
        pass
    result = dict(DEFAULTS)
    result.update(data)
    if result.get("quality") not in VALID_QUALITIES:
        result["quality"] = DEFAULTS["quality"]
    try:
        result["cache_limit_mb"] = max(50, min(2000, int(result["cache_limit_mb"])))
    except (TypeError, ValueError):
        result["cache_limit_mb"] = DEFAULTS["cache_limit_mb"]
    return result


def save(data):
    merged = dict(DEFAULTS)
    if isinstance(data, dict):
        merged.update(data)
    os.makedirs(os.path.dirname(YT_SETTINGS_FILE), exist_ok=True)
    tmp = YT_SETTINGS_FILE + ".tmp"
    with _LOCK:
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(merged, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, YT_SETTINGS_FILE)
            return True
        except Exception:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
            return False


def update(**changes):
    data = load()
    data.update(changes)
    return save(data)
