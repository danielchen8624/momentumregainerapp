from pynput import keyboard
import time

A_KEYS = {keyboard.KeyCode(char='a'), keyboard.KeyCode(char='A')}
SHIFT = keyboard.Key.shift

def startListener(execute_callback):
    current = set()
    armed = False  # becomes True once Shift+A is fully pressed

    def _in_combo_set(key):
        return key == SHIFT or key in A_KEYS

    def _combo_fully_down():
        return SHIFT in current and any(k in current for k in A_KEYS)

    def _any_combo_key_down():
        return SHIFT in current or any(k in current for k in A_KEYS)

    def on_press(key):
        nonlocal armed
        if _in_combo_set(key):
            current.add(key)
            if _combo_fully_down():
                armed = True

    def on_release(key):
        nonlocal armed
        if _in_combo_set(key):
            current.discard(key)
            if armed and not _any_combo_key_down():
                armed = False
                time.sleep(0.05)  # let modifier fully release
                execute_callback()

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
