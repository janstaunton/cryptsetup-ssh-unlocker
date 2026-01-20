.PHONY: install test lint format clean build

build:
	podman build -t ssh-unlocker .

install:
	uv sync --extra dev

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run pyright .

format:
	uv run ruff format .

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
