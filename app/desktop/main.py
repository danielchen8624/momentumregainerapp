from hotkeys import startListener
from capture import capture_selected_text
import requests

API_URL = "http://127.0.0.1:4545"

def execute():
    text = capture_selected_text()
    if not text:
        print("No selection detected.")
        return
    if len(text) > 20000:
        print("Selection too large; skipping (>20k chars).")
        return

    try:
        r = requests.post(f"{API_URL}/add", json={"text": text}, timeout=5)
        r.raise_for_status()
        print("Inserted:", r.json())
    except requests.RequestException as e:
        print("API error:", e)

def main():
    startListener(execute)

if __name__ == "__main__":
    main()
