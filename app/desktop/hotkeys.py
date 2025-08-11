from pynput import keyboard

class HotkeyManager:
    def __init__(self, on_capture, on_restore):
        self.on_capture = on_capture
        self.on_restore = on_restore
        self._listener = None
        self._pressed = set()

    def _on_press(self, key):
        self._pressed.add(key)
        if self._combo({"<ctrl>", "<alt>", "c"}):
            self.on_capture()
        if self._combo({"<ctrl>", "<alt>", "r"}):
            self.on_restore()

    def _on_release(self, key):
        self._pressed.discard(key)

    def _combo(self, keys):
        names = set()
        for k in self._pressed:
            if isinstance(k, keyboard.Key):
                names.add(f"<{k.name}>")
            else:
                try:
                    names.add(k.char.lower())
                except Exception:
                    pass
        return keys.issubset(names)

    def start(self):
        self._listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()
