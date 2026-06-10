import asyncio

from PIL import Image
from winsdk.windows.globalization import Language
from winsdk.windows.graphics.imaging import (
    BitmapAlphaMode,
    BitmapPixelFormat,
    SoftwareBitmap,
)
from winsdk.windows.media.ocr import OcrEngine
from winsdk.windows.security.cryptography import CryptographicBuffer

from .base import BaseOCR

# Source language hint -> BCP-47 tag understood by WinRT.
_LANG_TAGS = {"en": "en-US", "ja": "ja"}


class WinRtOcr(BaseOCR):
    """Windows built-in OCR. No extra install, low memory, EN/JP language packs
    ship with Windows 10/11."""

    def recognize(self, image: Image.Image, lang: str) -> str:
        engine = self._engine_for(lang)
        if engine is None:
            return ""
        bitmap = self._to_software_bitmap(image)
        text = asyncio.run(self._recognize_async(engine, bitmap))
        if lang == "ja":
            # WinRT joins detected words with spaces, which is wrong for Japanese
            # and degrades translation input.
            text = text.replace(" ", "")
        return text

    @staticmethod
    def _engine_for(lang: str) -> OcrEngine | None:
        if lang == "auto":
            return OcrEngine.try_create_from_user_profile_languages()
        tag = _LANG_TAGS.get(lang, lang)
        return OcrEngine.try_create_from_language(Language(tag))

    @staticmethod
    def _to_software_bitmap(image: Image.Image) -> SoftwareBitmap:
        rgba = image.convert("RGBA")
        r, g, b, a = rgba.split()
        # WinRT expects BGRA8 byte order.
        bgra = Image.merge("RGBA", (b, g, r, a)).tobytes()
        buffer = CryptographicBuffer.create_from_byte_array(bgra)
        return SoftwareBitmap.create_copy_from_buffer(
            buffer,
            BitmapPixelFormat.BGRA8,
            rgba.width,
            rgba.height,
            BitmapAlphaMode.PREMULTIPLIED,
        )

    @staticmethod
    async def _recognize_async(engine: OcrEngine, bitmap: SoftwareBitmap) -> str:
        result = await engine.recognize_async(bitmap)
        return result.text or ""
