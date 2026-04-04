<!--
Sync Impact Report
==================
Version Change: (none) → 1.0.0 — initial ratification
Modified Principles: none (new constitution)
Added Sections:
  - Core Principles I–VI (new)
  - Quality Standards (new)
  - Development Workflow (new)
  - Governance (new)
Removed Sections: none
Templates Updated:
  - .specify/templates/plan-template.md ✅ (Constitution Check gates populated)
  - .specify/templates/tasks-template.md ✅ (tests changed from OPTIONAL to REQUIRED)
  - .specify/templates/spec-template.md ✅ (no structural changes required)
  - .specify/templates/checklist-template.md ✅ (no structural changes required)
Deferred Items: none
-->

# Playlist Sync Constitution

## Core Principles

### I. Clean Code & Self-Explanatory Design (NON-NEGOTIABLE)

Code MUST be written for the reader, not the author. Every identifier, function, and module
MUST communicate its intent without requiring inline explanation.

- Names MUST be precise and descriptive: `user_email` over `data`, `retry_count` over `n`
- Boolean identifiers MUST use `is_`, `has_`, `can_`, `should_` prefixes
- Functions MUST do exactly one thing and stay under ~30 lines
- Magic literals are PROHIBITED — use named constants at module scope (`UPPER_SNAKE_CASE`)
- Comments MUST explain *why*, never *what* (code explains what; comments explain non-obvious
  domain constraints or trade-offs)
- Nesting deeper than 3 levels MUST be refactored via guard clauses or extracted helpers
- Module names like `utils.py` or `helpers.py` are PROHIBITED — be specific about ownership

**Rationale**: Playlist Sync is a long-lived utility. Code that speaks for itself reduces
maintenance cost and onboarding time. Fuzzy matching and ID3 metadata handling are subtle
enough that readable code is the primary guard against silent bugs.

### II. SOLID Design Principles (NON-NEGOTIABLE)

All classes and modules MUST adhere to SOLID:

- **S** — Each class/module has exactly one reason to change (Single Responsibility).
  A class that both matches tracks AND persists metadata violates this principle.
- **O** — New behavior MUST be added by extension, not modification. Prefer polymorphism
  over `if/elif` chains keyed on type or source.
- **L** — Subclasses MUST behave correctly wherever the base type is expected. Overriding
  a method to raise `NotImplementedError` signals a broken abstraction — split the interface.
- **I** — Abstract bases MUST be small and focused. Clients MUST NOT be forced to depend on
  methods they do not use (e.g., Spotify-specific methods MUST NOT appear on the base `Track`).
- **D** — High-level modules depend on abstractions (`Track`, `Matcher`, `Playlist`), not
  concrete classes. Dependencies MUST be injected, never instantiated inside business logic.

**Rationale**: The layered architecture (CLI → Playlists → Matching → Tracks → API) depends on
stable abstractions. SOLID violations create cross-layer coupling that breaks testability and
makes adding new music sources or matchers unnecessarily invasive.

### III. DRY — No Duplication

Every piece of knowledge MUST have a single, authoritative representation in the codebase.

- Logic that appears in two places MUST be extracted into a named, well-tested function.
  The rule of three applies: tolerate duplication once; extract on the second recurrence.
- Configuration values, thresholds, and external constants belong in `config/` or module-level
  constants — they MUST NOT be repeated inline across multiple modules.
- Copy-pasted `if/elif` blocks keyed on type or source MUST be replaced with data-driven
  dispatch or polymorphism.

**Rationale**: Fuzzy-matching logic and ID3 metadata handling are central to every sync
operation. Duplicating them produces silent divergence when one copy is updated and the other
is not.

### IV. Readability First; Performance as Justified Exception

MUST prefer clear, idiomatic code over micro-optimized code.

- When readability and performance conflict, readability MUST win — unless the performance
  cost is **demonstrably significant** (i.e., measured via profiling, not assumed).
- Performance optimizations MUST be accompanied by a comment citing the measured bottleneck
  and the magnitude of improvement.
- Generators, `functools.lru_cache`, and pagination MUST be used for provably large data
  paths (e.g., iterating full local music libraries or repeated Spotify API calls).
- Premature optimization is PROHIBITED — write clear code first; profile before tuning.

**Rationale**: The primary user is a single operator syncing playlists manually.
Correctness and legibility are higher-value than sub-millisecond gains. Performance
investment MUST be proportional to measured impact.

### V. Mandatory Unit Testing (NON-NEGOTIABLE)

Every concrete class MUST have unit tests covering its core logic and responsibilities.

- **Core logic**: primary responsibilities of the class under normal conditions
- **Edge cases**: empty inputs, boundary values, missing or malformed metadata, non-Latin
  characters (Cyrillic, CJK), the `"SKIP"` sentinel, and `None` vs. set `spotify_ref`
- **Regression coverage**: every bug fix MUST be accompanied by a failing test that would
  have caught the original defect before the fix is applied
- **Isolation**: tests MUST NOT depend on the filesystem, network, Spotify API, or any
  external state — use fakes (`FakeLocalTrack`, `FakeSpotifyTrack`), stubs, or mocks
- **Naming**: MUST follow `test_<unit>_<scenario>_<expected_outcome>` convention
- **Structure**: Arrange-Act-Assert (AAA) pattern is REQUIRED in every test

**Rationale**: Matching correctness is mission-critical. A false match corrupts playlist
data silently. Tests are the only automated guard against regressions in fuzzy matching
logic, ID3 persistence, and the `SKIP`/`None` sentinel semantics.

### VI. Type Safety & Complete Type Hints (NON-NEGOTIABLE)

All public functions, methods, and class attributes MUST carry explicit type hints.

- Use built-in generic syntax: `list[str]`, `dict[str, int]`, `X | None`.
  `typing.Optional`, `typing.List`, `typing.Dict` are PROHIBITED.
- Code MUST pass `mypy` in strict mode with zero errors and zero suppressions.
- Custom domain exception classes MUST be defined for each distinct failure mode.
  Bare `raise Exception(...)` is PROHIBITED.
- All public modules, classes, methods, and functions MUST have Google-style docstrings.
  Private helpers (`_foo`) and trivial one-liners are exempt.

**Rationale**: Python's dynamic nature makes type drift a real risk in a multi-layer codebase.
Strict typing is the automated equivalent of a contract test at every function boundary and
the primary mechanism for catching API misuse before runtime.

## Quality Standards

Non-negotiable tooling and style gates that EVERY commit MUST pass before merge.

- **Language**: Python ≥ 3.11; no compatibility shims for older versions
- **Dependency management**: `uv` — do not invoke `pip` directly
- **Formatting**: `uv run ruff format .` — zero style violations permitted
- **Linting**: `uv run ruff check .` — zero lint violations permitted
- **Type checking**: `uv run mypy .` — strict mode, zero errors
- **Testing**: `uv run pytest tests/` — all tests MUST pass; skipped tests MUST carry a
  documented justification comment
- **Line length**: 120 characters (as configured in `pyproject.toml`)
- **Docstrings**: Google-style for all public symbols; private helpers exempt
- **Naming**: `snake_case` for functions/variables/modules; `PascalCase` for classes;
  `UPPER_SNAKE_CASE` for constants; single leading underscore `_name` for private members

## Development Workflow

- Constitution Check MUST be performed at the plan phase and again immediately before merge.
- All new classes and public functions MUST have tests before the feature is considered done.
- Regression bugs MUST have a failing test added **before** the fix is implemented.
- Non-Latin track handling (Cyrillic, CJK) MUST be manually verified for matching accuracy
  when changes touch `SpotifyMatcher` or normalization logic.
- Singletons (`SpotifyAPI`, `Matcher`, `CONFIG`) MUST only be used at boundary layers
  (CLI entry points). Domain logic MUST receive all dependencies via injection.
- The `"SKIP"` sentinel and `None` distinction in `LocalTrack.spotify_ref` are core domain
  invariants. Code that conflates them is a critical bug and MUST be caught by tests.
- `PathMapper` is one-directional (local path → mapped path); code MUST NOT assume a reverse
  mapping exists.

## Governance

This constitution supersedes all other project practices. Where a conflict exists between
this document and any other guideline, the constitution wins.

**Amendment procedure**: Any change to this document MUST:
1. Increment the version according to the policy below.
2. Update the Sync Impact Report (HTML comment at file top) with a summary of changes.
3. Be committed with a message of the form: `docs: amend constitution to vX.Y.Z (<summary>)`.
4. Be propagated to any dependent template that references changed principles.

**Version policy**:
- MAJOR: backward-incompatible removal or redefinition of an existing principle
- MINOR: new principle or section added, or materially expanded guidance
- PATCH: clarifications, wording fixes, non-semantic refinements

**Compliance review**: The Constitution Check section in `plan-template.md` MUST be verified
at plan phase and before merge. All violations MUST be documented in `Complexity Tracking`
with an explicit justification before work proceeds.

**Version**: 1.0.0 | **Ratified**: 2026-04-04 | **Last Amended**: 2026-04-04
