.PHONY: install run dev test lint fmt build clean

install:
	uv sync

run:
	uv run evolix-ai

dev:
	uv run python scripts/dev.py

test:
	uv run pytest

lint:
	uv run ruff check .

fmt:
	uv run ruff format .

build:
	uv run pyinstaller packaging/evolix-ai.spec --noconfirm --clean

clean:
	rm -rf build dist *.egg-info
