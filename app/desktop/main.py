# app/desktop/main.py
import traceback
import requests
from hotkeys import startListener
from clip_capture import capture_selected_text

API_URL = "http://127.0.0.1:4545"

def execute():
    print("[hotkey] trigger received")
    try:
        text, changed = capture_selected_text()
        print(f"[hotkey] capture returned changed={changed}, len={len(text or '')}")
        if not changed or not text:
            print("[hotkey] No selection (clipboard didn’t change). Skipping send.")
            return
        r = requests.post(f"{API_URL}/add", json={"text": text}, timeout=5)
        print(f"[hotkey] POST /add status={r.status_code}")
    except Exception:
        print("[hotkey] ERROR:\n" + traceback.format_exc())

if __name__ == "__main__":
    print("[desktop] starting hotkey listener (Cmd+Shift+V by default)")
    print("[desktop] tip: override with HOTKEY=ctrl+alt+g python run_all.py")
    startListener(execute_callback=execute, debug=True)
    # startListener blocks via .join(); no extra loop needed
