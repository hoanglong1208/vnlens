import hashlib


def text_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


class ChangeDetector:
    """Decides when OCR output is worth translating.

    Two jobs:
      - Skip text identical to what was last emitted (avoids redundant API calls).
      - Debounce: visual novels reveal text character by character, so wait until
        the text stays unchanged for `debounce_ms` before treating it as stable.

    Time is passed in explicitly to keep the logic testable.
    """

    def __init__(self, debounce_ms: int = 300) -> None:
        self.debounce_ms = debounce_ms
        self._pending: str | None = None
        self._pending_since: float = 0.0
        self._last_emitted_hash: str | None = None

    def update(self, text: str, now_ms: float) -> str | None:
        """Feed the latest OCR result. Returns the text when it has stabilized into
        a new value, otherwise None."""
        text = text.strip()
        if not text:
            self._pending = None
            return None

        if text != self._pending:
            self._pending = text
            self._pending_since = now_ms
            return None

        if now_ms - self._pending_since < self.debounce_ms:
            return None

        current_hash = text_hash(text)
        if current_hash == self._last_emitted_hash:
            return None

        self._last_emitted_hash = current_hash
        return text
