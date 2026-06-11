"""Build the single-file Windows executable. Run on Windows: `uv run python build.py`."""

import os

import PyInstaller.__main__

PyInstaller.__main__.run(
    [
        "launcher.py",
        "--paths=src",
        "--name=VNLens",
        "--onefile",
        "--windowed",
        # winsdk loads its WinRT submodules dynamically.
        "--collect-submodules=winsdk",
        "--icon=assets/icons/icon.ico",
        f"--add-data=assets{os.pathsep}assets",
        "--noconfirm",
        "--clean",
    ]
)
