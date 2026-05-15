# Implementation Plan: Cross-Platform Playlist Sync

**Branch**: `008-cross-platform-playlist-sync` | **Date**: 2026-05-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-cross-platform-playlist-sync/spec.md`

## Summary

Enable any `TrackCollection` (local `.m3u`, `SpotifyPlaylist`, `DeezerPlaylist`) to be synced into any `SyncTarget` (`SpotifyPlaylist`, `DeezerPlaylist`). Introduce a `PlaylistFactory` class that detects the source platform from a URL/URI string and constructs the appropriate `TrackCollection`. Formalise `import_tracks()` as an abstract method on `SyncTarget`. Update the four CLI `import`/`sync` commands to use `PlaylistFactory` for source resolution. No changes to matchers or track classes are required — they already handle any `Track` subclass.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: spotipy 2.23.0, deezer-python, click 8.1.7, tqdm 4.66.2, music-tag 0.4.3  
**Storage**: N/A — no new persistence introduced  
**Testing**: pytest  
**Target Platform**: CLI tool, cross-platform (Windows/Linux/macOS)  
**Project Type**: CLI  
**Performance Goals**: No new requirements — single-operator tool; existing matcher performance is unchanged  
**Constraints**: Zero regressions on existing local→service flows; no new user-facing flags required; `PlaylistFactory` must not sit below the Playlist layer to avoid inverting CLI→Playlist→Matcher→API  
**Scale/Scope**: 1 new file (`playlist_factory.py`), 3 modified files (`__init__.py`, `main.py`, 1 test file created); ~100 lines of production code

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Principle I (Clean Code)**: `PlaylistFactory`, `resolve()`, `_is_spotify_source()`, `_is_deezer_source()`, `_extract_deezer_playlist_id()` — all names are precise and reveal intent. Single-purpose helpers. No magic literals (regex patterns and URL prefixes become named constants). Functions stay well under 30 lines.
- [x] **Principle II (SOLID)**: `PlaylistFactory` has a single responsibility (source detection + construction). Clients injected via constructor. `SyncTarget` is extended (new abstract method) not modified in existing behavior. No polymorphism violations — the existing `Playlist`/`SyncTarget` hierarchy is preserved.
- [x] **Principle III (DRY)**: All URL/URI detection logic lives in one place (`PlaylistFactory`). CLI commands delegate to it; no duplication of detection logic across `cli_spotify_import`, `cli_spotify_sync`, `cli_deezer_import`, `cli_deezer_sync`.
- [x] **Principle IV (Readability First)**: No performance-sensitive paths introduced. `PlaylistFactory.resolve()` is pure dispatch logic with no optimization trade-offs.
- [x] **Principle V (Unit Tests)**: `tests/playlists/test_playlist_factory.py` required, covering: local file, local dir, Spotify URI, Spotify HTTPS URL, Deezer HTTPS URL, path_mapper + service source → `ValueError`, unrecognised source → `ValueError`.
- [x] **Principle VI (Type Safety)**: All new public APIs carry explicit type hints. `PlaylistFactory` requires Google-style docstrings. Custom exception class (`UnrecognisedSourceError`) defined for the unrecognised-source failure mode rather than bare `ValueError`.
- [x] **Quality Gates**: `ruff format .`, `ruff check .`, `mypy .`, `pytest tests/` all expected to pass.

## Project Structure

### Documentation (this feature)

```text
specs/008-cross-platform-playlist-sync/
├── plan.md              ← this file
├── research.md          ← spotipy _get_id() behavior, Deezer URL parsing, circular imports, exceptions
├── data-model.md        ← PlaylistFactory, SyncTarget.import_tracks(), UnrecognisedSourceError
├── quickstart.md        ← CLI cross-platform examples, source × destination matrix
├── contracts/
│   └── playlist-factory.md  ← PlaylistFactory.resolve() + SyncTarget.import_tracks() contracts
└── tasks.md             ← Phase 2 output (speckit.tasks — NOT created by speckit.plan)
```

### Source Code (repository root)

```text
src/
├── playlists/
│   ├── __init__.py              (modified — add import_tracks abstractmethod to SyncTarget)
│   └── playlist_factory.py      (new — PlaylistFactory class)
└── main.py                      (modified — _build_playlist_factory(), resolve_source(), 4 commands)

tests/
└── playlists/
    └── test_playlist_factory.py (new — unit tests for PlaylistFactory.resolve())
```

**Structure Decision**: Single-project layout. `PlaylistFactory` belongs in `src/playlists/` because it constructs `SpotifyPlaylist`/`DeezerPlaylist` objects; placing it in `src/api/` would invert the `CLI → Playlist → Matcher → API` layer order.
