.PHONY: install run dev test lint fmt build clean

install:
	uv sync

run:
	uv run sg

dev:
	uv run python scripts/dev.py

test:
	uv run pytest

lint:
	uv run ruff check .

fmt:
	uv run ruff format .

build:
	uv run pyinstaller packaging/sg.spec --noconfirm --clean

clean:
	rm -rf build dist *.egg-info
