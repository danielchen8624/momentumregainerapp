import time
import requests
import pyperclip
from hotkeys import startListener
from requests.exceptions import RequestException



API_URL = "http://127.0.0.1:4545"

def execute(): 
    try:
        r = requests.post(f"{API_URL}/add", json = {"text": "hailo"}, timeout=5) #send a post request to the backend with the highlighted text
        r.raise_for_status() # Raise an error for bad responses (4xx and 5xx)
        print("Hotkey action executed successfully:", r.json())
    except RequestException as e:
        print("Error executing hotkey action:", e)

def main():
    startListener(execute)


if __name__ == "__main__":
    main()
