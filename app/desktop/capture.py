import platform
import time
import pyperclip
from pynput.keyboard import Controller, Key

# Tune this if some apps are slow to update the clipboard after Cmd/Ctrl+C
DEFAULT_WAIT_SEC = 0.35

_kb = Controller()

def _press_copy_mac():
    with _kb.pressed(Key.cmd):
        _kb.press('c'); _kb.release('c')

def _press_copy_other():
    with _kb.pressed(Key.ctrl):
        _kb.press('c'); _kb.release('c')

# ---------- macOS full-fidelity snapshot/restore ----------

def _snapshot_pasteboard_mac():
    """
    Snapshot every pasteboard item and every type (text, RTF, HTML, images, file URLs, etc.)
    Returns a serializable structure of {type: bytes} per item.
    """
    try:
        from AppKit import NSPasteboard
        pb = NSPasteboard.generalPasteboard()
        items = pb.pasteboardItems() or []
        snap = []
        for item in items:
            entry = {}
            for t in item.types() or []:
                data = item.dataForType_(t)
                if data:
                    entry[str(t)] = bytes(data)
            snap.append(entry)
        return snap
    except Exception:
        return None  # fall back to text-only

def _restore_pasteboard_mac(snapshot):
    """
    Restore the pasteboard to an earlier snapshot with all types intact.
    """
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
        # If anything fails, we silently skip; better to leave clipboard changed than crash the capture.
        pass

# ---------- public API ----------

def capture_selected_text(wait_sec: float = DEFAULT_WAIT_SEC) -> str:
    """
    Presses Copy in the foreground app, reads the text, and restores the previous clipboard.
    On macOS, attempts full-fidelity restore (all data types). Else/if unavailable, restores text only.
    Returns the captured plain text ('' if none).
    """
    system = platform.system()

    if system == "Darwin":
        # Try full-fidelity snapshot; if it fails, we fall back to text-only
        snapshot = _snapshot_pasteboard_mac()
        prev_text = None if snapshot is not None else (pyperclip.paste() or "")

        _press_copy_mac()
        time.sleep(wait_sec)

        text = (pyperclip.paste() or "").strip()

        # Restore
        if snapshot is not None:
            _restore_pasteboard_mac(snapshot)
        else:
            pyperclip.copy(prev_text or "")

        return text

    else:
        # Cross-platform text-only path
        prev_text = pyperclip.paste() or ""
        _press_copy_other()
        time.sleep(wait_sec)
        text = (pyperclip.paste() or "").strip()
        pyperclip.copy(prev_text or "")
        return text
