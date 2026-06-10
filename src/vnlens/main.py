import logging
import sys

from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtGui import QFontDatabase, QGuiApplication
from PyQt6.QtWidgets import QApplication

from .capture.region_selector import RegionSelector
from .config.manager import ConfigManager
from .config.schema import Region
from .core.pipeline import PipelineWorker
from .ocr.winrt_ocr import WinRtOcr
from .overlay.window import OverlayWindow
from .translation.registry import create_provider
from .ui.tray import TrayIcon, TrayStatus
from .ui.wizard import SetupWizard
from .utils import dpapi
from .utils.hotkey import HotkeyListener
from .utils.resources import resource_path

log = logging.getLogger(__name__)

_STATUS_MAP = {
    "active": TrayStatus.ACTIVE,
    "waiting": TrayStatus.WAITING,
    "error": TrayStatus.ERROR,
}


class _HotkeyBridge(QObject):
    """Re-emits hotkey events (fired on the listener thread) as Qt signals so the
    handlers run on the UI thread."""

    toggle = pyqtSignal()
    select_region = pyqtSignal()


class VNLensApp:
    def __init__(self) -> None:
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load()
        self._paused = False
        self._selector: RegionSelector | None = None

    def run(self) -> int:
        self._load_fonts()
        if not self._has_api_key() and not self._run_wizard():
            return 1

        provider = self._create_provider()
        self.overlay = OverlayWindow(self.config.overlay)
        self.tray = TrayIcon()
        self.tray.toggle_requested.connect(self._toggle_pause)
        self.tray.select_region_requested.connect(self._select_region)
        self.tray.quit_requested.connect(self._quit)
        self.tray.show()

        self.thread = QThread()
        self.worker = PipelineWorker(self.config, WinRtOcr(), provider)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.translated.connect(self.overlay.show_text)
        self.worker.cleared.connect(self.overlay.clear)
        self.worker.status.connect(self._on_status)

        self._setup_hotkeys()

        if self.config.capture.region is None:
            self._select_region()
        else:
            self._update_anchor(self.config.capture.region)

        self.thread.start()
        return self.app.exec()

    def _load_fonts(self) -> None:
        """Register the bundled overlay font; Windows does not ship Noto Sans."""
        font_path = resource_path("assets/fonts/NotoSans-Regular.ttf")
        if not font_path.exists() or QFontDatabase.addApplicationFont(str(font_path)) == -1:
            log.warning("Bundled Noto Sans not loaded; overlay falls back to a system font")

    def _has_api_key(self) -> bool:
        return self.config.translation.provider in self.config.translation.api_keys

    def _create_provider(self):
        provider_id = self.config.translation.provider
        encrypted = self.config.translation.api_keys[provider_id]
        return create_provider(provider_id, dpapi.decrypt(encrypted))

    def _run_wizard(self) -> bool:
        wizard = SetupWizard()
        if wizard.exec() != SetupWizard.DialogCode.Accepted:
            return False
        self.config.translation.provider = wizard.provider_id
        self.config.translation.api_keys[wizard.provider_id] = dpapi.encrypt(wizard.api_key)
        self.config_manager.save(self.config)
        return True

    def _setup_hotkeys(self) -> None:
        self._bridge = _HotkeyBridge()
        self._bridge.toggle.connect(self._toggle_pause)
        self._bridge.select_region.connect(self._select_region)
        self.hotkeys = HotkeyListener(
            {
                self.config.hotkeys.toggle: self._bridge.toggle.emit,
                self.config.hotkeys.select_region: self._bridge.select_region.emit,
            }
        )
        self.hotkeys.start()

    def _toggle_pause(self) -> None:
        self._paused = not self._paused
        self.worker.set_paused(self._paused)
        if self._paused:
            self.overlay.clear()
            self.tray.set_status(TrayStatus.PAUSED)
        else:
            self.tray.set_status(TrayStatus.ACTIVE)

    def _select_region(self) -> None:
        self._selector = RegionSelector()
        self._selector.selected.connect(self._on_region_selected)
        self._selector.showFullScreen()

    def _on_region_selected(self, region: Region) -> None:
        self.config.capture.region = region
        self.config_manager.save(self.config)
        self.worker.set_region(region)
        self._update_anchor(region)

    def _update_anchor(self, region: Region) -> None:
        screen = QGuiApplication.primaryScreen().geometry()
        self.overlay.set_anchor(region.to_pixels(screen.width(), screen.height()))

    def _on_status(self, status: str) -> None:
        if self._paused:
            return
        self.tray.set_status(_STATUS_MAP[status])

    def _quit(self) -> None:
        self.worker.stop()
        self.thread.quit()
        self.thread.wait(2000)
        self.hotkeys.stop()
        self.app.quit()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if sys.platform != "win32":
        log.warning("VNLens targets Windows; some features will not work on this platform.")
    return VNLensApp().run()


if __name__ == "__main__":
    sys.exit(main())
