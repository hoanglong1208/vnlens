import pytest
from pydantic import ValidationError

from vnlens.config.manager import ConfigManager
from vnlens.config.schema import AppConfig, Region


def test_defaults():
    config = AppConfig()
    assert config.translation.provider == "deepl"
    assert config.translation.target_lang == "vi"
    assert config.capture.interval_ms == 500
    assert config.ocr.engine == "winrt"


def test_region_to_pixels():
    region = Region(left=0.1, top=0.5, width=0.5, height=0.2)
    assert region.to_pixels(1920, 1080) == {
        "left": 192,
        "top": 540,
        "width": 960,
        "height": 216,
    }


def test_region_rejects_out_of_range():
    with pytest.raises(ValidationError):
        Region(left=1.5, top=0.0, width=0.5, height=0.5)


def test_interval_bounds():
    with pytest.raises(ValidationError):
        AppConfig(capture={"interval_ms": 100})


def test_roundtrip(tmp_path):
    manager = ConfigManager(path=tmp_path / "config.json")
    config = AppConfig()
    config.capture.region = Region(left=0.1, top=0.7, width=0.8, height=0.15)
    manager.save(config)

    loaded = manager.load()
    assert loaded.capture.region == config.capture.region
    assert loaded.translation.provider == "deepl"


def test_load_missing_returns_defaults(tmp_path):
    manager = ConfigManager(path=tmp_path / "missing.json")
    assert manager.load() == AppConfig()
