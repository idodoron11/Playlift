# Implementation Plan: Remove SpotifyAPI Singleton — Constructor Injection Refactor

**Branch**: `004-remove-spotifyapi-di` | **Date**: 2026-04-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-remove-spotifyapi-di/spec.md`

## Summary

`SpotifyAPI` is a hand-rolled singleton class whose only job is to lazily cache a
`spotipy.Spotify` instance. Replace it with a module-level `get_spotify_client()` function
decorated with `@functools.cache`. Inject the `spotipy.Spotify` client into `SpotifyMatcher`,
`SpotifyTrack`, and `SpotifyPlaylist` constructors (and the two `SpotifyPlaylist` classmethods)
so unit tests can pass mock clients directly without `patch()`. Add a complete `SpotifyPlaylist`
unit test suite — the class currently has zero unit tests.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: spotipy 2.23.0, music-tag 0.4.3, click 8.1.7, tqdm 4.66.2  
**Storage**: N/A — pure code quality refactor, no storage changes  
**Testing**: pytest; mypy strict; ruff check + format  
**Target Platform**: macOS desktop CLI (single-user, single-threaded)  
**Project Type**: CLI tool  
**Performance Goals**: N/A — no hot paths introduced  
**Constraints**: Zero breaking changes to production entry points; all existing integration tests must pass unchanged; `mypy` strict mode (spotipy under `ignore_missing_imports = true`)  
**Scale/Scope**: 9 source files modified, 1 test file rewritten, 1 new test class added

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Principle I (Clean Code)**: `get_spotify_client()` is verb-prefixed and precise. The
  `client` constructor parameter name is descriptive. No magic literals introduced. The new
  function body is ≤ 10 lines. Nesting depth unchanged.
- [x] **Principle II (SOLID)**: This refactor is a direct application of the Dependency
  Inversion Principle — moving from global-state consumption inside business logic to explicit
  constructor injection. SRP is preserved; `api/spotify.py` still has a single concern
  (providing the authenticated client). No new inheritance violations.
- [x] **Principle III (DRY)**: `get_spotify_client()` becomes the single authoritative source
  for the Spotify client. Every call site supplies it explicitly at construction time — no
  hidden global look-up inside classes. No logic duplication introduced.
- [x] **Principle IV (Readability First)**: `@functools.cache` is idiomatic and stdlib.
  No premature optimization. One comment explaining the `retries=0` workaround is preserved
  from the original code.
- [x] **Principle V (Unit Tests)**: Existing `SpotifyMatcher` unit tests are rewritten to
  use constructor injection. A new `SpotifyPlaylist` unit test module is added (FR-009).
  `SpotifyTrack` unit tests are updated to drop the `__new__` bypass. All tests remain
  isolated from the real Spotify API.
- [x] **Principle VI (Type Safety)**: All new public API (`get_spotify_client()`, new
  constructor `client=` params, classmethod `client=` params) carry complete type hints.
  `SpotifyTrack` and `SpotifyPlaylist` use `*, client: spotipy.Spotify | None = None` with an
  explicit `ValueError` guard; `create_from_another_playlist()` uses `*, client: spotipy.Spotify`
  (required, no default). `mypy` strict mode passes; `spotipy` is already under
  `ignore_missing_imports = true` and `api/spotify.py` has `disallow_any_unimported = false`.
- [x] **Quality Gates**: `ruff format .`, `ruff check .`, `mypy .`, `pytest tests/` are
  all required to pass (SC-005).

**Gate result**: ✅ All principles satisfied. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/004-remove-spotifyapi-di/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
api/
└── spotify.py           # REWRITE: SpotifyAPI class → get_spotify_client() function

matchers/
├── __init__.py          # MODIFY: remove TypeError guard from Matcher.__init__; pass client= in get_instance()
└── spotify_matcher.py   # MODIFY: add __init__(client=), convert _search to instance method

playlists/
├── compare.py           # MODIFY: import get_spotify_client; pass client= to SpotifyPlaylist()
└── spotify_playlist.py  # MODIFY: add client= to __init__, create(), create_from_another_playlist()

tracks/
└── spotify_track.py     # MODIFY: add client= keyword param to __init__

main.py                  # MODIFY: import get_spotify_client; pass client= at each construction site
cleanup.py               # MODIFY: import get_spotify_client; pass client= to SpotifyTrack() calls

tests/
├── matchers/
│   └── test_spotify_matcher.py   # REWRITE unit tests: drop patch+_MatcherTestBase, use fixtures
└── playlists/
    └── test_spotify_playlist.py  # ADD new unit test class for SpotifyPlaylist
```

**Structure Decision**: Single-project layout unchanged. No new packages. No new directories.
All changes are surgical modifications to existing files plus one new test class.
