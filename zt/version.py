# -*- coding: utf-8 -*-
"""ZimTube release metadata."""
import re

APP_VERSION = "1.0.1"
GITHUB_REPO = "mxtmod-lab/ZimTube"
LATEST_RELEASE_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
UPDATE_ASSET = "ZimTube-update.zip"
CHECKSUM_ASSET = UPDATE_ASSET + ".sha256"


def version_tuple(value):
    """Convert a semver-like value to a comparable numeric tuple."""
    text = str(value or "").strip().lstrip("vV")
    match = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?", text)
    if not match:
        return (0, 0, 0)
    return tuple(int(part or 0) for part in match.groups())


def is_newer(candidate, current=APP_VERSION):
    return version_tuple(candidate) > version_tuple(current)
