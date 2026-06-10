import contextlib
import sys

from PyQt6.QtCore import QPropertyAnimation, QRect, Qt
from PyQt6.QtGui import QFontMetrics, QPainter, QPaintEvent
from PyQt6.QtWidgets import QWidget

from ..config.schema import OverlayConfig
from . import renderer

_GAP = 8
_MAX_LINES = 3
_FADE_IN_MS = 150
_FADE_OUT_MS = 100


class OverlayWindow(QWidget):
    """Frameless, always-on-top, click-through window that shows the translation
    anchored below the capture region."""

    def __init__(self, config: OverlayConfig) -> None:
        super().__init__()
        self._style = renderer.TextStyle.from_config(config)
        self._text = ""
        self._anchor: dict[str, int] | None = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self._fade = QPropertyAnimation(self, b"windowOpacity")

    def set_anchor(self, region_px: dict[str, int]) -> None:
        """Set the capture region (in screen pixels) the overlay sits below."""
        self._anchor = region_px

    def show_text(self, text: str) -> None:
        self._text = text
        self._relayout()
        self.show()
        self._enable_click_through()
        self._start_fade(0.0, 1.0, _FADE_IN_MS)
        self.update()

    def clear(self) -> None:
        self._start_fade(self.windowOpacity(), 0.0, _FADE_OUT_MS, hide_at_end=True)

    def _relayout(self) -> None:
        if self._anchor is None:
            return
        width = self._anchor["width"]
        metrics = QFontMetrics(renderer.font_for(self._style))
        line_height = metrics.lineSpacing()
        text_width = width - renderer.ACCENT_WIDTH - 2 * renderer.PADDING_X
        bounding = metrics.boundingRect(
            QRect(0, 0, text_width, 0),
            int(Qt.TextFlag.TextWordWrap),
            self._text,
        )
        lines = min(max(bounding.height() // line_height, 1), _MAX_LINES)
        height = lines * line_height + 2 * renderer.PADDING_Y
        left = self._anchor["left"]
        top = self._anchor["top"] + self._anchor["height"] + _GAP
        self.setGeometry(left, top, width, height)

    def _start_fade(
        self, start: float, end: float, duration: int, hide_at_end: bool = False
    ) -> None:
        self._fade.stop()
        self._fade.setDuration(duration)
        self._fade.setStartValue(start)
        self._fade.setEndValue(end)
        with contextlib.suppress(TypeError):
            self._fade.finished.disconnect()
        if hide_at_end:
            self._fade.finished.connect(self.hide)
        self._fade.start()

    def _enable_click_through(self) -> None:
        """Make the window ignore mouse input so clicks reach the game behind it."""
        if sys.platform != "win32":
            return
        import ctypes

        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x00080000
        WS_EX_TRANSPARENT = 0x00000020
        hwnd = int(self.winId())
        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(
            hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT
        )

    def paintEvent(self, event: QPaintEvent) -> None:
        if not self._text:
            return
        painter = QPainter(self)
        renderer.draw(painter, self.rect(), self._text, self._style)
