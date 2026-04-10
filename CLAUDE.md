# Python Project — Claude Instructions

## Project Setup

### Virtual Environment
Always use `.venv` in the project root. Never use system Python.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
```

After any dependency change, run `pip install -e .` to keep the editable install current.

### Python Version
Target Python 3.12+. Set `python_version` in `pyproject.toml` to match.

---

## Type Annotations — mypy strict

This project runs **mypy in strict mode**. Every function, method, and variable must be fully annotated. No exceptions.

### Required annotations
- All function parameters and return types
- All class attributes (use `ClassVar` or instance annotations in `__init__`)
- Module-level variables
- Use `Final` for constants

### Forbidden patterns
- `# type: ignore` — fix the underlying issue instead
- `Any` unless truly unavoidable and documented with a comment
- Untyped third-party stubs without a `py.typed` marker or stub package (`types-*`)

### Running mypy
```bash
mypy src tests
```

Must return exit code 0 with zero errors before any commit.

### Common strict patterns

```python
from __future__ import annotations
from typing import Final, ClassVar
from collections.abc import Sequence, Mapping, Iterator, Callable

# Constants
MAX_RETRIES: Final = 3

# Class attributes
class Foo:
    count: ClassVar[int] = 0

    def __init__(self, name: str) -> None:
        self.name = name

# Optional fields
from typing import Optional   # or use X | None (Python 3.10+)
def find(key: str) -> str | None: ...

# Generics
def first(items: Sequence[int]) -> int: ...
```

---

## Code Conventions

- Formatter: **black** (line length 100)
- Import sorter: **isort** (profile = black)
- Linter: **ruff**
- All three run via pre-commit; do not disable hooks

### Project layout
```
src/
  <package>/
    __init__.py
    py.typed          # PEP 561 marker — required for mypy
tests/
  conftest.py
  test_<module>.py
```

Always use `src/` layout. Never import from `tests/` in `src/`.

---

## Testing

```bash
pytest tests/ --tb=short
```

Use `pytest` + `pytest-cov`. Aim for 80%+ coverage on `src/`.

---

## VSCode Integration

The `.vscode/` directory is committed and provides:
- Pylance in strict mode (real-time type errors)
- mypy extension for inline diagnostics
- Black + isort on save
- Debugger launch configs

If VSCode shows a "select interpreter" warning, point it to `.venv/bin/python`.

---

## Dependencies

Add runtime deps to `pyproject.toml` under `[project] dependencies`.
Add dev/test deps to `pyproject.toml` under `[project.optional-dependencies] dev`.

Regenerate pinned file after changes:
```bash
pip compile pyproject.toml --extra dev -o requirements-dev.txt
```
(requires `pip-tools`)
