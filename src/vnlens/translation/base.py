from abc import ABC, abstractmethod


class TranslationError(Exception):
    """Raised when a provider fails to translate (network, quota, bad key)."""


class TranslationProvider(ABC):
    """A translation backend. `id` matches the provider key used in config."""

    id: str

    @abstractmethod
    async def translate(self, text: str, src: str, dst: str) -> str:
        """Translate `text` from `src` to `dst` language codes.

        `src` may be "auto". Raises TranslationError on failure."""

    def estimate_cost(self, char_count: int) -> float:
        """Estimated USD cost for translating `char_count` characters."""
        return 0.0
