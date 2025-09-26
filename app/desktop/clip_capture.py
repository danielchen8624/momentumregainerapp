# app/desktop/clip_capture.py
import platform, time, subprocess, os, sys

_IS_MAC = platform.system() == "Darwin"

# Try to import macOS-specific clipboard APIs
if _IS_MAC:
    try:
        from AppKit import NSPasteboard, NSPasteboardTypeString, NSAttributedString
        from AppKit import NSPasteboardTypeHTML  # may be None on older macOS; we guard
        from Foundation import NSData
        from Cocoa import NSWorkspace
        _HAVE_PYOBJC = True
    except Exception:
        _HAVE_PYOBJC = False
else:
    _HAVE_PYOBJC = False

# Fallback cross-platform text clipboard
try:
    import pyperclip
    _HAVE_PYPERCLIP = True
except Exception:
    _HAVE_PYPERCLIP = False

# Pynput only used for the "pynput Cmd+C" fallback attempt
try:
    from pynput import keyboard
    _HAVE_PYNPUT = True
except Exception:
    _HAVE_PYNPUT = False


# ---------------------------
# Utility: logging helper
# ---------------------------
def _log(msg: str):
    print(msg, flush=True)


# ---------------------------
# macOS helpers (pyobjc path)
# ---------------------------
def _pb():
    return NSPasteboard.generalPasteboard()

def _pb_change_count():
    return _pb().changeCount()

def _pb_snapshot():
    """
    Take a 'snapshot' of current pasteboard items (all types), so we can restore later.
    We'll store types + data for each item.
    """
    board = _pb()
    items = board.pasteboardItems() or []
    snap = []
    for item in items:
        # Collect per-type data
        types = item.types() or []
        entry = []
        for t in types:
            data = item.dataForType_(t)
            if data is not None:
                entry.append((str(t), bytes(data)))
        snap.append(entry)
    return snap

def _pb_restore(snapshot):
    """
    Restore pasteboard from snapshot created by _pb_snapshot.
    """
    board = _pb()
    board.clearContents()
    # Rebuild items by writing per-type data via a temporary NSAttributedString or NSString where possible
    # Simpler approach: re-add only the richest item (this keeps images/rtf/html if present)
    # If multiple items existed, we add them all.
    for entry in snapshot:
        # We write each type back. PyObjC writing requires setData:forType:
        # We need an NSPasteboardWriting-conforming object; we can directly setData for each type on pasteboard
        # by creating a new item per entry.
        from AppKit import NSPasteboardItem
        pbi = NSPasteboardItem.alloc().init()
        for t, data in entry:
            nsdata = NSData.dataWithBytes_length_(data, len(data))
            pbi.setData_forType_(nsdata, t)
        board.writeObjects_([pbi])

def _frontmost_app_name():
    try:
        ws = NSWorkspace.sharedWorkspace()
        app = ws.frontmostApplication()
        return str(app.localizedName())
    except Exception:
        return "Unknown"

def _read_text_from_pasteboard_mac():
    board = _pb()
    # 1) Plain string
    s = board.stringForType_(NSPasteboardTypeString)
    if s:
        return str(s)

    # 2) HTML -> plain text (if supported)
    # Some PyObjC versions expose NSPasteboardTypeHTML; if missing, attempt using UTI
    html_types = []
    try:
        if NSPasteboardTypeHTML:
            html_types.append(NSPasteboardTypeHTML)
    except Exception:
        pass
    html_types.append("public.html")

    for t in html_types:
        try:
            data = board.dataForType_(t)
            if data:
                # Convert HTML to attributed string -> string
                attr, _ = NSAttributedString.alloc().initWithHTML_documentAttributes_(data, None)
                if attr:
                    return str(attr.string())
        except Exception:
            pass

    # 3) RTF -> plain text
    rtf_types = ["public.rtf", "NeXT Rich Text Format"]
    for t in rtf_types:
        try:
            data = board.dataForType_(t)
            if data:
                attr, _ = NSAttributedString.alloc().initWithRTF_documentAttributes_(data, None)
                if attr:
                    return str(attr.string())
        except Exception:
            pass

    return ""


def _menu_copy_via_applescript():
    """
    Use System Events to invoke Edit -> Copy on the frontmost app.
    This is more 'user-like' than synthetic keystrokes.
    """
    osa = r'''
    try
        tell application "System Events"
            set frontApp to first application process whose frontmost is true
            tell frontApp
                try
                    click menu item "Copy" of menu 1 of menu bar item "Edit" of menu bar 1
                    return "OK"
                on error
                    return "NO_EDIT_MENU"
                end try
            end tell
        end tell
    on error
        return "ERROR"
    end try
    '''
    out = subprocess.run(["osascript", "-e", osa], capture_output=True, text=True)
    return (out.returncode == 0) and ("OK" in (out.stdout or ""))


def _cmd_c_via_applescript():
    osa = r'''
    tell application "System Events"
        keystroke "c" using command down
    end tell
    '''
    out = subprocess.run(["osascript", "-e", osa], capture_output=True)
    return out.returncode == 0


def _cmd_c_via_pynput():
    if not _HAVE_PYNPUT:
        return False
    k = keyboard.Controller()
    try:
        with k.pressed(keyboard.Key.cmd):
            k.press('c')
            k.release('c')
        return True
    except Exception:
        return False


def _wait_for_change_count(before, timeout_s=1.0):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if _pb_change_count() != before:
            return True
        time.sleep(0.02)
    return False


# ---------------------------
# Cross-platform fallback
# ---------------------------
def _fallback_text_copy_attempt():
    """
    Weak, but better than nothing for non-mac:
    Try to read current clipboard text with pyperclip.
    """
    if not _HAVE_PYPERCLIP:
        return ("", False)
    try:
        before = pyperclip.paste()
        # Try to synthesize Ctrl+C (only if pynput is available)
        changed = False
        if _HAVE_PYNPUT:
            k = keyboard.Controller()
            try:
                with k.pressed(keyboard.Key.ctrl):
                    k.press('c'); k.release('c')
                time.sleep(0.1)
                after = pyperclip.paste()
                changed = (after != before)
                return (after if changed else "", changed)
            except Exception:
                pass
        # last resort: just return whatever is in the clipboard
        return (before or "", bool(before))
    except Exception:
        return ("", False)


# ---------------------------
# Public entry: capture
# ---------------------------
def capture_selected_text():
    """
    Returns: (text: str, changed: bool)
    - 'changed' True iff we detected the pasteboard actually changed during our attempts.
    """
    # Let the hotkey release & app UI settle (prevents selection loss in Chrome/Electron).
    time.sleep(0.12)

    if not _IS_MAC or not _HAVE_PYOBJC:
        # Non-mac or missing pyobjc – do a best-effort fallback
        _log("[cap] (fallback) using pyperclip / Ctrl+C path")
        return _fallback_text_copy_attempt()

    # macOS + pyobjc path (full-fidelity)
    app_name = _frontmost_app_name()
    _log(f"[cap] frontmost app: {app_name}")

    # Snapshot current pasteboard to restore later
    try:
        snapshot = _pb_snapshot()
    except Exception:
        snapshot = None

    before = _pb_change_count()
    changed = False

    # Attempt 1: Menu Edit->Copy (most 'human-like')
    _log("[cap] attempt: menu Edit->Copy")
    if _menu_copy_via_applescript():
        changed = _wait_for_change_count(before, timeout_s=1.0)
    _log(f"[cap] changed after menu click? {changed}")
    if not changed:
        # Attempt 2: AppleScript Cmd+C
        _log("[cap] attempt: AppleScript Cmd+C")
        if _cmd_c_via_applescript():
            changed = _wait_for_change_count(before, timeout_s=1.0)
        _log(f"[cap] changed after AppleScript? {changed}")

    if not changed:
        # Attempt 3: pynput Cmd+C
        _log("[cap] attempt: pynput Cmd+C")
        if _cmd_c_via_pynput():
            changed = _wait_for_change_count(before, timeout_s=1.0)
        _log(f"[cap] changed after pynput? {changed}")

    text = ""
    if changed:
        # Read text (plain → HTML→text → RTF→text)
        try:
            text = _read_text_from_pasteboard_mac() or ""
        except Exception:
            text = ""

    else:
        _log("[cap] no pasteboard change detected; not capturing.")

    # Restore original pasteboard (best effort)
    if snapshot is not None:
        try:
            _pb_restore(snapshot)
        except Exception:
            pass

    return (text, changed)
