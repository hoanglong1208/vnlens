from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPaintEvent
from PyQt6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .. import __version__
from ..config.schema import AppConfig
from ..overlay import renderer
from ..translation.registry import available_providers
from ..utils import dpapi
from .connection_test import run_connection_test
from .theme import TEXT_DIM

_PREVIEW_TEXT = "Hoa anh đào đang nở rộ ngoài sân trường."
_PROVIDER_CHOICES = [
    ("deepl", "DeepL"),
    ("google", "Google Translate (sắp có)"),
    ("claude", "Claude API (sắp có)"),
    ("libre", "LibreTranslate (sắp có)"),
]
_LANG_CHOICES = [("auto", "Tự động"), ("en", "Tiếng Anh"), ("ja", "Tiếng Nhật")]
_HOTKEY_CHOICES = [f"f{n}" for n in range(1, 13)]


def _dim_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setProperty("dim", "true")
    label.setWordWrap(True)
    return label


class _TranslationPage(QWidget):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self._config = config

        self._provider = QComboBox()
        enabled = set(available_providers())
        for provider_id, label in _PROVIDER_CHOICES:
            self._provider.addItem(label, provider_id)
            if provider_id not in enabled:
                index = self._provider.count() - 1
                self._provider.model().item(index).setEnabled(False)
            if provider_id == config.translation.provider:
                self._provider.setCurrentIndex(self._provider.count() - 1)

        self._key = QLineEdit()
        self._key.setEchoMode(QLineEdit.EchoMode.Password)
        has_key = config.translation.provider in config.translation.api_keys
        self._key.setPlaceholderText(
            "Đã lưu — nhập để thay key" if has_key else "Nhập API key"
        )

        test_button = QPushButton("Kiểm tra kết nối")
        test_button.clicked.connect(self._on_test)
        self._result = _dim_label("")

        form = QFormLayout(self)
        form.addRow("Dịch vụ:", self._provider)
        form.addRow("API key:", self._key)
        form.addRow("", test_button)
        form.addRow("", self._result)
        form.addRow("Ngôn ngữ đích:", _dim_label("Tiếng Việt"))

    def _on_test(self) -> None:
        key = self._key.text().strip() or self._stored_key()
        if not key:
            self._result.setText("Chưa có API key.")
            return
        self._result.setText("Đang kiểm tra...")
        provider_id = self._provider.currentData()
        QTimer.singleShot(0, lambda: self._run_test(provider_id, key))

    def _run_test(self, provider_id: str, key: str) -> None:
        ok, message = run_connection_test(provider_id, key)
        self._result.setText(f"→ {message}" if ok else f"Lỗi: {message}")

    def _stored_key(self) -> str:
        encrypted = self._config.translation.api_keys.get(self._provider.currentData())
        if not encrypted:
            return ""
        try:
            return dpapi.decrypt(encrypted)
        except OSError:
            return ""

    def apply(self, config: AppConfig) -> None:
        config.translation.provider = self._provider.currentData()
        new_key = self._key.text().strip()
        if new_key:
            config.translation.api_keys[config.translation.provider] = dpapi.encrypt(new_key)


class _OverlayPreview(QWidget):
    def __init__(self, style: renderer.TextStyle) -> None:
        super().__init__()
        self.style = style
        self.setMinimumHeight(76)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        renderer.draw(painter, self.rect(), _PREVIEW_TEXT, self.style)


class _OverlayPage(QWidget):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        overlay = config.overlay
        self._color = QColor(overlay.text_color)
        self._preview = _OverlayPreview(renderer.TextStyle.from_config(overlay))

        self._font_size = QSlider(Qt.Orientation.Horizontal)
        self._font_size.setRange(12, 24)
        self._font_size.setValue(overlay.font_size)

        self._opacity = QSlider(Qt.Orientation.Horizontal)
        self._opacity.setRange(0, 95)
        self._opacity.setValue(round(overlay.opacity * 100))

        self._shadow = QCheckBox("Đổ bóng chữ")
        self._shadow.setChecked(overlay.shadow)

        self._color_button = QPushButton()
        self._color_button.setFixedWidth(60)
        self._color_button.clicked.connect(self._pick_color)

        for signal in (self._font_size.valueChanged, self._opacity.valueChanged):
            signal.connect(self._refresh_preview)
        self._shadow.toggled.connect(self._refresh_preview)

        form = QFormLayout(self)
        form.addRow("Cỡ chữ:", self._font_size)
        form.addRow("Độ mờ nền:", self._opacity)
        form.addRow("Màu chữ:", self._color_button)
        form.addRow("", self._shadow)
        form.addRow("Xem trước:", self._preview)
        form.addRow(
            "",
            _dim_label("Nhấn F4 để kéo overlay đến vị trí bất kỳ; menu tray có "
                       '"Bám dưới vùng chọn" để quay về vị trí tự động.'),
        )
        self._refresh_preview()

    def _pick_color(self) -> None:
        color = QColorDialog.getColor(self._color, self, "Màu chữ overlay")
        if color.isValid():
            self._color = color
            self._refresh_preview()

    def _refresh_preview(self) -> None:
        self._color_button.setStyleSheet(f"background: {self._color.name()};")
        self._preview.style = renderer.TextStyle(
            font_size=self._font_size.value(),
            text_color=self._color,
            bg_opacity=self._opacity.value() / 100,
            shadow=self._shadow.isChecked(),
        )
        self._preview.update()

    def apply(self, config: AppConfig) -> None:
        config.overlay.font_size = self._font_size.value()
        config.overlay.opacity = self._opacity.value() / 100
        config.overlay.text_color = self._color.name()
        config.overlay.shadow = self._shadow.isChecked()


class _OcrPage(QWidget):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self._engine = QComboBox()
        self._engine.addItem("Windows OCR (khuyến nghị)", "winrt")
        self._engine.addItem("EasyOCR (sắp có)", "easyocr")
        self._engine.model().item(1).setEnabled(False)

        self._lang = QComboBox()
        for code, label in _LANG_CHOICES:
            self._lang.addItem(label, code)
            if code == config.ocr.source_lang:
                self._lang.setCurrentIndex(self._lang.count() - 1)

        self._interval = QSlider(Qt.Orientation.Horizontal)
        self._interval.setRange(300, 1000)
        self._interval.setSingleStep(50)
        self._interval.setValue(config.capture.interval_ms)
        self._interval_label = _dim_label("")
        self._interval.valueChanged.connect(self._update_interval_label)
        self._update_interval_label()

        form = QFormLayout(self)
        form.addRow("Engine:", self._engine)
        form.addRow("Ngôn ngữ nguồn:", self._lang)
        form.addRow("Chu kỳ quét:", self._interval)
        form.addRow("", self._interval_label)

    def _update_interval_label(self) -> None:
        self._interval_label.setText(
            f"{self._interval.value()} ms — nhanh hơn tốn CPU hơn, chậm hơn tiết kiệm hơn."
        )

    def apply(self, config: AppConfig) -> None:
        config.ocr.engine = self._engine.currentData()
        config.ocr.source_lang = self._lang.currentData()
        config.capture.interval_ms = self._interval.value()


class _HotkeysPage(QWidget):
    _ACTIONS = [
        ("toggle", "Tạm dừng / tiếp tục:"),
        ("select_region", "Chọn vùng dịch:"),
        ("move_overlay", "Di chuyển overlay:"),
    ]

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self._combos: dict[str, QComboBox] = {}
        form = QFormLayout(self)
        for field, label in self._ACTIONS:
            combo = QComboBox()
            current = getattr(config.hotkeys, field)
            for key in _HOTKEY_CHOICES:
                combo.addItem(key.upper(), key)
                if key == current:
                    combo.setCurrentIndex(combo.count() - 1)
            self._combos[field] = combo
            form.addRow(label, combo)
        form.addRow("", _dim_label("Phím tắt hoạt động cả khi game đang focus."))

    def conflict(self) -> bool:
        keys = [combo.currentData() for combo in self._combos.values()]
        return len(set(keys)) != len(keys)

    def apply(self, config: AppConfig) -> None:
        for field, combo in self._combos.items():
            setattr(config.hotkeys, field, combo.currentData())


class _AboutPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel(f"VNLens {__version__}")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        link = QLabel(
            '<a style="color:#e94560" href="https://github.com/hoanglong1208/vnlens">'
            "github.com/hoanglong1208/vnlens</a>"
        )
        link.setOpenExternalLinks(True)
        layout.addWidget(title)
        layout.addWidget(_dim_label("Dịch màn hình thời gian thực cho visual novel."))
        layout.addWidget(link)
        layout.addWidget(_dim_label("Mã nguồn mở theo giấy phép MIT. Mọi tính năng miễn phí."))
        layout.addStretch()


class SettingsDialog(QDialog):
    """Sidebar-style settings dashboard. Edits a copy of the config and emits
    `saved` with the new config when the user confirms."""

    saved = pyqtSignal(AppConfig)

    _SECTIONS = [
        ("Dịch thuật", _TranslationPage),
        ("Overlay", _OverlayPage),
        ("OCR", _OcrPage),
        ("Phím tắt", _HotkeysPage),
        ("Giới thiệu", _AboutPage),
    ]

    def __init__(self, config: AppConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Cài đặt VNLens")
        self.resize(640, 440)
        self._config = config.model_copy(deep=True)

        nav = QListWidget()
        nav.setFixedWidth(150)
        stack = QStackedWidget()
        self._pages: list[QWidget] = []
        for label, page_cls in self._SECTIONS:
            nav.addItem(label)
            page = page_cls(self._config) if page_cls is not _AboutPage else page_cls()
            self._pages.append(page)
            stack.addWidget(page)
        nav.currentRowChanged.connect(stack.setCurrentIndex)
        nav.setCurrentRow(0)

        self._error = QLabel("")
        self._error.setStyleSheet(f"color: {TEXT_DIM};")
        save_button = QPushButton("Lưu")
        save_button.setDefault(True)
        save_button.clicked.connect(self._save)
        cancel_button = QPushButton("Huỷ")
        cancel_button.clicked.connect(self.reject)

        buttons = QHBoxLayout()
        buttons.addWidget(self._error)
        buttons.addStretch()
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)

        content = QVBoxLayout()
        content.addWidget(stack)
        content.addLayout(buttons)

        root = QHBoxLayout(self)
        root.addWidget(nav)
        root.addLayout(content)

    def _save(self) -> None:
        hotkeys_page = next(p for p in self._pages if isinstance(p, _HotkeysPage))
        if hotkeys_page.conflict():
            self._error.setText("Các phím tắt phải khác nhau.")
            return
        for page in self._pages:
            if hasattr(page, "apply"):
                page.apply(self._config)
        self.saved.emit(self._config)
        self.accept()
