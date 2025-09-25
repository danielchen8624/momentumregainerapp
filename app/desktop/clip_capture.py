import platform, time, subprocess, pyperclip
from pynput.keyboard import Controller, Key

DEFAULT_WAIT_SEC = 0.45
MAX_WAIT_MS      = 2000
POLL_EVERY_MS    = 25
_kb = Controller()

# ---------- keystroke & menu helpers ----------
def _press_copy_mac_via_pynput():
    with _kb.pressed(Key.cmd):
        _kb.press('c'); _kb.release('c')

def _press_copy_mac_via_applescript():
    subprocess.run(
        ['osascript', '-e',
         'tell application "System Events" to keystroke "c" using command down'],
        check=False
    )

def _click_copy_menu_mac() -> bool:
    """
    Tries to click Edit -> Copy in the frontmost app using UI scripting.
    Returns True if the AppleScript ran without error (not a guarantee the app has that menu).
    """
    script = r'''
    tell application "System Events"
      set frontApp to first application process whose frontmost is true
      try
        click menu item "Copy" of menu 1 of menu bar item "Edit" of menu bar 1 of frontApp
        return "ok"
      on error errMsg
        return "err:" & errMsg
      end try
    end tell
    '''
    try:
        out = subprocess.check_output(['osascript', '-e', script], text=True).strip()
        return out == "ok"
    except Exception:
        return False

def _press_copy_other():
    with _kb.pressed(Key.ctrl):
        _kb.press('c'); _kb.release('c')

# ---------- mac pasteboard helpers ----------
def _front_app_name_mac() -> str:
    try:
        out = subprocess.check_output(
            ['osascript', '-e',
             'tell application "System Events" to get name of (first application process whose frontmost is true)'],
            text=True
        ).strip()
        return out
    except Exception:
        return "unknown"

def _pb_change_count():
    from AppKit import NSPasteboard
    pb = NSPasteboard.generalPasteboard()
    return pb.changeCount(), pb

def _wait_for_change(prev_count, timeout_ms=MAX_WAIT_MS):
    from AppKit import NSPasteboard
    start = time.time()
    while (time.time() - start) * 1000 < timeout_ms:
        if NSPasteboard.generalPasteboard().changeCount() > prev_count:
            return True
        time.sleep(POLL_EVERY_MS / 1000.0)
    return False

def _snapshot_pasteboard_mac():
    try:
        from AppKit import NSPasteboard
        items = NSPasteboard.generalPasteboard().pasteboardItems() or []
        snap = []
        for it in items:
            entry = {}
            for t in it.types() or []:
                data = it.dataForType_(t)
                if data:
                    entry[str(t)] = bytes(data)
            snap.append(entry)
        return snap
    except Exception:
        return None

def _restore_pasteboard_mac(snapshot):
    try:
        if not snapshot:
            return
        from AppKit import NSPasteboard, NSPasteboardItem
        from Foundation import NSData
        pb = NSPasteboard.generalPasteboard()
        pb.clearContents()
        new_items = []
        for entry in snapshot:
            it = NSPasteboardItem.alloc().init()
            for t, raw in entry.items():
                nsdata = NSData.dataWithBytes_length_(raw, len(raw))
                it.setData_forType_(nsdata, t)
            new_items.append(it)
        if new_items:
            pb.writeObjects_(new_items)
    except Exception:
        pass

# ---------- public API ----------
def capture_selected_text(wait_sec: float = DEFAULT_WAIT_SEC) -> tuple[str, bool]:
    """
    Returns (text, changed). 'changed' is True only if the pasteboard changed after our Copy attempts.
    On macOS we snapshot/restore the clipboard (full fidelity).
    """
    system = platform.system()

    if system == "Darwin":
        appname = _front_app_name_mac()
        print(f"[cap] frontmost app: {appname}")

        snapshot = _snapshot_pasteboard_mac()
        text, changed = "", False

        # Attempt A: menu click
        prev, _ = _pb_change_count()
        print("[cap] attempt: menu Edit->Copy")
        if _click_copy_menu_mac():
            changed = _wait_for_change(prev, timeout_ms=MAX_WAIT_MS)
            print(f"[cap] changed after menu click? {changed}")

        # Attempt B: AppleScript keystroke (if still no change)
        if not changed:
            prev, _ = _pb_change_count()
            print("[cap] attempt: AppleScript Cmd+C")
            _press_copy_mac_via_applescript()
            changed = _wait_for_change(prev, timeout_ms=MAX_WAIT_MS)
            print(f"[cap] changed after AppleScript? {changed}")

        # Attempt C: pynput keystroke (final fallback)
        if not changed:
            prev, _ = _pb_change_count()
            print("[cap] attempt: pynput Cmd+C")
            _press_copy_mac_via_pynput()
            changed = _wait_for_change(prev, timeout_ms=MAX_WAIT_MS)
            print(f"[cap] changed after pynput? {changed}")

        if changed:
            time.sleep(min(wait_sec, 0.3))
            text = (pyperclip.paste() or "").strip()
            print(f"[cap] captured len={len(text)} preview={text[:60]!r}")
        else:
            print("[cap] no pasteboard change detected; not capturing.")

        _restore_pasteboard_mac(snapshot)
        return text, changed

    # Non-mac: text-only
    prev_text = pyperclip.paste() or ""
    _press_copy_other()
    time.sleep(wait_sec)
    text = (pyperclip.paste() or "").strip()
    changed = bool(text) and (text != prev_text)
    pyperclip.copy(prev_text or "")
    print(f"[cap] (non-mac) changed={changed} preview={text[:60]!r}")
    return text, changed
