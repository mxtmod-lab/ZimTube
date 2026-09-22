# -*- coding: utf-8 -*-
"""Gamepad / keyboard input normalizer."""
import sdl2

# Button repeat config
REPEAT_DELAY  = 0.35   # seconds before first repeat
REPEAT_RATE   = 0.12   # seconds between repeats

_AXIS_DEAD = 8000

_BTN_MAP = {
    # TrimUI physical labels are opposite SDL's generic ABXY naming.
    sdl2.SDL_CONTROLLER_BUTTON_A:             "btn_b",
    sdl2.SDL_CONTROLLER_BUTTON_B:             "btn_a",
    sdl2.SDL_CONTROLLER_BUTTON_X:             "btn_y",
    sdl2.SDL_CONTROLLER_BUTTON_Y:             "btn_x",
    sdl2.SDL_CONTROLLER_BUTTON_START:         "btn_start",
    sdl2.SDL_CONTROLLER_BUTTON_BACK:          "btn_menu",
    sdl2.SDL_CONTROLLER_BUTTON_GUIDE:         "btn_menu",
    sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER:  "btn_l",
    sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER: "btn_r",
    sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP:       "btn_up",
    sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN:     "btn_down",
    sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT:     "btn_left",
    sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT:    "btn_right",
}

_KEY_MAP = {
    sdl2.SDLK_UP:     "btn_up",
    sdl2.SDLK_DOWN:   "btn_down",
    sdl2.SDLK_LEFT:   "btn_left",
    sdl2.SDLK_RIGHT:  "btn_right",
    sdl2.SDLK_RETURN: "btn_a",
    sdl2.SDLK_ESCAPE: "btn_b",
    sdl2.SDLK_z:      "btn_a",
    sdl2.SDLK_x:      "btn_b",
    sdl2.SDLK_F1:     "btn_menu",
    sdl2.SDLK_m:      "btn_menu",
}


class InputState:
    def __init__(self):
        self._held   = {}  # name -> time_held_since
        self._fired  = set()
        self._import_time()

    def _import_time(self):
        import time as _t
        self._time = _t.monotonic

    def process_event(self, ev):
        """Process one SDL event; returns dict of triggered inputs or empty."""
        t = self._time()
        result = {}

        if ev.type == sdl2.SDL_CONTROLLERBUTTONDOWN:
            name = _BTN_MAP.get(ev.cbutton.button)
            if name:
                self._held[name] = t
                result[name] = True

        elif ev.type == sdl2.SDL_CONTROLLERBUTTONUP:
            name = _BTN_MAP.get(ev.cbutton.button)
            if name:
                self._held.pop(name, None)
                self._fired.discard(name)

        elif ev.type == sdl2.SDL_KEYDOWN:
            name = _KEY_MAP.get(ev.key.keysym.sym)
            if name and not ev.key.repeat:
                self._held[name] = t
                result[name] = True

        elif ev.type == sdl2.SDL_KEYUP:
            name = _KEY_MAP.get(ev.key.keysym.sym)
            if name:
                self._held.pop(name, None)
                self._fired.discard(name)

        return result

    def tick(self):
        """Call once per frame; returns dict of repeat-fired inputs."""
        t = self._time()
        result = {}
        for name, since in list(self._held.items()):
            held_for = t - since
            if name not in self._fired and held_for > REPEAT_DELAY:
                self._fired.add(name)
                result[name] = True
            elif name in self._fired:
                # Use a simple slot approach
                slots = int((held_for - REPEAT_DELAY) / REPEAT_RATE)
                last_slots = getattr(self, f"_slots_{name}", 0)
                if slots > last_slots:
                    setattr(self, f"_slots_{name}", slots)
                    result[name] = True
        return result

    def clear(self):
        self._held.clear()
        self._fired.clear()
