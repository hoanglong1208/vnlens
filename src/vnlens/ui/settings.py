from collections.abc import Callable

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPaintEvent
from PyQt6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
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
from .theme import ACCENT, SIDEBAR_BG

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


def _scaffold(page: QWidget, title: str, subtitle: str) -> QFormLayout:
    """Standard page layout: header, divider, then a form with roomy spacing."""
    layout = QVBoxLayout(page)
    layout.setContentsMargins(28, 24, 28, 24)
    layout.setSpacing(6)

    heading = QLabel(title)
    heading.setObjectName("pageTitle")
    layout.addWidget(heading)
    layout.addWidget(_dim_label(subtitle))

    divider = QFrame()
    divider.setObjectName("divider")
    divider.setFixedHeight(1)
    layout.addSpacing(8)
    layout.addWidget(divider)
    layout.addSpacing(10)

    form = QFormLayout()
    form.setVerticalSpacing(14)
    form.setHorizontalSpacing(18)
    form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
    layout.addLayout(form)
    layout.addStretch()
    return form


def _labeled_slider(
    low: int, high: int, value: int, fmt: Callable[[int], str]
) -> tuple[QSlider, QWidget]:
    """A slider with a live value label to its right."""
    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(low, high)
    slider.setValue(value)

    label = _dim_label(fmt(value))
    label.setFixedWidth(64)
    label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    slider.valueChanged.connect(lambda v: label.setText(fmt(v)))

    row = QWidget()
    box = QHBoxLayout(row)
    box.setContentsMargins(0, 0, 0, 0)
    box.setSpacing(10)
    box.addWidget(slider)
    box.addWidget(label)
    return slider, row


class _TranslationPage(QWidget):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self._config = config
        form = _scaffold(self, "Dịch thuật", "Dịch vụ dịch và API key của bạn.")

        self._provider = QComboBox()
        enabled = set(available_providers())
        for provider_id, label in _PROVIDER_CHOICES:
            self._provider.addItem(label, provider_id)
            if provider_id not in enabled:
                self._provider.model().item(self._provider.count() - 1).setEnabled(False)
            if provider_id == config.translation.provider:
                self._provider.setCurrentIndex(self._provider.count() - 1)

        self._key = QLineEdit()
        self._key.setEchoMode(QLineEdit.EchoMode.Password)
        has_key = config.translation.provider in config.translation.api_keys
        self._key.setPlaceholderText("Đã lưu — nhập để thay key" if has_key else "Nhập API key")

        test_button = QPushButton("Kiểm tra kết nối")
        test_button.clicked.connect(self._on_test)
        test_row = QWidget()
        test_box = QHBoxLayout(test_row)
        test_box.setContentsMargins(0, 0, 0, 0)
        test_box.setSpacing(10)
        test_box.addWidget(test_button)
        test_box.addStretch()
        self._result = _dim_label("")

        form.addRow("Dịch vụ:", self._provider)
        form.addRow("API key:", self._key)
        form.addRow("", test_row)
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
        self.setMinimumHeight(84)

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        renderer.draw(painter, self.rect(), _PREVIEW_TEXT, self.style)


class _OverlayPage(QWidget):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        overlay = config.overlay
        self._color = QColor(overlay.text_color)
        self._preview = _OverlayPreview(renderer.TextStyle.from_config(overlay))
        form = _scaffold(self, "Overlay", "Giao diện hộp dịch hiển thị trên game.")

        self._font_size, font_row = _labeled_slider(
            12, 24, overlay.font_size, lambda v: f"{v} px"
        )
        self._opacity, opacity_row = _labeled_slider(
            0, 95, round(overlay.opacity * 100), lambda v: f"{v}%"
        )

        self._shadow = QCheckBox("Đổ bóng chữ")
        self._shadow.setChecked(overlay.shadow)

        self._color_button = QPushButton()
        self._color_button.setFixedSize(64, 28)
        self._color_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._color_button.clicked.connect(self._pick_color)

        self._font_size.valueChanged.connect(self._refresh_preview)
        self._opacity.valueChanged.connect(self._refresh_preview)
        self._shadow.toggled.connect(self._refresh_preview)

        form.addRow("Cỡ chữ:", font_row)
        form.addRow("Độ mờ nền:", opacity_row)
        form.addRow("Màu chữ:", self._color_button)
        form.addRow("", self._shadow)
        form.addRow("Xem trước:", self._preview)
        form.addRow(
            "",
            _dim_label('Nhấn F4 để kéo overlay đến vị trí bất kỳ; menu tray có '
                       '"Bám dưới vùng chọn" để quay về vị trí tự động.'),
        )
        self._refresh_preview()

    def _pick_color(self) -> None:
        color = QColorDialog.getColor(self._color, self, "Màu chữ overlay")
        if color.isValid():
            self._color = color
            self._refresh_preview()

    def _refresh_preview(self) -> None:
        self._color_button.setStyleSheet(
            f"background: {self._color.name()}; border-radius: 6px; border: 1px solid #2e3458;"
        )
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
        form = _scaffold(self, "OCR", "Nhận diện chữ và tần suất quét màn hình.")

        self._engine = QComboBox()
        self._engine.addItem("Windows OCR (khuyến nghị)", "winrt")
        self._engine.addItem("EasyOCR (sắp có)", "easyocr")
        self._engine.model().item(1).setEnabled(False)

        self._lang = QComboBox()
        for code, label in _LANG_CHOICES:
            self._lang.addItem(label, code)
            if code == config.ocr.source_lang:
                self._lang.setCurrentIndex(self._lang.count() - 1)

        self._interval, interval_row = _labeled_slider(
            300, 1000, config.capture.interval_ms, lambda v: f"{v} ms"
        )

        form.addRow("Engine:", self._engine)
        form.addRow("Ngôn ngữ nguồn:", self._lang)
        form.addRow("Chu kỳ quét:", interval_row)
        form.addRow("", _dim_label("Quét nhanh phản hồi sớm hơn nhưng tốn CPU hơn."))

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
        form = _scaffold(self, "Phím tắt", "Hoạt động cả khi game đang focus.")
        self._combos: dict[str, QComboBox] = {}
        for field, label in self._ACTIONS:
            combo = QComboBox()
            current = getattr(config.hotkeys, field)
            for key in _HOTKEY_CHOICES:
                combo.addItem(key.upper(), key)
                if key == current:
                    combo.setCurrentIndex(combo.count() - 1)
            self._combos[field] = combo
            form.addRow(label, combo)

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
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(8)

        title = QLabel("VNLens")
        title.setObjectName("brand")
        layout.addWidget(title)
        layout.addWidget(_dim_label(f"Phiên bản {__version__}"))
        layout.addSpacing(10)
        layout.addWidget(QLabel("Dịch màn hình thời gian thực cho visual novel."))
        link = QLabel(
            f'<a style="color:{ACCENT}" href="https://github.com/hoanglong1208/vnlens">'
            "github.com/hoanglong1208/vnlens</a>"
        )
        link.setOpenExternalLinks(True)
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
        self.resize(700, 480)
        # Below this the form rows and footer start clipping.
        self.setMinimumSize(640, 440)
        self._config = config.model_copy(deep=True)

        sidebar = QWidget()
        sidebar.setFixedWidth(176)
        sidebar.setStyleSheet(f"background: {SIDEBAR_BG};")
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(0, 0, 0, 0)
        side.setSpacing(0)

        brand_box = QWidget()
        brand_layout = QVBoxLayout(brand_box)
        brand_layout.setContentsMargins(18, 20, 18, 14)
        brand_layout.setSpacing(2)
        brand = QLabel("VNLens")
        brand.setObjectName("brand")
        brand_layout.addWidget(brand)
        brand_layout.addWidget(_dim_label(f"v{__version__}"))
        side.addWidget(brand_box)

        nav = QListWidget()
        nav.setObjectName("nav")
        stack = QStackedWidget()
        self._pages: list[QWidget] = []
        for label, page_cls in self._SECTIONS:
            nav.addItem(label)
            page = page_cls(self._config) if page_cls is not _AboutPage else page_cls()
            self._pages.append(page)
            stack.addWidget(page)
        nav.currentRowChanged.connect(stack.setCurrentIndex)
        nav.setCurrentRow(0)
        side.addWidget(nav)

        self._error = QLabel("")
        self._error.setStyleSheet(f"color: {ACCENT};")
        save_button = QPushButton("Lưu")
        save_button.setObjectName("primary")
        save_button.setDefault(True)
        save_button.clicked.connect(self._save)
        cancel_button = QPushButton("Huỷ")
        cancel_button.clicked.connect(self.reject)

        footer_divider = QFrame()
        footer_divider.setObjectName("divider")
        footer_divider.setFixedHeight(1)

        buttons = QHBoxLayout()
        buttons.setContentsMargins(28, 12, 28, 16)
        buttons.setSpacing(10)
        buttons.addWidget(self._error)
        buttons.addStretch()
        buttons.addWidget(cancel_button)
        buttons.addWidget(save_button)

        content = QVBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)
        content.addWidget(stack)
        content.addWidget(footer_divider)
        content.addLayout(buttons)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(sidebar)
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
