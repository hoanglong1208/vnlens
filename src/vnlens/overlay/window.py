import contextlib
import sys

from PyQt6.QtCore import QPoint, QPropertyAnimation, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QFontMetrics, QGuiApplication, QMouseEvent, QPainter, QPaintEvent, QPen
from PyQt6.QtWidgets import QWidget

from ..config.schema import OverlayConfig
from . import renderer

_GAP = 8
_MAX_LINES = 4
_FADE_IN_MS = 150
_FADE_OUT_MS = 100
_FALLBACK_WIDTH_FRAC = 0.4
_MOVE_HINT = "Kéo overlay đến vị trí mong muốn, nhấn F4 để khoá"


class OverlayWindow(QWidget):
    """Frameless, always-on-top window showing the translation.

    Two placement modes: anchored (follows the capture region, flipping above it
    when there is no room below) and float (a fixed position the user picked by
    dragging). The window is click-through except in move mode, where dragging
    is enabled and a dashed border is drawn.
    """

    moved = pyqtSignal(float, float)  # new top-left corner as screen fractions

    def __init__(self, config: OverlayConfig) -> None:
        super().__init__()
        self._style = renderer.TextStyle.from_config(config)
        self._text = ""
        self._anchor: dict[str, int] | None = None
        self._position_mode: str = config.position_mode
        self._float_pos: tuple[float, float] | None = (
            (config.float_pos.x, config.float_pos.y) if config.float_pos else None
        )
        self._move_mode = False
        self._hint_shown = False
        self._drag_offset: QPoint | None = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self._fade = QPropertyAnimation(self, b"windowOpacity")

    def apply_config(self, config: OverlayConfig) -> None:
        """Apply new overlay settings live, without recreating the window."""
        self._style = renderer.TextStyle.from_config(config)
        self._position_mode = config.position_mode
        self._float_pos = (
            (config.float_pos.x, config.float_pos.y) if config.float_pos else None
        )
        if self.isVisible():
            self._relayout()
            self.update()

    def set_anchor(self, region_px: dict[str, int]) -> None:
        """Set the capture region (in screen pixels) the overlay anchors to."""
        self._anchor = region_px
        if self.isVisible():
            self._relayout()

    def set_position_mode(self, mode: str, float_pos: tuple[float, float] | None) -> None:
        self._position_mode = mode
        self._float_pos = float_pos
        if self.isVisible():
            self._relayout()

    def set_move_mode(self, enabled: bool) -> None:
        self._move_mode = enabled
        if enabled:
            if not self._text:
                self.show_text(_MOVE_HINT)
                self._hint_shown = True
            self.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self._drag_offset = None
            self.unsetCursor()
            if self._hint_shown:
                self._hint_shown = False
                self._text = ""
                self.hide()
        self._set_click_through(not enabled)
        self.update()

    def show_text(self, text: str) -> None:
        self._text = text
        self._hint_shown = False
        self._relayout()
        # Fade in only from hidden; consecutive lines would flicker otherwise.
        if self.isVisible():
            self._stop_fade()
            self.setWindowOpacity(1.0)
        else:
            self.setWindowOpacity(0.0)
            self.show()
            self._set_click_through(not self._move_mode)
            self._start_fade(0.0, 1.0, _FADE_IN_MS)
        self.update()

    def clear(self) -> None:
        if self._move_mode:
            return
        self._start_fade(self.windowOpacity(), 0.0, _FADE_OUT_MS, hide_at_end=True)

    def _relayout(self) -> None:
        screen = QGuiApplication.primaryScreen().geometry()
        width = (
            self._anchor["width"]
            if self._anchor is not None
            else round(screen.width() * _FALLBACK_WIDTH_FRAC)
        )

        metrics = QFontMetrics(renderer.font_for(self._style))
        line_height = metrics.lineSpacing()
        text_width = width - renderer.ACCENT_WIDTH - 2 * renderer.PADDING_X
        bounding = metrics.boundingRect(
            QRect(0, 0, text_width, 0),
            int(Qt.TextFlag.TextWordWrap),
            self._text,
        )
        lines = (bounding.height() + line_height - 1) // line_height
        height = min(max(lines, 1), _MAX_LINES) * line_height + 2 * renderer.PADDING_Y

        if self._position_mode == "float" and self._float_pos is not None:
            left = round(self._float_pos[0] * screen.width())
            top = round(self._float_pos[1] * screen.height())
        elif self._anchor is not None:
            left = self._anchor["left"]
            top = self._anchor["top"] + self._anchor["height"] + _GAP
            # VN text boxes usually sit at the bottom of the screen; flip the
            # overlay above the region when it would not fit below.
            if top + height - 1 > screen.bottom():
                top = self._anchor["top"] - _GAP - height
        else:
            left = round((screen.width() - width) / 2)
            top = round(screen.height() * 0.7)

        left = max(screen.left(), min(left, screen.right() - width + 1))
        top = max(screen.top(), min(top, screen.bottom() - height + 1))
        self.setGeometry(left, top, width, height)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._move_mode and event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._drag_offset is None:
            return
        self._drag_offset = None
        screen = QGuiApplication.primaryScreen().geometry()
        x = min(max(self.frameGeometry().left() / screen.width(), 0.0), 1.0)
        y = min(max(self.frameGeometry().top() / screen.height(), 0.0), 1.0)
        self._position_mode = "float"
        self._float_pos = (x, y)
        self.moved.emit(x, y)

    def _stop_fade(self) -> None:
        """Stop any running fade. Disconnect first: stop() emits finished, which
        would otherwise trigger a pending hide."""
        with contextlib.suppress(TypeError):
            self._fade.finished.disconnect()
        self._fade.stop()

    def _start_fade(
        self, start: float, end: float, duration: int, hide_at_end: bool = False
    ) -> None:
        self._stop_fade()
        self._fade.setDuration(duration)
        self._fade.setStartValue(start)
        self._fade.setEndValue(end)
        if hide_at_end:
            self._fade.finished.connect(self.hide)
        self._fade.start()

    def _set_click_through(self, enabled: bool) -> None:
        """Toggle the Win32 style that lets mouse input pass through to the game.
        Disabled while in move mode so the window can be dragged."""
        if sys.platform != "win32":
            return
        import ctypes

        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x00080000
        WS_EX_TRANSPARENT = 0x00000020
        hwnd = int(self.winId())
        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE) | WS_EX_LAYERED
        if enabled:
            style |= WS_EX_TRANSPARENT
        else:
            style &= ~WS_EX_TRANSPARENT
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)

    def paintEvent(self, event: QPaintEvent) -> None:
        if not self._text:
            return
        painter = QPainter(self)
        renderer.draw(painter, self.rect(), self._text, self._style)
        if self._move_mode:
            painter.setPen(QPen(renderer.ACCENT_COLOR, 1, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
