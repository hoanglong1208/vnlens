from vnlens.utils.change_detect import ChangeDetector, text_hash


def test_emits_after_debounce():
    d = ChangeDetector(debounce_ms=300)
    assert d.update("hello", now_ms=0) is None
    assert d.update("hello", now_ms=200) is None
    assert d.update("hello", now_ms=300) == "hello"


def test_resets_debounce_on_change():
    d = ChangeDetector(debounce_ms=300)
    d.update("hel", now_ms=0)
    d.update("hell", now_ms=100)
    assert d.update("hello", now_ms=200) is None
    assert d.update("hello", now_ms=450) is None
    assert d.update("hello", now_ms=500) == "hello"


def test_same_text_emitted_once():
    d = ChangeDetector(debounce_ms=300)
    assert d.update("hello", now_ms=0) is None
    assert d.update("hello", now_ms=300) == "hello"
    assert d.update("hello", now_ms=600) is None


def test_reemits_after_returning_to_previous_text():
    d = ChangeDetector(debounce_ms=300)
    d.update("a", now_ms=0)
    assert d.update("a", now_ms=300) == "a"
    d.update("b", now_ms=400)
    assert d.update("b", now_ms=700) == "b"
    d.update("a", now_ms=800)
    assert d.update("a", now_ms=1100) == "a"


def test_blank_text_ignored():
    d = ChangeDetector(debounce_ms=300)
    assert d.update("   ", now_ms=0) is None
    assert d.update("", now_ms=300) is None


def test_text_is_stripped():
    d = ChangeDetector(debounce_ms=0)
    assert d.update("  hi  ", now_ms=0) is None
    assert d.update("  hi  ", now_ms=0) == "hi"


def test_text_hash_stable():
    assert text_hash("hello") == text_hash("hello")
    assert text_hash("hello") != text_hash("world")
