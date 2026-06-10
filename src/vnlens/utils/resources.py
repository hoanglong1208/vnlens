import sys
from pathlib import Path


def resource_path(relative: str) -> Path:
    """Resolve a bundled resource both in development (repo root) and inside a
    PyInstaller onefile bundle (sys._MEIPASS extraction dir)."""
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root is not None:
        return Path(bundle_root) / relative
    return Path(__file__).resolve().parents[3] / relative
