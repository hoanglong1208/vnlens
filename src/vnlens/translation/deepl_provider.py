import asyncio

import deepl

from .base import TranslationError, TranslationProvider


class DeepLProvider(TranslationProvider):
    id = "deepl"

    # DeepL only returns Vietnamese on its next-generation models, so a model_type
    # must be requested explicitly.
    _MODEL_TYPE = "quality_optimized"

    def __init__(self, api_key: str) -> None:
        self._translator = deepl.Translator(api_key)

    async def translate(self, text: str, src: str, dst: str) -> str:
        return await asyncio.to_thread(self._translate_sync, text, src, dst)

    def _translate_sync(self, text: str, src: str, dst: str) -> str:
        try:
            result = self._translator.translate_text(
                text,
                source_lang=None if src == "auto" else src.upper(),
                target_lang=dst.upper(),
                model_type=self._MODEL_TYPE,
            )
        except deepl.DeepLException as exc:
            raise TranslationError(str(exc)) from exc
        return result.text
