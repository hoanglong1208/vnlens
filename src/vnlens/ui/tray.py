from enum import Enum

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

_ICON_SIZE = 64


class TrayStatus(Enum):
    ACTIVE = ("Đang dịch", QColor(0x4C, 0xAF, 0x50))
    WAITING = ("Đang chờ", QColor(0xFF, 0xC1, 0x07))
    ERROR = ("Lỗi", QColor(0xE5, 0x39, 0x35))
    PAUSED = ("Tạm dừng", QColor(0x9E, 0x9E, 0x9E))

    def __init__(self, label: str, color: QColor) -> None:
        self.label = label
        self.color = color


def _status_icon(color: QColor) -> QIcon:
    pixmap = QPixmap(_ICON_SIZE, _ICON_SIZE)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    painter.drawEllipse(8, 8, _ICON_SIZE - 16, _ICON_SIZE - 16)
    painter.end()
    return QIcon(pixmap)


class TrayIcon(QSystemTrayIcon):
    toggle_requested = pyqtSignal()
    select_region_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.setToolTip("VNLens")

        menu = QMenu()
        self._status_action = menu.addAction("Đang dịch")
        self._status_action.setEnabled(False)
        menu.addSeparator()
        self._toggle_action = menu.addAction("Tạm dừng")
        self._toggle_action.triggered.connect(self.toggle_requested)
        menu.addAction("Chọn vùng mới").triggered.connect(self.select_region_requested)
        menu.addSeparator()
        menu.addAction("Thoát").triggered.connect(self.quit_requested)
        self.setContextMenu(menu)

        self.set_status(TrayStatus.ACTIVE)

    def set_status(self, status: TrayStatus) -> None:
        self.setIcon(_status_icon(status.color))
        self._status_action.setText(status.label)
        self._toggle_action.setText(
            "Tiếp tục" if status is TrayStatus.PAUSED else "Tạm dừng"
        )
