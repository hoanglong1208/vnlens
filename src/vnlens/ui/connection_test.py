import asyncio

from ..translation.base import TranslationError
from ..translation.registry import create_provider

SAMPLE_TEXT = "The cherry blossoms are in full bloom."


def run_connection_test(provider_id: str, api_key: str) -> tuple[bool, str]:
    """Translate a sample sentence with the given credentials.

    Returns (True, translation) on success, (False, error message) otherwise.
    Blocking; callers on the UI thread should defer it past the next paint."""
    try:
        provider = create_provider(provider_id, api_key)
        translated = asyncio.run(provider.translate(SAMPLE_TEXT, "en", "vi"))
    except (TranslationError, ValueError) as exc:
        return False, str(exc)
    return True, translated
