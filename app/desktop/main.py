import threading, time, json, sys, signal, requests, webbrowser
from app.desktop.os_idle import idle_ms
from app.desktop.hotkeys import HotkeyManager
from app.desktop.tray_app import make_icon
from PIL import Image  # import ensures pystray has pillow
import uvicorn

API_URL = "http://127.0.0.1:4545"
IDLE_THRESHOLD_MS = 3 * 60 * 1000  # 3 minutes for demo

paused = False
def toggle_pause():
    global paused
    paused = not paused
toggle_pause.paused = False  # attach state

def run_api():
    uvicorn.run("app.backend.main:app", host="127.0.0.1", port=4545, log_level="warning")

def on_capture():
    # demo: send a fake capture; real ones come from extensions later
    payload = {
        "kind": "note",
        "title": "Manual capture",
        "app_id": "desktop",
        "group_id": "default",
        "locator": {"demo": True, "ts": int(time.time())}
    }
    try:
        requests.post(f"{API_URL}/capture/item", json=payload, timeout=1.0)
        print("Captured demo item")
    except Exception as e:
        print("capture failed:", e)

def on_restore():
    # for now, just open recent list in browser (placeholder)
    try:
        webbrowser.open(f"{API_URL}/docs")  # FastAPI docs as a temp UI
    except Exception as e:
        print("restore failed:", e)

def idle_watcher():
    last_notified = 0
    while True:
        time.sleep(1.0)
        if paused:
            continue
        ms = idle_ms()
        if ms != 0 and ms >= IDLE_THRESHOLD_MS and (time.time() - last_notified) > 30:
            print("Idle threshold reached → show resume UI")
            try:
                webbrowser.open(f"{API_URL}/docs")  # replace with your React UI later
            except Exception:
                pass
            last_notified = time.time()

def main():
    # start API
    api_t = threading.Thread(target=run_api, daemon=True)
    api_t.start()

    # start hotkeys
    hk = HotkeyManager(on_capture=on_capture, on_restore=on_restore)
    hk.start()

    # start idle watcher
    idle_t = threading.Thread(target=idle_watcher, daemon=True)
    idle_t.start()

    # tray
    def on_quit():
        print("Quitting…")
        sys.exit(0)
    def on_pause_toggle():
        toggle_pause()
        on_pause_toggle.paused = paused

    on_pause_toggle.paused = paused

    icon = make_icon(on_pause_toggle, on_quit)
    icon.run()  # blocks; quit from tray

if __name__ == "__main__":
    # allow Ctrl+C in terminal
    signal.signal(signal.SIGINT, lambda s,f: sys.exit(0))
    main()
