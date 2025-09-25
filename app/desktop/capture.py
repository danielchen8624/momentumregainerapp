import time
import platform
import pyperclip
from pynput.keyboard import Controller, Key

_kb = Controller()

def _press_copy():
    if platform.system() == "Darwin":
        with _kb.pressed(Key.cmd):
            _kb.press('c'); _kb.release('c')
    else:
        with _kb.pressed(Key.ctrl):
            _kb.press('c'); _kb.release('c')

def capture_selected_text(wait_sec: float = 0.25, restore_clipboard: bool = True) -> str:
    """Simulate Copy in the active app, then read clipboard text."""
    prev = pyperclip.paste()
    _press_copy()
    time.sleep(wait_sec)                  # give the app time to update the clipboard
    text = (pyperclip.paste() or "").strip()
    if restore_clipboard:
        pyperclip.copy(prev or "")
    return text
