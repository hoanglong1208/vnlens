import logging
import sys

from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtGui import QFontDatabase, QGuiApplication, QIcon
from PyQt6.QtWidgets import QApplication

from .capture.region_selector import RegionSelector
from .config.manager import ConfigManager, config_dir
from .config.schema import AppConfig, FloatPosition, Region
from .core.pipeline import PipelineWorker
from .ocr.winrt_ocr import WinRtOcr
from .overlay.window import OverlayWindow
from .translation.base import TranslationProvider
from .translation.registry import create_provider
from .ui import theme
from .ui.settings import SettingsDialog
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
    move_overlay = pyqtSignal()


class VNLensApp:
    def __init__(self) -> None:
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setStyleSheet(theme.QSS)
        self.app.setWindowIcon(QIcon(str(resource_path("assets/icons/icon.ico"))))
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load()
        self._paused = False
        self._selector: RegionSelector | None = None

    def run(self) -> int:
        self._load_fonts()
        provider = self._ensure_provider()
        if provider is None:
            return 1

        self.overlay = OverlayWindow(self.config.overlay)
        self.tray = TrayIcon()
        self.tray.toggle_requested.connect(self._toggle_pause)
        self.tray.select_region_requested.connect(self._select_region)
        self.tray.settings_requested.connect(self._open_settings)
        self.tray.move_overlay_toggled.connect(self.overlay.set_move_mode)
        self.tray.reset_position_requested.connect(self._reset_overlay_position)
        self.tray.quit_requested.connect(self._quit)
        self.tray.show()
        self.overlay.moved.connect(self._on_overlay_moved)

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

    def _ensure_provider(self) -> TranslationProvider | None:
        """Build the configured provider, rerunning setup when the stored key is
        unusable (DPAPI keys do not survive a copy to another Windows account)."""
        if self._has_api_key():
            try:
                return self._create_provider()
            except OSError:
                log.warning("Stored API key cannot be decrypted; rerunning setup")
        if not self._run_wizard():
            return None
        return self._create_provider()

    def _create_provider(self) -> TranslationProvider:
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
        self._bridge.move_overlay.connect(self.tray.toggle_move_mode)
        self.hotkeys = HotkeyListener(
            {
                self.config.hotkeys.toggle: self._bridge.toggle.emit,
                self.config.hotkeys.select_region: self._bridge.select_region.emit,
                self.config.hotkeys.move_overlay: self._bridge.move_overlay.emit,
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
        # Anchor first: set_region starts the pipeline producing translations.
        self._update_anchor(region)
        self.worker.set_region(region)

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self.config)
        dialog.saved.connect(self._apply_settings)
        dialog.exec()

    def _apply_settings(self, new_config: AppConfig) -> None:
        old = self.config
        self.config = new_config
        self.config_manager.save(new_config)

        self.overlay.apply_config(new_config.overlay)
        self.worker.update_config(new_config)

        translation_changed = (
            new_config.translation.provider != old.translation.provider
            or new_config.translation.api_keys != old.translation.api_keys
        )
        if translation_changed:
            try:
                self.worker.set_provider(self._create_provider())
            except OSError:
                log.warning("Could not load the new API key; keeping the old provider")

        if new_config.hotkeys != old.hotkeys:
            self.hotkeys.stop()
            self._setup_hotkeys()

    def _on_overlay_moved(self, x: float, y: float) -> None:
        self.config.overlay.position_mode = "float"
        self.config.overlay.float_pos = FloatPosition(x=x, y=y)
        self.config_manager.save(self.config)

    def _reset_overlay_position(self) -> None:
        self.config.overlay.position_mode = "anchored"
        self.config.overlay.float_pos = None
        self.config_manager.save(self.config)
        self.tray.set_move_checked(False)
        self.overlay.set_position_mode("anchored", None)

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
        # The worker may be mid-retry (up to ~7s of backoff); destroying a live
        # QThread crashes, so force-stop it if graceful shutdown times out.
        if not self.thread.wait(3000):
            self.thread.terminate()
            self.thread.wait(1000)
        self.hotkeys.stop()
        self.app.quit()


def _setup_logging() -> None:
    """Log to a file in the config dir; a windowed .exe has no console."""
    handlers: list[logging.Handler] = []
    log_path = config_dir() / "vnlens.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handlers.append(logging.FileHandler(log_path, encoding="utf-8"))
    if sys.stderr is not None:
        handlers.append(logging.StreamHandler())
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=handlers,
    )


def main() -> int:
    # CI runs the frozen exe with --smoke to verify the bundle imports cleanly;
    # reaching this point means every module resolved.
    if "--smoke" in sys.argv:
        return 0
    _setup_logging()
    if sys.platform != "win32":
        log.warning("VNLens targets Windows; some features will not work on this platform.")
    return VNLensApp().run()


if __name__ == "__main__":
    sys.exit(main())
