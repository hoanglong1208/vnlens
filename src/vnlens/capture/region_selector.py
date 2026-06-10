from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QGuiApplication, QKeyEvent, QMouseEvent, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from ..config.schema import Region

_VEIL = QColor(0, 0, 0, 110)
_BORDER = QColor(0xE9, 0x45, 0x60)
_LABEL_BG = QColor(0, 0, 0, 180)
_LABEL_COLOR = QColor(0xEA, 0xEA, 0xEA)


class RegionSelector(QWidget):
    """Full-screen translucent overlay. The user drags a rectangle around the
    game text box; the selection is emitted as a Region in screen fractions."""

    selected = pyqtSignal(Region)
    cancelled = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._origin: QPoint | None = None
        self._current = QRect()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setGeometry(QGuiApplication.primaryScreen().geometry())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self._origin = event.position().toPoint()
        self._current = QRect(self._origin, self._origin)
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._origin is not None:
            self._current = QRect(self._origin, event.position().toPoint()).normalized()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._origin is None:
            return
        self._origin = None
        # Drags can extend past the screen edge (negative coords); clamp before
        # converting, or Region validation rejects the selection.
        rect = self._current.intersected(self.rect())
        if rect.width() < 5 or rect.height() < 5:
            return
        self.selected.emit(self._to_region(rect))
        self.close()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.cancelled.emit()
            self.close()

    def _to_region(self, rect: QRect) -> Region:
        screen = self.geometry()
        return Region(
            left=rect.left() / screen.width(),
            top=rect.top() / screen.height(),
            width=rect.width() / screen.width(),
            height=rect.height() / screen.height(),
        )

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), _VEIL)
        if self._current.isNull():
            return

        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(self._current, Qt.GlobalColor.transparent)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

        painter.setPen(QPen(_BORDER, 2))
        painter.drawRect(self._current)
        self._draw_label(painter)

    def _draw_label(self, painter: QPainter) -> None:
        label = f"{self._current.width()} x {self._current.height()}"
        metrics = painter.fontMetrics()
        text_rect = metrics.boundingRect(label).adjusted(-6, -3, 6, 3)
        text_rect.moveTopLeft(
            QPoint(self._current.left(), self._current.top() - text_rect.height())
        )
        painter.fillRect(text_rect, _LABEL_BG)
        painter.setPen(_LABEL_COLOR)
        painter.drawText(text_rect, int(Qt.AlignmentFlag.AlignCenter), label)
