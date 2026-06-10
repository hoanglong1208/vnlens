import asyncio

import pytest

from vnlens.translation import retry
from vnlens.translation.base import TranslationError, TranslationProvider


class FlakyProvider(TranslationProvider):
    id = "flaky"

    def __init__(self, fail_times: int) -> None:
        self.fail_times = fail_times
        self.calls = 0

    async def translate(self, text: str, src: str, dst: str) -> str:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise TranslationError("boom")
        return f"ok:{text}"


@pytest.fixture
def no_sleep(monkeypatch):
    delays: list[float] = []

    async def record(delay: float) -> None:
        delays.append(delay)

    monkeypatch.setattr(retry.asyncio, "sleep", record)
    return delays


def test_succeeds_first_try(no_sleep):
    provider = FlakyProvider(fail_times=0)
    result = asyncio.run(retry.translate_with_retry(provider, "hi", "en", "vi"))
    assert result == "ok:hi"
    assert provider.calls == 1
    assert no_sleep == []


def test_retries_with_backoff(no_sleep):
    provider = FlakyProvider(fail_times=2)
    result = asyncio.run(retry.translate_with_retry(provider, "hi", "en", "vi"))
    assert result == "ok:hi"
    assert provider.calls == 3
    assert no_sleep == [1.0, 2.0]


def test_raises_after_max_attempts(no_sleep):
    provider = FlakyProvider(fail_times=10)
    with pytest.raises(TranslationError):
        asyncio.run(retry.translate_with_retry(provider, "hi", "en", "vi"))
    assert provider.calls == retry.MAX_ATTEMPTS
