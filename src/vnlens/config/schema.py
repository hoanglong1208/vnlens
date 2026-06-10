from typing import Literal

from pydantic import BaseModel, Field

Provider = Literal["deepl", "google", "claude", "libre"]
OcrEngine = Literal["winrt", "easyocr"]
PositionMode = Literal["anchored", "float"]


class Region(BaseModel):
    """Capture region stored as fractions of the screen (0..1) so it survives
    resolution and window-size changes."""

    left: float = Field(ge=0.0, le=1.0)
    top: float = Field(ge=0.0, le=1.0)
    width: float = Field(gt=0.0, le=1.0)
    height: float = Field(gt=0.0, le=1.0)

    def to_pixels(self, screen_width: int, screen_height: int) -> dict[str, int]:
        return {
            "left": round(self.left * screen_width),
            "top": round(self.top * screen_height),
            "width": round(self.width * screen_width),
            "height": round(self.height * screen_height),
        }


class CaptureConfig(BaseModel):
    interval_ms: int = Field(default=500, ge=300, le=1000)
    region: Region | None = None


class OcrConfig(BaseModel):
    engine: OcrEngine = "winrt"
    source_lang: str = "auto"
    preprocess: bool = True


class TranslationConfig(BaseModel):
    provider: Provider = "deepl"
    target_lang: str = "vi"
    # Provider id -> encrypted API key blob. Never stored in plaintext.
    api_keys: dict[str, str] = Field(default_factory=dict)


class OverlayConfig(BaseModel):
    position_mode: PositionMode = "anchored"
    font_size: int = Field(default=16, ge=12, le=24)
    opacity: float = Field(default=0.82, ge=0.0, le=0.95)
    text_color: str = "#eaeaea"
    shadow: bool = True


class HotkeyConfig(BaseModel):
    toggle: str = "f2"
    select_region: str = "f3"


class AppConfig(BaseModel):
    version: int = 1
    capture: CaptureConfig = Field(default_factory=CaptureConfig)
    ocr: OcrConfig = Field(default_factory=OcrConfig)
    translation: TranslationConfig = Field(default_factory=TranslationConfig)
    overlay: OverlayConfig = Field(default_factory=OverlayConfig)
    hotkeys: HotkeyConfig = Field(default_factory=HotkeyConfig)
