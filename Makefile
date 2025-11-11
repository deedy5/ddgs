PY := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: help setup lint format test all clean

help:
	@echo "Targets:"
	@echo "  setup   - create venv and install dependencies"
	@echo "  lint    - run ruff check, ruff format and mypy"
	@echo "  format  - run ruff format and ruff check --fix"
	@echo "  test    - run pytest"
	@echo "  all     - run setup, lint, format and test"
	@echo "  clean   - remove cache, venv and build artifacts"

setup:
	python3 -m venv .venv
	$(PIP) install -e .[dev]

lint:
	$(PY) -m ruff check --fix
	$(PY) -m mypy --install-types --non-interactive .

format:
	$(PY) -m ruff format

test:
	$(PY) -m pytest

all: setup lint format test

clean:
	rm -rf .venv/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -name __pycache__ -exec rm -rf {} +
	rm -f uv.lock
