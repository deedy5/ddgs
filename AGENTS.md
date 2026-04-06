# AGENTS.md — Guide for Coding Agents

## Project Overview

**ddgs** (Dux Distributed Global Search) is a Python metasearch library that aggregates results from diverse web search services. It provides a `DDGS` class with methods like `text()`, `images()`, `news()`, `videos()`, `books()`, and `extract()`.

- **Python**: >=3.10 (tested up to 3.14)
- **Dependencies**: `click`, `primp`, `lxml`
- **Package layout**: `ddgs/` (source), `tests/` (tests), optional extras: `api` (FastAPI), `mcp` (stdio)

## Build / Lint / Test Commands

```bash
# Setup (creates .venv, installs dev deps)
python3 -m venv .venv
.venv/bin/pip install -e .[dev]

# Lint (ruff check + mypy type-check)
.venv/bin/ruff check --fix
.venv/bin/mypy --install-types --non-interactive .

# Format
.venv/bin/ruff format

# Run all tests
.venv/bin/pytest

# Run a single test file
.venv/bin/pytest tests/ddgs_test.py

# Run a single test function
.venv/bin/pytest tests/ddgs_test.py::test_text_search

# Make targets (use .venv/bin/python internally)
make lint
make format
make test
```

**Important**: Tests make real HTTP requests and include a 2-second pause between tests (`autouse` fixture). Tests are slow by nature.

## Engine Architecture

Each search engine is a subclass of `BaseSearchEngine[T]` in `ddgs/engines/`. Key concepts:

- `ENGINES` dict in `ddgs/engines/__init__.py` maps category → {name → engine class}.
- `DDGS._search()` spawns threads via `ThreadPoolExecutor`, calling `engine.search()` in parallel.
- Results are deduplicated and ranked by `ResultsAggregator` and `SimpleFilterRanker`.
- `BaseSearchEngine` handles HTTP requests, HTML parsing (lxml), and XPath-based result extraction.
- Engine instances are cached per `DDGS` instance in `_engines_cache`.

## Pre-commit Hooks

Pre-commit is managed via `prek` (not `pre-commit`). Install with `prek install`. Hooks run on commit:

1. Standard checks (large files, AST, trailing whitespace, etc.)
2. `ruff check --fix`
3. `ruff format`
4. `mypy --install-types --non-interactive .`

Run all hooks manually: `prek`

## Code Style Guidelines

### Imports

- **Standard library** first, then **third-party**, then **local** (enforced by ruff `I` rules / isort).
- Use relative imports within the `ddgs` package (e.g., `from .base import BaseSearchEngine`).
- Do **not** use `from __future__ import annotations`; use Python 3.10+ union syntax directly: `str | None`.
- Guard type-only imports with `if TYPE_CHECKING:` to avoid runtime imports.

### Typing

- **mypy strict mode** is enabled. All functions must have full type annotations (parameters and return types).
- Use `ClassVar` for class-level attributes on classes.
- Use `Any` sparingly; prefer concrete types. Use `# noqa: ANN401` when `Any` is intentional.
- Use generics (`Generic[T]`) for result-type polymorphism (see `BaseSearchEngine[T]`).
- Union types: `str | None` (not `Optional[str]`), `bool | str` (not `Union[bool, str]`).
- Use `Literal` for constrained string values (e.g., `Literal["text", "images"]`).

### Naming

- **Classes**: PascalCase (e.g., `BaseSearchEngine`, `HttpClient`, `Duckduckgo`).
- **Functions/methods**: snake_case (e.g., `build_payload`, `extract_results`).
- **Constants**: UPPER_SNAKE_CASE (e.g., `ENGINES`).
- **Private**: prefix with `_` (e.g., `_search`, `_get_engines`, `_normalize_url`).
- **Test files**: `*_test.py` (not `test_*.py`).
- **Test functions**: `test_*` (e.g., `test_text_search`).

### Formatting

- **Line length**: 120 characters max (`ruff` setting).
- **Quotes**: double quotes preferred (ruff formatter default).
- **Trailing commas**: handled by formatter.
- **Docstrings**: Google style, required on all public classes/methods (`pydocstyle D` rules enabled). Exception: `D107` (missing `__init__` docstring) is ignored.

### Error Handling

- Raise custom exceptions from `ddgs/exceptions.py`: `DDGSException` (base), `RatelimitException`, `TimeoutException`.
- Pattern: define a local `msg` variable, then `raise SomeException(msg)`.
- Use `raise ... from ex` when re-raising to preserve exception chains.
- Use `logger.info()` / `logger.warning()` for non-fatal errors (not `print()`; ruff `T20` bans print).
- Bare `except` is forbidden; use `except Exception as ex:` with `# noqa: BLE001` if catching all.

### General Patterns

- Keyword-only args after `*` (e.g., `*, verify: bool | str = True`).
- Use `@classmethod` and `@staticmethod` where appropriate.
- Use `@dataclass` for result data structures (see `TextResult`, `ImagesResult`, etc.).
- Use `__slots__` for lightweight wrapper classes (see `Response`).
- Use `cached_property` for expensive lazy computations.
- Suppress ruff rules inline with `# noqa: RULE` when justified (document why implicitly by context).

### Adding a New Search Engine

1. Create `ddgs/engines/<engine_name>.py`.
2. Subclass `BaseSearchEngine[<ResultType>]`.
3. Set class variables: `name`, `category`, `provider`, `search_url`, `search_method`, `items_xpath`, `elements_xpath`.
4. Implement `build_payload()`.
5. Register in `ddgs/engines/__init__.py` under the correct category `ENGINES` dict.
6. Add integration tests in `tests/`.

### CLI

The CLI is built with Click (`ddgs/cli.py`). Entry point: `ddgs` command via `ddgs.cli:safe_entry_point`.

```bash
# Text search
.venv/bin/ddgs text -q "python" --max-results 5

# Images, news, videos, books
.venv/bin/ddgs images -q "cats"
.venv/bin/ddgs news -q "tech" --timelimit d

# Save results
.venv/bin/ddgs text -q "dogs" -o results.json --format json
.venv/bin/ddgs text -q "dogs" -o results.csv --format csv
```

### Adding Tests

- Test files live in `tests/` and are named `*_test.py`.
- Use `pytest` fixtures. The `pause_between_tests` autouse fixture adds a 2s delay between tests.
- Tests are integration tests that make real network calls — do not mock HTTP.
- Use `CliRunner` from Click for CLI tests.

### Things to Avoid

- Do not use `print()` — use `logging` instead (ruff `T20` bans print).
- Do not use `Optional[T]` — use `T | None`.
- Do not import `TYPE_CHECKING`-guarded modules at runtime.
- Do not add `.gitignore`-listed or generated files (`.mypy_cache/`, `build/`, `*.egg-info/`).
- Do not commit without running `make lint` and `make test` first.
- Do not skip the 2s test pause — it prevents rate-limiting from engines.
- Do not create `test_*` files — use `*_test.py` naming convention.

### Using ddgs as a Search Tool

If you need to search the web, extract URLs, or find images/news/videos/books,
see `skills/ddgs/SKILL.md` for Python API, CLI, and MCP integration guidance.
