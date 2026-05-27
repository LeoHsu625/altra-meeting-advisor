from pynput import keyboard
from typing import Callable


def start_hotkey_listener(
    on_cue: Callable,
    on_stop: Callable,
) -> keyboard.GlobalHotKeys:
    hotkeys = keyboard.GlobalHotKeys({
        "<f9>": on_cue,
        "<f10>": on_stop,
    })
    hotkeys.start()
    return hotkeys
