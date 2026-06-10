import logging
import os
import sys
from pathlib import Path

from pydantic import ValidationError

from .schema import AppConfig

log = logging.getLogger(__name__)

APP_NAME = "VNLens"
CONFIG_FILENAME = "config.json"


def config_dir() -> Path:
    """Per-user config directory. %APPDATA%\\VNLens on Windows, ~/.config/vnlens
    elsewhere (used only for development on Linux)."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
        root = Path(base) if base else Path.home() / "AppData" / "Roaming"
        return root / APP_NAME
    return Path.home() / ".config" / "vnlens"


class ConfigManager:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or config_dir() / CONFIG_FILENAME

    def load(self) -> AppConfig:
        """Load config, falling back to defaults if the file is missing or invalid."""
        if not self.path.exists():
            return AppConfig()
        try:
            return AppConfig.model_validate_json(self.path.read_text(encoding="utf-8"))
        except ValidationError:
            log.warning("Invalid config at %s, using defaults", self.path)
            return AppConfig()

    def save(self, config: AppConfig) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
