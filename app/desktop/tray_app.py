from pystray import Icon, Menu, MenuItem
from PIL import Image

def make_icon(on_pause_toggle, on_quit):
    img = Image.new("RGBA", (16, 16), (40, 140, 255, 255))
    icon = Icon("Momentum", img, "Momentum", menu=Menu(
        MenuItem(lambda _: "Pause capture" if not on_pause_toggle.paused else "Resume capture",
                 lambda _: on_pause_toggle()),
        MenuItem("Quit", lambda _: on_quit())
    ))
    return icon
