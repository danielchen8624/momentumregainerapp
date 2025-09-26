# app/desktop/hotkeys.py
from pynput import keyboard
import threading
import os

def _hotkey_from_env(default="cmd+shift+v"):
    """
    Allow overriding with HOTKEY env var, e.g.:
      HOTKEY=ctrl+alt+g python run_all.py
    """
    raw = os.environ.get("HOTKEY")
    if raw:
        return raw.lower()
    return default

def startListener(execute_callback, debug=False):
    hotkey = _hotkey_from_env("cmd+shift+v")  # default = Cmd+Shift+V
    # Convert to pynput GlobalHotKeys format: "cmd+shift+v" -> "<cmd>+<shift>+v"
    parts = [p.strip().lower() for p in hotkey.split("+") if p.strip()]
    mods = []
    key = None
    for p in parts:
        if p in ("cmd", "ctrl", "alt", "shift"):
            mods.append(f"<{p}>")
        else:
            key = p
    if key is None:
        raise ValueError(f"Hotkey needs a key: {hotkey}")
    seq = "+".join(mods + [key])

    if debug:
        print(f"[hotkeys] binding {seq}")

    def on_activate():
        if debug:
            print(f"[hotkeys] trigger: {seq}")
        threading.Thread(target=execute_callback, daemon=True).start()

    h = keyboard.GlobalHotKeys({seq: on_activate})
    h.start()
    if debug:
        print(f"[hotkeys] listener started with {seq} (suppression ON)")
    h.join()  # keep the process alive
