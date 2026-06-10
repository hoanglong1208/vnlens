from .base import TranslationProvider
from .deepl_provider import DeepLProvider

# Provider id -> implementation. New providers are registered here.
_PROVIDERS: dict[str, type[TranslationProvider]] = {
    DeepLProvider.id: DeepLProvider,
}


def available_providers() -> list[str]:
    return list(_PROVIDERS)


def create_provider(provider_id: str, api_key: str) -> TranslationProvider:
    try:
        provider_cls = _PROVIDERS[provider_id]
    except KeyError:
        raise ValueError(f"Unknown translation provider: {provider_id}") from None
    return provider_cls(api_key)
