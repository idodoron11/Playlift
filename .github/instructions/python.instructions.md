---
applyTo: "**/*.py"
---

# Python Coding Instructions

General rules for writing clean, idiomatic, high-quality Python 3.11+ code.

## Language Version & Tooling

- Target **Python 3.11+**. Use modern language features; do not add compatibility shims for older versions.
- Format with **ruff format** and lint with **ruff check**. Do not introduce style violations.
- Type-check with **mypy** in strict mode. All code must pass without errors.

## Type Hints

- Add type hints to **every** function and method signature — parameters and return types.
- Use **built-in generic types** (`list[str]`, `dict[str, int]`, `tuple[int, ...]`) instead of `typing.List`, `typing.Dict`, etc.
- Use `X | Y` union syntax instead of `typing.Union[X, Y]`.
- Use `X | None` instead of `typing.Optional[X]`.
- Import from `typing` only what is unavailable as a built-in: `TypeVar`, `Protocol`, `TypeAlias`, `overload`, `Final`, `Literal`, `TYPE_CHECKING`, etc.
- Use `typing.TYPE_CHECKING` guards for imports needed only at type-check time to avoid circular imports.
- Annotate class attributes and instance variables; use `ClassVar` for class-level constants when appropriate.
- Prefer `TypeAlias` for complex type expressions that are reused.

```python
# Good
def find(items: list[str], query: str) -> str | None: ...

# Bad
from typing import List, Optional
def find(items: List[str], query: str) -> Optional[str]: ...
```

## Docstrings

- Add a docstring to **every public module, class, method, and function** (anything not prefixed with `_`).
- Follow **PEP 257** conventions:
  - One-line docstrings for simple, obvious functions — fit on a single line with no blank lines.
  - Multi-line docstrings: summary line, blank line, then elaboration.
  - Closing `"""` on its own line for multi-line docstrings.
- Use **Google-style** sections for parameters, return values, and exceptions:

```python
def fetch_track(track_id: str, market: str = "US") -> Track:
    """Fetch a single track from the Spotify catalog.

    Args:
        track_id: The Spotify track ID (22-character base-62 string).
        market: An ISO 3166-1 alpha-2 country code for content availability.

    Returns:
        A fully populated Track object.

    Raises:
        TrackNotFoundError: If no track with the given ID exists.
        SpotifyAPIError: If the API request fails.
    """
```

- Do **not** add docstrings to private helpers (`_foo`), dunder methods, or trivial one-liners where the signature is self-documenting.

## Naming

- Follow PEP 8: `snake_case` for functions, methods, variables, and modules; `PascalCase` for classes; `UPPER_SNAKE_CASE` for module-level constants.
- Private attributes/methods: single leading underscore `_name`.  Never use double underscores unless intentionally triggering name mangling.
- Use descriptive names; avoid single-letter variables except in short list comprehensions or math contexts.
- Predicate functions (returning `bool`) should read as questions: `is_valid`, `has_match`, `can_retry`.

## Imports

- Group imports in this order, separated by a blank line:
  1. Standard library
  2. Third-party packages
  3. Local application modules
- Use absolute imports. Avoid relative imports except inside packages where they reduce verbosity.
- Never use wildcard imports (`from module import *`).
- Import only what is used; remove unused imports.

## Code Structure & Design

- Keep functions short and focused on a **single responsibility**. If a function needs more than ~30 lines, consider splitting it.
- Prefer **composition over inheritance**. Use classes to group related data and behavior, but avoid deep inheritance hierarchies.
- Avoid mutable default arguments; use `None` as default and assign inside the function body.
- Use dataclasses (`@dataclass`) or named tuples for plain data-carrying classes instead of ad-hoc dicts.
- Raise specific, meaningful exceptions. Define custom exception classes for domain errors rather than raising bare `Exception`.
- Use context managers (`with`) for resource management (files, locks, connections).

## Modern Python Features

- Use **f-strings** for string formatting. Avoid `%`-formatting and `.format()`.
- Use **structural pattern matching** (`match`/`case`) for complex conditional dispatch when it improves clarity.
- Use **walrus operator** (`:=`) sparingly — only when it meaningfully reduces repetition.
- Prefer `pathlib.Path` over `os.path` for filesystem operations.
- Use `enum.Enum` (or `enum.StrEnum`) for sets of named constants instead of plain string/int literals.

## Comprehensions & Iteration

- Prefer list/dict/set comprehensions over `map`/`filter` with `lambda` when the expression is simple.
- Use generators for large sequences to avoid unnecessary memory allocation.
- Never use a comprehension solely for its side effects — use a `for` loop instead.

## Error Handling

- Catch the **most specific** exception type possible. Never silence exceptions with a bare `except:` or `except Exception: pass`.
- Use `logging` for unexpected or non-fatal errors; do not print stack traces to stdout in library code.
- Always clean up resources in `finally` blocks or via context managers; do not rely on reference counting.

## Testing

- Write tests for every public function. Aim for branch coverage of meaningful logic paths.
- Name tests descriptively: `test_<unit>_<scenario>_<expected_outcome>`.
- Keep tests independent — no shared mutable state between test cases.
- Use fakes/stubs/mocks to isolate the unit under test from external dependencies (filesystem, network, DB).
- Assert on observable behaviour and return values, not on internal implementation details.
