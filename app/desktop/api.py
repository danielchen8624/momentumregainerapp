import requests
from requests.exceptions import RequestException

API_URL = "http://127.0.0.1:4545"

def add_message(text: str, timeout_sec: float = 5.0) -> dict:
    try:
        r = requests.post(f"{API_URL}/add", json={"text": text}, timeout=timeout_sec)
        r.raise_for_status()
        return r.json()
    except RequestException as e:
        print("API error:", e)
        return {"ok": False, "error": str(e)}
