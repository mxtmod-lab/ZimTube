# -*- coding: utf-8 -*-
"""
ZimTube SDL2 Engine — lightweight screen manager with texture cache,
toast notifications, and gamepad input.
"""
import ctypes, os, time, threading

import sdl2
import sdl2.sdlttf as ttf
import sdl2.sdlimage as img

from .state  import SCREEN_W, SCREEN_H, FPS_IDLE, FPS_ACTIVE
from .inputs import InputState
from .fonts  import load_fonts

# ── Colours ────────────────────────────────────────────────────────────────
BG_COLOR       = (15, 15, 15, 255)    # near-black background
ACCENT         = (255, 0, 0, 255)     # YouTube red
HEADER_BG      = (24, 24, 24, 255)
CARD_BG        = (28, 28, 28, 255)
CARD_SEL       = (40, 40, 40, 255)
CARD_BORDER    = (255, 0, 0, 255)
TEXT_PRIMARY   = (255, 255, 255, 255)
TEXT_SECONDARY = (170, 170, 170, 255)
TEXT_DIM       = (110, 110, 110, 255)
FOOTER_BG      = (20, 20, 20, 255)

_TOAST_DURATION = 3.0


class ZimTubeEngine:
    def __init__(self):
        self.window   = None
        self.renderer = None
        self.font_title = None
        self.font_body  = None
        self.font_small = None
        self._screens   = {}          # name -> screen instance
        self._stack     = []          # [screen_name, ...]
        self._inputs    = InputState()
        self._tex_cache = {}          # path -> (texture, w, h)
        self._tex_lock  = threading.Lock()
        self._toast_msg  = ""
        self._toast_until = 0.0
        self._running   = False
        self._dirty     = True        # force first render

    # ── Init ───────────────────────────────────────────────────────────────

    def init_sdl(self):
        sdl2.SDL_SetHint(b"SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", b"1")
        sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_JOYSTICK |
                      sdl2.SDL_INIT_GAMECONTROLLER)
        img.IMG_Init(img.IMG_INIT_JPG | img.IMG_INIT_PNG)

        dm = sdl2.SDL_DisplayMode()
        sdl2.SDL_GetCurrentDisplayMode(0, ctypes.byref(dm))
        dw, dh = dm.w or SCREEN_W, dm.h or SCREEN_H

        self.window = sdl2.SDL_CreateWindow(
            b"ZimTube",
            sdl2.SDL_WINDOWPOS_CENTERED, sdl2.SDL_WINDOWPOS_CENTERED,
            dw, dh,
            sdl2.SDL_WINDOW_SHOWN | sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP,
        )
        self.renderer = sdl2.SDL_CreateRenderer(
            self.window, -1,
            sdl2.SDL_RENDERER_ACCELERATED | sdl2.SDL_RENDERER_PRESENTVSYNC,
        )
        sdl2.SDL_ShowCursor(sdl2.SDL_DISABLE)

        # Open all controllers
        for i in range(sdl2.SDL_NumJoysticks()):
            if sdl2.SDL_IsGameController(i):
                sdl2.SDL_GameControllerOpen(i)

    def init_fonts(self):
        fonts = load_fonts()
        if not fonts:
            return False
        self.font_title, self.font_body, self.font_small = fonts
        return True

    # ── Screen management ──────────────────────────────────────────────────

    def register_screen(self, name, screen):
        self._screens[name] = screen

    def get_screen(self, name):
        """Return a registered screen instance for context actions."""
        return self._screens.get(name)

    def push_screen(self, name, params=None):
        screen = self._screens.get(name)
        if not screen:
            return
        self._stack.append(name)
        screen.on_enter(params)
        self._dirty = True

    def pop_screen(self):
        if len(self._stack) > 1:
            old = self._stack.pop()
            self._screens[old].on_exit()
            cur = self._screens[self._stack[-1]]
            cur.on_resume()
            self._dirty = True

    def current_screen(self):
        if self._stack:
            return self._screens[self._stack[-1]]
        return None

    # ── Toast ──────────────────────────────────────────────────────────────

    def toast(self, msg, duration=_TOAST_DURATION):
        self._toast_msg   = msg
        self._toast_until = time.monotonic() + duration
        self._dirty = True

    # ── Texture loading ────────────────────────────────────────────────────

    def load_texture(self, path):
        """Load image from disk as SDL texture; cached. Returns (tex,w,h) or None."""
        with self._tex_lock:
            cached = self._tex_cache.get(path)
        if cached:
            return cached
        if not os.path.exists(path):
            return None
        try:
            surf = img.IMG_Load(path.encode())
            if not surf:
                return None
            tex = sdl2.SDL_CreateTextureFromSurface(self.renderer, surf)
            w, h = surf.contents.w, surf.contents.h
            sdl2.SDL_FreeSurface(surf)
            if not tex:
                return None
            entry = (tex, w, h)
            with self._tex_lock:
                # Evict oldest if cache too large
                if len(self._tex_cache) > 80:
                    oldest_key = next(iter(self._tex_cache))
                    old_tex = self._tex_cache.pop(oldest_key)[0]
                    sdl2.SDL_DestroyTexture(old_tex)
                self._tex_cache[path] = entry
            return entry
        except Exception:
            return None

    def evict_texture(self, path):
        with self._tex_lock:
            entry = self._tex_cache.pop(path, None)
        if entry:
            sdl2.SDL_DestroyTexture(entry[0])

    # ── Draw primitives ────────────────────────────────────────────────────

    def fill_rect(self, x, y, w, h, r, g, b, a=255):
        sdl2.SDL_SetRenderDrawBlendMode(self.renderer, sdl2.SDL_BLENDMODE_BLEND)
        sdl2.SDL_SetRenderDrawColor(self.renderer, r, g, b, a)
        rect = sdl2.SDL_Rect(int(x), int(y), int(w), int(h))
        sdl2.SDL_RenderFillRect(self.renderer, rect)

    def draw_rect(self, x, y, w, h, r, g, b, a=255, thickness=2):
        for i in range(thickness):
            sdl2.SDL_SetRenderDrawColor(self.renderer, r, g, b, a)
            rect = sdl2.SDL_Rect(int(x)+i, int(y)+i, int(w)-2*i, int(h)-2*i)
            sdl2.SDL_RenderDrawRect(self.renderer, rect)

    def draw_texture(self, tex, x, y, w, h):
        dst = sdl2.SDL_Rect(int(x), int(y), int(w), int(h))
        sdl2.SDL_RenderCopy(self.renderer, tex, None, dst)

    def draw_texture_fit(self, tex_entry, x, y, w, h):
        """Draw texture scaled to fit within (w,h) preserving aspect ratio."""
        if not tex_entry:
            return
        tex, tw, th = tex_entry
        if tw == 0 or th == 0:
            return
        scale = min(w / tw, h / th)
        dw = int(tw * scale)
        dh = int(th * scale)
        dx = x + (w - dw) // 2
        dy = y + (h - dh) // 2
        dst = sdl2.SDL_Rect(dx, dy, dw, dh)
        sdl2.SDL_RenderCopy(self.renderer, tex, None, dst)

    def draw_text(self, text, font, x, y, r, g, b, a=255,
                  center_y=False, center_x=False, max_w=None):
        if not text or not font:
            return 0
        text = str(text)
        if max_w:
            # Truncate with ellipsis
            while len(text) > 3:
                surf = ttf.TTF_RenderUTF8_Blended(
                    font, text.encode("utf-8", errors="replace"),
                    sdl2.SDL_Color(r, g, b, a))
                if not surf:
                    break
                tw = surf.contents.w
                sdl2.SDL_FreeSurface(surf)
                if tw <= max_w:
                    break
                text = text[:-2] + "…"

        color = sdl2.SDL_Color(r, g, b, a)
        surf = ttf.TTF_RenderUTF8_Blended(font, text.encode("utf-8", errors="replace"), color)
        if not surf:
            return 0
        tex = sdl2.SDL_CreateTextureFromSurface(self.renderer, surf)
        tw, th = surf.contents.w, surf.contents.h
        sdl2.SDL_FreeSurface(surf)
        if not tex:
            return 0
        rx = x - tw // 2 if center_x else x
        ry = y - th // 2 if center_y else y
        dst = sdl2.SDL_Rect(rx, ry, tw, th)
        sdl2.SDL_RenderCopy(self.renderer, tex, None, dst)
        sdl2.SDL_DestroyTexture(tex)
        return tw

    def text_width(self, text, font):
        if not text or not font:
            return 0
        w_ref, h_ref = ctypes.c_int(0), ctypes.c_int(0)
        ttf.TTF_SizeUTF8(font, text.encode("utf-8", errors="replace"),
                         ctypes.byref(w_ref), ctypes.byref(h_ref))
        return w_ref.value

    # ── Main loop ──────────────────────────────────────────────────────────

    def run(self):
        self._running = True
        self.push_screen("home")

        ev = sdl2.SDL_Event()
        frame_t = 1.0 / FPS_ACTIVE
        last_render = 0.0

        while self._running:
            t = time.monotonic()
            inputs = {}

            while sdl2.SDL_PollEvent(ctypes.byref(ev)):
                if ev.type == sdl2.SDL_QUIT:
                    self._running = False
                    break
                fired = self._inputs.process_event(ev)
                inputs.update(fired)

            # Repeat
            inputs.update(self._inputs.tick())

            screen = self.current_screen()
            current_name = self._stack[-1] if self._stack else ""
            if inputs.get("btn_menu"):
                if current_name == "action_menu":
                    dirty = screen.handle_input({"btn_menu": True})
                    if dirty:
                        self._dirty = True
                    inputs.pop("btn_menu", None)
                elif current_name in ("home", "watch"):
                    self.push_screen("action_menu", {"source": current_name})
                    inputs.pop("btn_menu", None)
                    screen = self.current_screen()
            if screen and inputs:
                dirty = screen.handle_input(inputs)
                if dirty:
                    self._dirty = True

            # Render at target FPS when dirty, idle FPS otherwise
            fps = FPS_ACTIVE if self._dirty else FPS_IDLE
            if t - last_render >= 1.0 / fps:
                self._render()
                last_render = t
                self._dirty = False

            time.sleep(max(0, frame_t - (time.monotonic() - t)))

        sdl2.SDL_DestroyRenderer(self.renderer)
        sdl2.SDL_DestroyWindow(self.window)
        sdl2.SDL_Quit()

    def _render(self):
        sdl2.SDL_SetRenderDrawColor(self.renderer, *BG_COLOR)
        sdl2.SDL_RenderClear(self.renderer)

        screen = self.current_screen()
        if screen:
            screen.render(self)

        # Toast overlay
        if self._toast_msg and time.monotonic() < self._toast_until:
            self._draw_toast()
        elif self._toast_msg and time.monotonic() >= self._toast_until:
            self._toast_msg = ""

        sdl2.SDL_RenderPresent(self.renderer)

    def _draw_toast(self):
        msg = self._toast_msg
        pad_x, pad_y = 24, 12
        tw = self.text_width(msg, self.font_body)
        bw = tw + pad_x * 2
        bh = 44
        bx = (SCREEN_W - bw) // 2
        by = SCREEN_H - 90
        self.fill_rect(bx, by, bw, bh, 20, 20, 20, 220)
        self.draw_rect(bx, by, bw, bh, 255, 0, 0, 200, 2)
        self.draw_text(msg, self.font_body, bx + pad_x, by + pad_y, 255, 255, 255)

    def mark_dirty(self):
        self._dirty = True

    def quit(self):
        self._running = False
