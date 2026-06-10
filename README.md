# VNLens

Real-time screen translator overlay for visual novels and text-heavy games.

VNLens reads text from a chosen region of the screen, translates it, and shows the result in a click-through overlay — no need to leave the game. Windows only.

## Status

Early development. See the roadmap for what works today.

## Requirements

- Windows 10 / 11
- Python 3.11+

## Development

Uses [uv](https://docs.astral.sh/uv/) for dependency management.

```
uv sync
uv run vnlens
```

Run tests and linters:

```
uv run pytest
uv run ruff check
```

## Build

Build the single-file executable on Windows:

```
uv run python build.py
```

The result is `dist/VNLens.exe`.

## License

MIT
