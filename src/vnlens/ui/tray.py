from enum import Enum

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

_ICON_SIZE = 64
_PAUSE_LABEL = "Tạm dừng"
_RESUME_LABEL = "Tiếp tục"


class TrayStatus(Enum):
    ACTIVE = ("Đang dịch", QColor(0x4C, 0xAF, 0x50))
    WAITING = ("Đang chờ", QColor(0xFF, 0xC1, 0x07))
    ERROR = ("Lỗi", QColor(0xE5, 0x39, 0x35))
    PAUSED = (_PAUSE_LABEL, QColor(0x9E, 0x9E, 0x9E))

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
    move_overlay_toggled = pyqtSignal(bool)
    reset_position_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.setToolTip("VNLens")

        # setContextMenu does not take ownership; keep a reference or the menu
        # gets garbage-collected and right-click shows nothing.
        menu = self._menu = QMenu()
        self._status_action = menu.addAction("Đang dịch")
        self._status_action.setEnabled(False)
        menu.addSeparator()
        self._toggle_action = menu.addAction(_PAUSE_LABEL)
        self._toggle_action.triggered.connect(self.toggle_requested)
        menu.addAction("Chọn vùng mới").triggered.connect(self.select_region_requested)
        menu.addSeparator()
        self._move_action = menu.addAction("Di chuyển overlay")
        self._move_action.setCheckable(True)
        self._move_action.toggled.connect(self.move_overlay_toggled)
        menu.addAction("Bám dưới vùng chọn").triggered.connect(self.reset_position_requested)
        menu.addSeparator()
        menu.addAction("Thoát").triggered.connect(self.quit_requested)
        self.setContextMenu(menu)

        self.set_status(TrayStatus.ACTIVE)

    def set_status(self, status: TrayStatus) -> None:
        self.setIcon(_status_icon(status.color))
        self._status_action.setText(status.label)
        self._toggle_action.setText(
            _RESUME_LABEL if status is TrayStatus.PAUSED else _PAUSE_LABEL
        )

    def toggle_move_mode(self) -> None:
        """Flip the move-overlay action; its toggled signal drives the handler,
        so hotkey and menu share one code path."""
        self._move_action.toggle()

    def set_move_checked(self, checked: bool) -> None:
        self._move_action.setChecked(checked)
