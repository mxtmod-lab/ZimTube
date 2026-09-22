# -*- coding: utf-8 -*-
"""Safe TrimUI backlight control for audio-only playback.

The player runs as a standalone process, so the saved state is returned to its
caller and restored from ``finally`` when RetroArch exits. Only the backlight
is disabled; the device itself is not suspended and audio keeps playing.
"""
import glob
import os


def _read(path):
    try:
        with open(path, "r", encoding="ascii") as handle:
            return handle.read().strip()
    except (OSError, ValueError):
        return None


def _write(path, value):
    try:
        with open(path, "w", encoding="ascii") as handle:
            handle.write(str(value) + "\n")
        return True
    except (OSError, ValueError):
        return False


def _backlight_dirs():
    """Return kernel backlight devices, preferring TrimUI's usual name."""
    paths = glob.glob("/sys/class/backlight/*")
    return sorted(paths, key=lambda path: (os.path.basename(path) != "backlight", path))


def screen_off():
    """Turn off only the LCD backlight and return a restoration token.

    Brightness is the primary control because it works on stock and CrossMix
    kernels. ``bl_power`` is also used when available, but is never required.
    ``None`` means this firmware exposes no writable backlight control.
    """
    for directory in _backlight_dirs():
        brightness_path = os.path.join(directory, "brightness")
        old_brightness = _read(brightness_path)
        if old_brightness is None:
            continue

        power_path = os.path.join(directory, "bl_power")
        old_power = _read(power_path) if os.path.exists(power_path) else None
        token = {
            "brightness_path": brightness_path,
            "brightness": old_brightness,
            "power_path": power_path if old_power is not None else "",
            "power": old_power,
        }

        # Some TrimUI kernels ignore bl_power but expose writable brightness.
        brightness_off = _write(brightness_path, 0)
        power_off = _write(power_path, 4) if old_power is not None else False
        if brightness_off or power_off:
            return token

    return None


def screen_on(token):
    """Restore the exact backlight state captured by :func:`screen_off`."""
    if not isinstance(token, dict):
        return False

    restored = False
    power_path = token.get("power_path")
    old_power = token.get("power")
    if power_path and old_power is not None:
        restored = _write(power_path, old_power) or restored

    brightness_path = token.get("brightness_path")
    old_brightness = token.get("brightness")
    if brightness_path and old_brightness is not None:
        restored = _write(brightness_path, old_brightness) or restored
    return restored
