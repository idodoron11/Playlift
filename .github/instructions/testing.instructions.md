---
description: "Use when writing, reviewing, or generating Python tests. Covers pytest patterns, fixtures, mocking strategy, meaningful test design, unhappy-path assertions, and general test quality."
applyTo: "tests/**/*.py"
---

# Python Testing Instructions

Guidelines for writing high-quality, maintainable pytest tests for Python 3.11+.
Apply together with `python.instructions.md` and `clean-code.instructions.md`.

---

## Framework

- Use **pytest** as the sole testing framework. Do not use `unittest.TestCase` for new tests.
- Prefer plain functions with fixtures over class-based test suites.
- Use class grouping only to logically cluster related test cases (e.g., `TestFoo`), not for shared setup (use fixtures for that).

---

## Naming

- Test functions: `test_<unit>_<scenario>_<expected_outcome>`
  - `test_match_when_no_results_returns_none`
  - `test_sync_track_when_already_matched_skips_api_call`
- Fixture names: snake_case nouns describing what they provide (`local_track`, `mock_matcher`, `spotify_playlist`).
- Test doubles: append `Mock`, `Spy`, `Fake`, or `Stub` suffixes to make the role explicit (`matcher_mock`, `SpotifyPlaylistSpy`, `FakeLocalTrack`).

---

## Every Class Gets Unit Tests

- Every public class must have a corresponding unit test module under `tests/` mirroring the source layout (e.g., `tracks/local_track.py` → `tests/tracks/test_local_track.py`).
- Unit tests focus on a **single component in isolation**. All external collaborators (API clients, file I/O, other domain classes) must be replaced with test doubles.
- Each significant public method or property should have at least one test for the happy path and one for each meaningful edge/failure case.

---

## Fixtures

Prefer fixtures for setup that is reused across multiple tests or that would otherwise clutter the test body.

```python
# ✅ Good: shared fixture, injected cleanly
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_spotify_api() -> MagicMock:
    api = MagicMock()
    api.search.return_value = {"tracks": {"items": []}}
    return api

@pytest.fixture
def matcher(mock_spotify_api: MagicMock) -> SpotifyMatcher:
    return SpotifyMatcher(api=mock_spotify_api)

def test_match_when_no_results_returns_none(matcher: SpotifyMatcher) -> None:
    result = matcher.match("Artist", "Title")
    assert result is None
```

- Co-locate fixtures with the tests that use them, or put shared fixtures in `conftest.py`.
- Fixtures should return fully constructed objects — avoid building objects inline in every test.
- Scope fixtures appropriately: default to `function` scope; use `module` or `session` only for expensive, truly read-only resources.

---

## Mocking Strategy

### Prefer constructor / method injection

Pass mocks directly through the constructor or a method parameter. This is the cleanest and most explicit form of dependency injection.

```python
# ✅ Good: inject via constructor
def test_match_calls_api_with_correct_query(mock_spotify_api: MagicMock) -> None:
    matcher = SpotifyMatcher(api=mock_spotify_api)
    matcher.match("Muse", "Unintended")
    mock_spotify_api.search.assert_called_once()
```

### Fall back to `patch` / `monkeypatch` only when injection is unavailable

When a dependency is accessed via a global, singleton, or internal attribute that cannot be injected, use `unittest.mock.patch` or pytest's `monkeypatch`.

```python
# ✅ Acceptable fallback: patch a singleton
from unittest.mock import patch

def test_sync_uses_global_api(track: LocalTrack) -> None:
    with patch("matchers.spotify_matcher.SpotifyAPI.get_instance") as mock_get:
        mock_get.return_value.search.return_value = {"tracks": {"items": []}}
        result = sync(track)
    assert result is None
```

- Prefer `patch.object` over `patch` with a string path when possible — it's refactor-safe.
- Always patch at the point of **use**, not the point of definition.
- Never patch internals of the unit under test; only patch its dependencies.

---

## Write Meaningful Tests

Tests should verify **behaviour**, not configuration.

### Avoid tests that assert on literal configurable values

```python
# ❌ Bad: asserts a threshold constant — will break if the constant is tuned
def test_autopilot_threshold() -> None:
    assert matcher.AUTOPILOT_THRESHOLD == 0.85

# ✅ Good: asserts the behaviour the threshold controls
def test_autopilot_accepts_high_confidence_match(matcher: SpotifyMatcher) -> None:
    track = FakeLocalTrack(title="Unintended", artist="Muse")
    mock_spotify_api.search.return_value = high_confidence_response()
    result = matcher.auto_match(track)
    assert result is not None

def test_autopilot_rejects_low_confidence_match(matcher: SpotifyMatcher) -> None:
    track = FakeLocalTrack(title="Unintended", artist="Muse")
    mock_spotify_api.search.return_value = low_confidence_response()
    result = matcher.auto_match(track)
    assert result is None
```

### Focus on observable outcomes

- Assert on **return values, state changes, and side effects** visible through the public API.
- Do not assert on private attributes or implementation details.
- Prefer `assert result == expected` over a chain of `assert result.field_a == x; assert result.field_b == y` when equality is the right check.

---

## Unhappy Paths

Use **dedicated exception types**, not string inspection of error messages.

```python
# ❌ Bad: brittle string comparison — breaks on any message wording change
def test_invalid_track_id_raises() -> None:
    with pytest.raises(ValueError, match="Track ID must be"):
        SpotifyTrack("")

# ✅ Good: assert the exception type; message is irrelevant to callers
def test_invalid_track_id_raises() -> None:
    with pytest.raises(ValueError):
        SpotifyTrack("")

# ✅ Best: use a domain-specific exception when one exists
from exceptions import InvalidTrackError

def test_invalid_track_id_raises_domain_exception() -> None:
    with pytest.raises(InvalidTrackError):
        SpotifyTrack("")
```

- Define custom exception classes in `exceptions.py` for domain errors; tests should catch those, not `Exception`.
- Cover at least: missing input, invalid input, and downstream failures (e.g., API error) for any function with error paths.

---

## Logging Assertions

Avoid asserting on specific log messages. Log output is internal; it's not part of the public contract.

```python
# ❌ Bad: asserts on private log wording
def test_no_match_logs_warning(caplog) -> None:
    with caplog.at_level(logging.WARNING):
        matcher.match("Unknown", "Track")
    assert "No results found" in caplog.text

# ✅ Good: assert on the returned value instead
def test_no_match_returns_none() -> None:
    result = matcher.match("Unknown", "Track")
    assert result is None
```

If observable behaviour truly cannot be asserted without logs (e.g., a fire-and-forget side effect with no return value), use `caplog`:

```python
import logging
import pytest

def test_non_latin_artist_logs_warning(matcher: SpotifyMatcher, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING, logger="matchers.spotify_matcher"):
        matcher.match("Кино", "Группа крови")
    assert caplog.records  # at least one warning was emitted
```

Use `caplog.records` (list of `LogRecord`) rather than `caplog.text` (string) to avoid brittle substring matching.

---

## Arrange–Act–Assert

Structure every test body with three distinct phases, separated by a blank line:

```python
def test_compare_playlists_returns_tracks_only_in_local(
    local_playlist: FakeLocalPlaylist,
    spotify_playlist: FakeSpotifyPlaylist,
) -> None:
    # Arrange
    local_playlist.add_track(FakeLocalTrack(spotify_ref="S1"))
    spotify_playlist.add_track(FakeSpotifyTrack(track_id="S2"))

    # Act
    local_only, spotify_only = compare_playlists(local_playlist, spotify_playlist)

    # Assert
    assert len(local_only) == 0
    assert len(spotify_only) == 1
    assert spotify_only[0].track_id == "S2"
```

- One logical assertion per test whenever possible; use multiple only when asserting facets of the same result.
- Each test must be fully independent — no shared mutable state, no ordering dependencies.

---

## Test Doubles

| Double | When to use |
|--------|-------------|
| `MagicMock` / `Mock` | Mocking external collaborators where call assertions matter |
| `Fake*` class | Lightweight stand-in where a real implementation is too heavy (e.g., `FakeLocalTrack`) |
| `*Spy` class | Wraps a real object to capture method calls while preserving behaviour |
| `Stub` | Returns fixed data; no call assertions needed |

Prefer hand-written `Fake*` classes over `MagicMock` when the double needs to implement a meaningful interface (e.g., a `Track` subclass). `MagicMock` silently accepts any attribute access, making tests less reliable.

```python
# ✅ Good: typed fake — access to undefined attrs raises AttributeError
class FakeLocalTrack:
    def __init__(self, spotify_ref: str | None = None, title: str = "Title") -> None:
        self._spotify_ref = spotify_ref
        self._title = title

    @property
    def spotify_ref(self) -> str | None:
        return self._spotify_ref

    @property
    def title(self) -> str:
        return self._title
```

---

## Parametrize for Equivalence Classes

Use `pytest.mark.parametrize` when the same behaviour holds across multiple inputs of the same equivalence class. Do not copy-paste a test body for minor input variations.

```python
@pytest.mark.parametrize("isrc", [
    "USRC17607839",
    "usrc17607839",       # lowercase
    "US-RC1-76-07839",    # with hyphens
])
def test_normalize_isrc_returns_canonical_form(isrc: str) -> None:
    assert _normalize_isrc(isrc) == "USRC17607839"
```

Do **not** parametrize tests that cover qualitatively different behaviours — write separate tests with descriptive names instead.

---

## No Magic Strings or Numbers

Never use unexplained literal strings or numbers inline in tests. Use a named variable within the test, or a module-level constant when the value is shared across multiple tests.

```python
# ❌ Bad: magic IDs and strings scattered across tests
def test_isrc_returns_value() -> None:
    track = _make_spotify_track({"id": "abc123", "external_ids": {"isrc": "USRC17607839"}, ...})
    assert track.isrc == "USRC17607839"

def test_isrc_is_normalized() -> None:
    track = _make_spotify_track({"id": "abc123", "external_ids": {"isrc": "usrc17607839"}, ...})
    assert track.isrc == "USRC17607839"


# ✅ Good: shared constants for values used in multiple tests
TRACK_ID = "abc123"
CANONICAL_ISRC = "USRC17607839"

def test_isrc_returns_value() -> None:
    track = _make_spotify_track({"id": TRACK_ID, "external_ids": {"isrc": CANONICAL_ISRC}, ...})
    assert track.isrc == CANONICAL_ISRC

def test_isrc_is_normalized() -> None:
    lowercase_isrc = CANONICAL_ISRC.lower()
    track = _make_spotify_track({"id": TRACK_ID, "external_ids": {"isrc": lowercase_isrc}, ...})
    assert track.isrc == CANONICAL_ISRC
```

- Define constants at **module level** (`UPPER_SNAKE_CASE`) when a value is referenced in two or more tests.
- Use a **local variable with a descriptive name** when a value is only used within one test body.
- This applies to track IDs, URIs, ISRC codes, status strings, numeric thresholds, durations — any literal that carries domain meaning.

---

## General Best Practices

- **No production-code changes to ease testing.** If a class is hard to test, prefer dependency injection or a thin seam over adding test-only hooks.
- **No filesystem or network I/O in unit tests.** Use `tmp_path` (pytest fixture) for file operations; mock API clients for network calls.
- **Tests must be deterministic.** No `time.sleep`, no `random`, no dependency on clock time (freeze with `freezegun` or monkeypatch if needed).
- **Fast.** Unit tests should run in milliseconds. Mark slow/integration tests with `@pytest.mark.integration` to allow excluding them from the default run.
- **Readable.** A test is documentation. The reader should understand the scenario without reading the source under test.
- **No commented-out tests.** Delete them or convert to `pytest.mark.skip(reason="...")` with an explanation.
