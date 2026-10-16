# Evolix AI

Desktop application written in Python (PySide6/Qt), buildable for **macOS** and **Windows**.

## Requirements

- [uv](https://docs.astral.sh/uv/) (environment & dependency management)
- [Make](https://www.gnu.org/software/make/) (optional, for shortcuts)

## Getting started

```bash
uv sync          # install the environment + dependencies
make run         # or: uv run evolix-ai
```

## Development

```bash
make test        # run tests (pytest + pytest-qt)
make lint        # check the code (ruff)
make fmt         # format the code (ruff)
```

## Features

- **Projects** — create, edit and delete projects, each opened in its own workspace.
- **AI providers** — manage OpenAI-compatible chat connections (base URL, API key, default model) with a connection test and model autocomplete.
- **Chat** — a simple chat form bound to a selected provider, plus an embedded browser.

## Build

Packaged with PyInstaller. Run it on the **target operating system** (PyInstaller does not cross-compile).

```bash
make build       # or: uv run pyinstaller packaging/evolix-ai.spec --noconfirm --clean
```

Output in `dist/`:

| Platform | Artifact |
| -------- | -------- |
| macOS    | `dist/Evolix AI.app` |
| Windows  | `dist/Evolix AI/Evolix AI.exe` |

> The app must be built on Windows to produce a `.exe`, and on macOS to produce a `.app`.

## CI/CD

GitHub Actions (`.github/workflows/build.yml`) builds in parallel on `macos-14` and
`windows-latest`, then uploads the artifacts. Pushing a `v*` tag attaches the zips to a Release.

```bash
git tag v0.1.0 && git push origin v0.1.0
```

## Structure

```
src/evolix_ai/       # main source
├── __main__.py      # entry point
├── db.py            # SQLite persistence (projects, providers, settings)
├── providers.py     # OpenAI-compatible chat client
└── ui/              # PySide6 interface
packaging/evolix-ai.spec  # PyInstaller config (macOS + Windows)
resources/           # icons, assets (put icon.icns / icon.ico here)
tests/               # pytest + pytest-qt
```

### Icon

Put the platform-specific icon in `resources/`:

- macOS: `resources/icon.icns`
- Windows: `resources/icon.ico`

`packaging/evolix-ai.spec` picks up the icon automatically when the file exists.
