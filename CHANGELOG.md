# Changelog

All notable changes to VNLens are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

## [0.1.0] - 2026-06-11

First public beta.

### Added

- Real-time translation pipeline: screen capture (mss) -> Windows OCR -> change detection (SHA-1 + debounce) -> DeepL.
- Click-through overlay anchored below the capture region, with smart flip above when there is no room and clamping to the screen.
- Move mode (F4): drag the overlay anywhere; position saved per screen fraction.
- Line structure preservation: mid-sentence wraps rejoined before translation, real breaks kept.
- First-run wizard: provider + API key + connection test.
- Settings dashboard: provider/API key, overlay style with live preview, OCR language, poll interval, hotkeys. Changes apply live.
- System tray with status colors and full menu.
- Global hotkeys (F2 pause, F3 select region, F4 move overlay).
- API keys encrypted with Windows DPAPI; translation retry with backoff; file logging.
- Bundled Noto Sans font for full Vietnamese diacritics.
- App logo: window/taskbar/exe icon, tray badge with status dot (green translating, yellow waiting, red error) and grayscale paused variant.
