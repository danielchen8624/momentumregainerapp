import sys, time
IDLE_UNKNOWN = 0

def idle_ms():
    if sys.platform.startswith("win"):
        try:
            import ctypes
            from ctypes import wintypes
            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
            if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
                millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
                return int(millis)
        except Exception:
            return IDLE_UNKNOWN
    elif sys.platform == "darwin":
        try:
            from Quartz import CGEventSourceSecondsSinceLastEventType, kCGEventSourceStateHIDSystemState, kCGAnyInputEventType
            sec = CGEventSourceSecondsSinceLastEventType(kCGEventSourceStateHIDSystemState, kCGAnyInputEventType)
            return int(sec * 1000)
        except Exception:
            return IDLE_UNKNOWN
    else:
        # linux fallback: best-effort (can be improved with X11/DBus)
        return IDLE_UNKNOWN
    return IDLE_UNKNOWN
