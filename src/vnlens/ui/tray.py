from enum import Enum

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

from ..utils.resources import resource_path

_PAUSE_LABEL = "Tạm dừng"
_RESUME_LABEL = "Tiếp tục"
_DOT_BG = QColor(0x1A, 0x1A, 0x2E)


class TrayStatus(Enum):
    """Tray states: the colored logo carries a status dot; paused shows the
    grayscale logo with no dot."""

    ACTIVE = ("Đang dịch", QColor(0x4C, 0xAF, 0x50))
    WAITING = ("Đang chờ", QColor(0xFF, 0xC1, 0x07))
    ERROR = ("Lỗi", QColor(0xE5, 0x39, 0x35))
    PAUSED = (_PAUSE_LABEL, None)

    def __init__(self, label: str, dot_color: QColor | None) -> None:
        self.label = label
        self.dot_color = dot_color


_icon_cache: dict[TrayStatus, QIcon] = {}


def _status_icon(status: TrayStatus) -> QIcon:
    if status in _icon_cache:
        return _icon_cache[status]

    name = "tray-off.png" if status is TrayStatus.PAUSED else "tray-on.png"
    pixmap = QPixmap(str(resource_path(f"assets/icons/{name}")))
    if status.dot_color is not None:
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        # Dark rim separates the dot from the badge underneath.
        painter.setBrush(_DOT_BG)
        painter.drawEllipse(37, 37, 26, 26)
        painter.setBrush(status.dot_color)
        painter.drawEllipse(40, 40, 20, 20)
        painter.end()

    icon = QIcon(pixmap)
    _icon_cache[status] = icon
    return icon


class TrayIcon(QSystemTrayIcon):
    toggle_requested = pyqtSignal()
    select_region_requested = pyqtSignal()
    settings_requested = pyqtSignal()
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
        menu.addAction("Cài đặt").triggered.connect(self.settings_requested)
        menu.addSeparator()
        self._move_action = menu.addAction("Di chuyển overlay")
        self._move_action.setCheckable(True)
        self._move_action.toggled.connect(self.move_overlay_toggled)
        menu.addAction("Bám dưới vùng chọn").triggered.connect(self.reset_position_requested)
        menu.addSeparator()
        menu.addAction("Thoát").triggered.connect(self.quit_requested)
        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)

        self.set_status(TrayStatus.ACTIVE)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.settings_requested.emit()

    def set_status(self, status: TrayStatus) -> None:
        self.setIcon(_status_icon(status))
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
