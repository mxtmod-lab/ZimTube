# -*- coding: utf-8 -*-
"""Apply a verified ZimTube package after the SDL application exits."""
import hashlib
import json
import os
import py_compile
import shutil
import sys
import zipfile

REQUIRED = ("app.py", "launch.sh", "config.json", "zt")
MANAGED = ("app.py", "launch.sh", "config.json", "icon.png", "assets", "bin", "libs", "vendor", "zt")


class InstallError(Exception):
    pass


def _safe_members(archive):
    members = archive.infolist()
    for member in members:
        normalized = member.filename.replace("\\", "/")
        parts = normalized.split("/")
        if normalized.startswith("/") or ".." in parts:
            raise InstallError("Gói cập nhật chứa đường dẫn không an toàn")
        if member.is_dir():
            continue
        mode = member.external_attr >> 16
        if mode and (mode & 0o170000) == 0o120000:
            raise InstallError("Gói cập nhật không được chứa symbolic link")
    return members


def _payload_root(staging):
    entries = [name for name in os.listdir(staging) if name != "__MACOSX"]
    if len(entries) == 1 and os.path.isdir(os.path.join(staging, entries[0])):
        candidate = os.path.join(staging, entries[0])
        if os.path.isfile(os.path.join(candidate, "app.py")):
            return candidate
    return staging


def _validate_payload(root):
    for name in REQUIRED:
        if not os.path.exists(os.path.join(root, name)):
            raise InstallError(f"Gói cập nhật thiếu {name}")
    for base, _, files in os.walk(os.path.join(root, "zt")):
        for name in files:
            if name.endswith(".py"):
                py_compile.compile(os.path.join(base, name), doraise=True)
    py_compile.compile(os.path.join(root, "app.py"), doraise=True)


def apply_pending(app_dir, pending_file, result_file):
    work = os.path.dirname(pending_file)
    staging = os.path.join(work, "staging")
    backup = os.path.join(work, "backup")
    package = ""
    success = False
    message = "Cập nhật thất bại"
    try:
        with open(pending_file, "r", encoding="utf-8") as src:
            pending = json.load(src)
        package = pending["package"]
        digest = hashlib.sha256()
        with open(package, "rb") as src:
            for chunk in iter(lambda: src.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != pending.get("sha256"):
            raise InstallError("Checksum thay đổi trước khi cài")
        shutil.rmtree(staging, ignore_errors=True)
        shutil.rmtree(backup, ignore_errors=True)
        os.makedirs(staging); os.makedirs(backup)
        with zipfile.ZipFile(package) as archive:
            archive.extractall(staging, _safe_members(archive))
        payload = _payload_root(staging)
        _validate_payload(payload)
        for name in MANAGED:
            old = os.path.join(app_dir, name)
            if os.path.exists(old):
                target = os.path.join(backup, name)
                if os.path.isdir(old): shutil.copytree(old, target)
                else: shutil.copy2(old, target)
        try:
            for name in MANAGED:
                new = os.path.join(payload, name)
                if not os.path.exists(new):
                    continue
                target = os.path.join(app_dir, name)
                if os.path.isdir(target): shutil.rmtree(target)
                elif os.path.exists(target): os.remove(target)
                if os.path.isdir(new): shutil.copytree(new, target)
                else: shutil.copy2(new, target)
            os.chmod(os.path.join(app_dir, "launch.sh"), 0o755)
            _validate_payload(app_dir)
        except Exception:
            for name in MANAGED:
                target = os.path.join(app_dir, name)
                saved = os.path.join(backup, name)
                if os.path.isdir(target): shutil.rmtree(target)
                elif os.path.exists(target): os.remove(target)
                if os.path.isdir(saved): shutil.copytree(saved, target)
                elif os.path.exists(saved): shutil.copy2(saved, target)
            raise
        success = True
        message = f"Đã cập nhật ZimTube lên v{pending.get('version', '')}"
    except Exception as exc:
        message = f"Cập nhật thất bại: {exc}"
    finally:
        os.makedirs(os.path.dirname(result_file), exist_ok=True)
        with open(result_file, "w", encoding="utf-8") as out:
            out.write(message)
        try: os.remove(pending_file)
        except OSError: pass
        shutil.rmtree(staging, ignore_errors=True)
        shutil.rmtree(backup, ignore_errors=True)
        if success and package:
            try: os.remove(package)
            except OSError: pass
    return success, message


def main(argv=None):
    args = argv or sys.argv[1:]
    if len(args) != 3:
        return 2
    ok, _ = apply_pending(args[0], args[1], args[2])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
