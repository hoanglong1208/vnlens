from collections.abc import Callable

from pynput import keyboard


def _to_pynput(key: str) -> str:
    """Turn a config key like "f2" or "ctrl+f3" into pynput's hotkey syntax."""
    parts = [p.strip().lower() for p in key.split("+")]
    return "+".join(f"<{p}>" if len(p) > 1 else p for p in parts)


class HotkeyListener:
    """Listens for global hotkeys, including while a game window has focus.

    Callbacks run on the listener thread, so they should be quick and thread-safe
    (e.g. emit a Qt signal rather than touch widgets directly)."""

    def __init__(self, bindings: dict[str, Callable[[], None]]) -> None:
        self._hotkeys = {_to_pynput(key): cb for key, cb in bindings.items()}
        self._listener: keyboard.GlobalHotKeys | None = None

    def start(self) -> None:
        self._listener = keyboard.GlobalHotKeys(self._hotkeys)
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
