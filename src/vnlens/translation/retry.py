import asyncio
import logging

from .base import TranslationError, TranslationProvider

log = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
BASE_DELAY_S = 1.0


async def translate_with_retry(
    provider: TranslationProvider, text: str, src: str, dst: str
) -> str:
    """Call the provider with up to MAX_ATTEMPTS tries and exponential backoff
    (1s -> 2s -> 4s). Re-raises the last TranslationError when all attempts fail."""
    delay = BASE_DELAY_S
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return await provider.translate(text, src, dst)
        except TranslationError as exc:
            if attempt == MAX_ATTEMPTS:
                raise
            log.warning("Translate attempt %d failed (%s), retrying in %.0fs", attempt, exc, delay)
            await asyncio.sleep(delay)
            delay *= 2
    raise AssertionError("unreachable")
