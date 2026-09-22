#!/bin/sh
# ZimTube launcher - tìm Python rồi chạy app
case "$0" in
    */*) cd "${0%/*}" || exit 1 ;;
esac
APP="$(pwd)"
export SDCARD_PATH="${SDCARD_PATH:-/mnt/SDCARD}"
export PATH="$SDCARD_PATH/System/bin:$PATH"
export LD_LIBRARY_PATH="$APP/libs:$SDCARD_PATH/System/lib:/usr/trimui/lib:/usr/lib64:/usr/lib:/lib:$LD_LIBRARY_PATH"
export PYSDL2_DLL_PATH="$APP/libs:/usr/trimui/lib:/usr/lib64:/usr/lib"

CACHE_DIR="$SDCARD_PATH/.zimtube"
CACHE_PY="$CACHE_DIR/python/bin/python3"
RUNTIME_URL="https://github.com/mxtmod-lab/ZimRetrohub/releases/download/runtime-python-3.11.14-aarch64/python-3.11.14-aarch64.tar.gz"
RUNTIME_SHA="bb998dbad759a6299288ad76646ee1ff3ce110b91d35718ed73160bd72a2a3b2"
RUNTIME_MB=27

if [ -n "$LOGS_PATH" ] && [ -d "$LOGS_PATH" ]; then
    ERRLOG="$LOGS_PATH/ZimTube.txt"
else
    ERRLOG="$SDCARD_PATH/ZimTube-loi.txt"
fi

log() { echo "[ZimTube] $*"; }

fatal() {
    log "$1"
    { echo "ZimTube khong khoi dong duoc"; echo "$(date 2>/dev/null)"; echo; echo "$1"; echo; echo "$2"; } > "$ERRLOG" 2>/dev/null
    exit 1
}

usable() {
    [ -n "$1" ] && [ -f "$1" ] || return 1
    [ -x "$1" ] || chmod +x "$1" 2>/dev/null
    "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null
}

find_python() {
    for c in \
        "$(command -v python3 2>/dev/null)" \
        "$APP/python/bin/python3" \
        "$CACHE_PY" \
        "$SDCARD_PATH/System/bin/python3" \
        "$SDCARD_PATH/Apps/PortMaster/PortMaster/exlibs/python3" \
        "$SDCARD_PATH/Apps/RetroHub/python/bin/python3" \
        "$SDCARD_PATH/Apps/ZimRetroHub/python/bin/python3" \
        /usr/bin/python3 /usr/local/bin/python3
    do
        if usable "$c"; then echo "$c"; return 0; fi
    done
    return 1
}

download_python() {
    log "Khong tim thay Python. Dang tai ve (~${RUNTIME_MB}MB)..."
    free_kb="$(df -k "$SDCARD_PATH" 2>/dev/null | awk 'NR==2 {print $4}')"
    case "$free_kb" in
        ''|*[!0-9]*) : ;;
        *) [ "$free_kb" -lt 204800 ] && return 1 ;;
    esac
    rm -rf "$CACHE_DIR/python" "$CACHE_DIR/py.tar.gz"
    mkdir -p "$CACHE_DIR" || return 1
    tgz="$CACHE_DIR/py.tar.gz"
    ok=1
    if command -v wget >/dev/null 2>&1; then
        wget -O "$tgz" "$RUNTIME_URL" && ok=0
        [ $ok -ne 0 ] && wget --no-check-certificate -O "$tgz" "$RUNTIME_URL" && ok=0
    fi
    if [ $ok -ne 0 ] && command -v curl >/dev/null 2>&1; then
        curl -fsSL -o "$tgz" "$RUNTIME_URL" && ok=0
        [ $ok -ne 0 ] && curl -fsSLk -o "$tgz" "$RUNTIME_URL" && ok=0
    fi
    [ $ok -ne 0 ] && { rm -f "$tgz"; return 1; }
    if command -v sha256sum >/dev/null 2>&1; then
        got="$(sha256sum "$tgz" 2>/dev/null | awk '{print $1}')"
        if [ "$got" != "$RUNTIME_SHA" ]; then
            log "Tai ve bi loi (sha256 khong khop)."; rm -f "$tgz"; return 1
        fi
    fi
    tar xzf "$tgz" -C "$CACHE_DIR" 2>/dev/null || { rm -rf "$tgz" "$CACHE_DIR/python"; return 1; }
    rm -f "$tgz"; chmod +x "$CACHE_PY" 2>/dev/null
    usable "$CACHE_PY" || { rm -rf "$CACHE_DIR/python"; return 1; }
}

PY=""
if [ -f "/tmp/.zt_python" ]; then
    CACHED_PY="$(cat /tmp/.zt_python 2>/dev/null)"
    usable "$CACHED_PY" && PY="$CACHED_PY"
fi
if [ -z "$PY" ]; then
    PY="$(find_python)"
    [ -n "$PY" ] && echo "$PY" > /tmp/.zt_python 2>/dev/null
fi
if [ -z "$PY" ]; then
    if download_python; then
        PY="$CACHE_PY"; echo "$PY" > /tmp/.zt_python 2>/dev/null
    else
        fatal "Khong co Python. Cai ZimRetroHub truoc de dung chung Python." \
              "Hoac noi Wi-Fi de ZimTube tu tai Python ve."
    fi
fi

rm -f "$ERRLOG" 2>/dev/null
touch /tmp/stay_alive 2>/dev/null

while true; do
    rm -f /tmp/launch_game.sh
    "$PY" app.py 2>>"$ERRLOG"
    APP_EXIT_CODE=$?
    if [ -f /tmp/launch_game.sh ]; then
        # app.py da huy renderer/window va SDL_Quit truoc khi toi day, nen
        # RetroArch la tien trinh duy nhat nam video/input cua may.
        sh /tmp/launch_game.sh
        PLAYER_EXIT_CODE=$?
        rm -f /tmp/launch_game.sh /tmp/stay_awake 2>/dev/null
        echo "[ZimTube] Player handoff exit code: $PLAYER_EXIT_CODE" >> "$ERRLOG"
        touch /tmp/stay_alive 2>/dev/null
    elif [ -f "$CACHE_DIR/update/pending.json" ]; then
        log "Dang cai dat ban cap nhat ZimTube..."
        "$PY" -m zt.apply_update "$APP" \
            "$CACHE_DIR/update/pending.json" \
            "$CACHE_DIR/update/result.txt" >>"$ERRLOG" 2>&1
        touch /tmp/stay_alive 2>/dev/null
        # Luon mo lai app: thanh cong hoac rollback deu hien ket qua cho nguoi dung.
        continue
    else
        break
    fi
done

rm -f /tmp/stay_alive 2>/dev/null
