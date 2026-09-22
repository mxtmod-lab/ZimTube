# -*- coding: utf-8 -*-
"""Secure GitHub Release update client using only the Python standard library."""
import hashlib
import json
import os
import re
import tempfile
import urllib.error
import urllib.request

from zt.paths import CACHE_DIR
from zt.version import (APP_VERSION, CHECKSUM_ASSET, LATEST_RELEASE_API,
                        UPDATE_ASSET, is_newer)

UPDATE_DIR = os.path.join(CACHE_DIR, "update")
PENDING_FILE = os.path.join(UPDATE_DIR, "pending.json")
RESULT_FILE = os.path.join(UPDATE_DIR, "result.txt")
USER_AGENT = f"ZimTube/{APP_VERSION} TrimUI"


class UpdateError(Exception):
    pass


def _request_json(url, timeout=15):
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json", "User-Agent": USER_AGENT,
    })
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise UpdateError("Chưa có bản phát hành trên GitHub")
        raise UpdateError(f"GitHub trả về lỗi HTTP {exc.code}")
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        raise UpdateError("Không thể kết nối GitHub. Hãy kiểm tra Wi-Fi")


def check_latest():
    data = _request_json(LATEST_RELEASE_API)
    tag = str(data.get("tag_name") or "").lstrip("vV")
    if not tag:
        raise UpdateError("Bản phát hành không có số phiên bản")
    assets = {item.get("name"): item for item in data.get("assets", [])}
    package = assets.get(UPDATE_ASSET)
    checksum = assets.get(CHECKSUM_ASSET)
    if not package or not checksum:
        raise UpdateError("Bản mới thiếu gói ZIP hoặc checksum")
    return {
        "current": APP_VERSION, "latest": tag, "newer": is_newer(tag),
        "notes": str(data.get("body") or "").strip(),
        "size": int(package.get("size") or 0),
        "package_url": package.get("browser_download_url"),
        "checksum_url": checksum.get("browser_download_url"),
    }


def _download(url, destination, progress=None, timeout=30):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response, open(destination, "wb") as out:
            total = int(response.headers.get("Content-Length") or 0)
            current = 0
            while True:
                chunk = response.read(128 * 1024)
                if not chunk:
                    break
                out.write(chunk); current += len(chunk)
                if progress:
                    progress(current, total)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        try: os.remove(destination)
        except OSError: pass
        raise UpdateError(f"Tải bản cập nhật thất bại: {exc}")


def download_release(info, progress=None):
    os.makedirs(UPDATE_DIR, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="zimtube-", suffix=".zip", dir=UPDATE_DIR)
    os.close(fd)
    try:
        _download(info["package_url"], temporary, progress)
        checksum_path = temporary + ".sha256"
        _download(info["checksum_url"], checksum_path)
        with open(checksum_path, "r", encoding="utf-8") as src:
            expected = src.read().strip().split()[0].lower()
        if not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise UpdateError("File checksum không hợp lệ")
        digest = hashlib.sha256()
        with open(temporary, "rb") as src:
            for chunk in iter(lambda: src.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != expected:
            raise UpdateError("Checksum không khớp; đã hủy cập nhật")
        package_path = os.path.join(UPDATE_DIR, UPDATE_ASSET)
        os.replace(temporary, package_path)
        marker = {"version": info["latest"], "package": package_path,
                  "sha256": expected}
        marker_tmp = PENDING_FILE + ".tmp"
        with open(marker_tmp, "w", encoding="utf-8") as out:
            json.dump(marker, out)
        os.replace(marker_tmp, PENDING_FILE)
        return package_path
    finally:
        for path in (temporary, temporary + ".sha256"):
            try: os.remove(path)
            except OSError: pass


def consume_result():
    try:
        with open(RESULT_FILE, "r", encoding="utf-8") as src:
            message = src.read().strip()
        os.remove(RESULT_FILE)
        return message
    except OSError:
        return ""
