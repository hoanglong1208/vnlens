import asyncio
import logging
import time

from PyQt6.QtCore import QObject, pyqtSignal

from ..capture.screen import ScreenCapture
from ..config.schema import AppConfig, Region
from ..ocr.base import BaseOCR
from ..translation.base import TranslationError, TranslationProvider
from ..translation.retry import translate_with_retry
from ..utils.change_detect import ChangeDetector

log = logging.getLogger(__name__)


class PipelineWorker(QObject):
    """Runs the capture -> OCR -> change-detect -> translate loop on a background
    thread and reports results through Qt signals.

    `region` and `paused` are written from the UI thread; the GIL makes those
    single-attribute assignments safe enough for this use.
    """

    translated = pyqtSignal(str)
    cleared = pyqtSignal()
    status = pyqtSignal(str)  # "active" | "waiting" | "error"

    def __init__(self, config: AppConfig, ocr: BaseOCR, provider: TranslationProvider) -> None:
        super().__init__()
        self._config = config
        self._ocr = ocr
        self._provider = provider
        self._region: Region | None = config.capture.region
        self._paused = False
        self._running = True

    def set_region(self, region: Region) -> None:
        self._region = region

    def set_paused(self, paused: bool) -> None:
        self._paused = paused

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        capture = ScreenCapture()
        detector = ChangeDetector(debounce_ms=300)
        interval = self._config.capture.interval_ms / 1000
        source_lang = self._config.ocr.source_lang
        target_lang = self._config.translation.target_lang

        while self._running:
            region = self._region
            if self._paused or region is None:
                time.sleep(interval)
                continue

            try:
                stable = detector.update(
                    self._ocr.recognize(capture.grab(region), source_lang),
                    time.monotonic() * 1000,
                )
            except Exception:
                # A single bad frame must not kill the loop; report and keep polling.
                log.exception("Capture/OCR failed")
                self.status.emit("error")
                time.sleep(interval)
                continue

            if stable:
                self._translate(stable, source_lang, target_lang)
            elif stable == "":
                self.cleared.emit()
            time.sleep(interval)

        capture.close()

    def _translate(self, text: str, src: str, dst: str) -> None:
        self.status.emit("waiting")
        try:
            result = asyncio.run(translate_with_retry(self._provider, text, src, dst))
        except TranslationError as exc:
            log.warning("Translation failed: %s", exc)
            self.status.emit("error")
            return
        self.translated.emit(result)
        self.status.emit("active")
