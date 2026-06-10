from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QButtonGroup,
    QLabel,
    QLineEdit,
    QRadioButton,
    QVBoxLayout,
    QWizard,
    QWizardPage,
)

from ..translation.registry import available_providers
from .connection_test import SAMPLE_TEXT, run_connection_test

# (id, label, enabled) — only providers implemented in this version are selectable.
_PROVIDER_CHOICES = [
    ("deepl", "DeepL (khuyến nghị)"),
    ("google", "Google Translate (sắp có)"),
    ("claude", "Claude API (sắp có)"),
    ("libre", "LibreTranslate (sắp có)"),
]


class _ProviderPage(QWizardPage):
    def __init__(self, wizard: "SetupWizard") -> None:
        super().__init__()
        self._wizard = wizard
        self.setTitle("Chọn dịch vụ dịch thuật")

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        self._group = QButtonGroup(self)
        enabled = set(available_providers())
        for provider_id, label in _PROVIDER_CHOICES:
            button = QRadioButton(label)
            button.setEnabled(provider_id in enabled)
            button.setProperty("provider_id", provider_id)
            if provider_id == wizard.provider_id:
                button.setChecked(True)
            self._group.addButton(button)
            layout.addWidget(button)

        layout.addWidget(QLabel("API Key:"))
        self._key_field = QLineEdit()
        self._key_field.setEchoMode(QLineEdit.EchoMode.Password)
        self._key_field.textChanged.connect(self.completeChanged)
        layout.addWidget(self._key_field)

    def isComplete(self) -> bool:
        return bool(self._key_field.text().strip())

    def validatePage(self) -> bool:
        self._wizard.provider_id = self._group.checkedButton().property("provider_id")
        self._wizard.api_key = self._key_field.text().strip()
        return True


class _TestPage(QWizardPage):
    def __init__(self, wizard: "SetupWizard") -> None:
        super().__init__()
        self._wizard = wizard
        self._passed = False
        self.setTitle("Kiểm tra kết nối")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f'"{SAMPLE_TEXT}"'))
        self._result = QLabel("Đang kiểm tra kết nối...")
        self._result.setWordWrap(True)
        layout.addWidget(self._result)

    def initializePage(self) -> None:
        self._passed = False
        self._result.setText("Đang kiểm tra kết nối...")
        # Let the page paint before the blocking network call.
        QTimer.singleShot(0, self._run_test)

    def _run_test(self) -> None:
        ok, message = run_connection_test(self._wizard.provider_id, self._wizard.api_key)
        self._result.setText(f"→ {message}" if ok else f"Lỗi: {message}")
        self._passed = ok
        self.completeChanged.emit()

    def isComplete(self) -> bool:
        return self._passed


class SetupWizard(QWizard):
    """First-run setup: pick a provider, enter the API key, and verify it works.
    Region selection runs afterwards from the main controller."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("VNLens · Thiết lập lần đầu")
        # ModernStyle renders consistently with the app stylesheet; the native
        # Aero style on Windows ignores parts of it.
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(480, 380)
        self.provider_id = "deepl"
        self.api_key = ""
        self.addPage(_ProviderPage(self))
        self.addPage(_TestPage(self))
