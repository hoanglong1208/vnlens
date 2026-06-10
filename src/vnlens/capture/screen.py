import mss
from PIL import Image

from ..config.schema import Region


class ScreenCapture:
    """Grabs a screen region with mss and returns it as a PIL image.

    An mss instance is not safe to share across threads, so each capture thread
    creates its own ScreenCapture.
    """

    def __init__(self) -> None:
        self._sct = mss.mss()

    def screen_size(self) -> tuple[int, int]:
        """Size of the primary monitor in pixels."""
        monitor = self._sct.monitors[1]
        return monitor["width"], monitor["height"]

    def grab(self, region: Region) -> Image.Image:
        width, height = self.screen_size()
        box = region.to_pixels(width, height)
        shot = self._sct.grab(box)
        return Image.frombytes("RGB", shot.size, shot.rgb)

    def close(self) -> None:
        self._sct.close()
