# Implementation Plan: Decouple Playlist from SyncTarget (ISP / LSP Fix)

**Branch**: `005-decouple-playlist-synctarget` | **Date**: 2026-04-21 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/005-decouple-playlist-synctarget/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Remove `track_matcher()` from the `Playlist` ABC and introduce a new `SyncTarget` ABC that owns this method. `SpotifyPlaylist` inherits both `Playlist` and `SyncTarget`; `LocalPlaylist` inherits only `Playlist`. This eliminates the LSP violation where `LocalPlaylist.track_matcher()` raises `TypeError`, and applies the Interface Segregation Principle to cleanly separate "track collection" from "sync destination" concerns. Zero behavioral changes — validated by existing tests, mypy, and ruff.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: spotipy 2.23.0, music-tag 0.4.3, click 8.1.7  
**Storage**: Local filesystem (m3u files, ID3 tags)  
**Testing**: pytest (via `uv run pytest tests/`)  
**Target Platform**: macOS / Linux CLI  
**Project Type**: CLI tool  
**Performance Goals**: N/A (structural refactoring only)  
**Constraints**: N/A (no new runtime code paths)  
**Scale/Scope**: 4 files modified, ~15 lines changed total

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Principle I (Clean Code)**: `SyncTarget` is a precise, descriptive name. No new
  functions exceed 5 lines. No magic literals introduced. No nesting changes.
- [x] **Principle II (SOLID)**: This IS the SOLID fix — removes LSP violation (L) from
  `LocalPlaylist` and applies ISP (I) by splitting `Playlist` from `SyncTarget`.
  Constitution §II-L explicitly calls out: "Overriding a method to raise
  `NotImplementedError` signals a broken abstraction — split the interface."
- [x] **Principle III (DRY)**: No logic duplication — the `track_matcher()` body exists
  exactly once in `SpotifyPlaylist` and is removed from `LocalPlaylist` and `PlaylistMock`.
- [x] **Principle IV (Readability First)**: No performance trade-offs. The refactoring
  simplifies the type hierarchy which improves readability.
- [x] **Principle V (Unit Tests)**: No new concrete classes are introduced. `SyncTarget` is
  abstract; its implementation (`SpotifyPlaylist.track_matcher()`) is already tested. Existing
  test suite validates behavior preservation. No new test files needed per SC-007.
- [x] **Principle VI (Type Safety)**: `SyncTarget` ABC has complete type hints. All modified
  files must pass `mypy` strict mode. No new exceptions or domain concepts.
- [x] **Quality Gates**: `ruff format .`, `ruff check .`, `mypy .`, `pytest tests/` all
  must pass as success criteria SC-001 through SC-003.

## Project Structure

### Documentation (this feature)

```text
specs/005-decouple-playlist-synctarget/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── spec.md              # Feature specification
```

### Source Code (files modified by this feature)

```text
playlists/
├── __init__.py           # Add SyncTarget ABC, remove track_matcher() from Playlist
├── local_playlist.py     # Remove track_matcher() stub + Matcher import
└── spotify_playlist.py   # Add SyncTarget to base classes + import SyncTarget

tests/
└── playlists/
    └── playlist_mock.py  # Remove track_matcher() + orphaned Matcher/MatcherMock imports
```

**Structure Decision**: No new files or directories. All changes are within existing modules.
The `SyncTarget` ABC is co-located in `playlists/__init__.py` alongside `Playlist` and
`TrackCollection` for consistency.

## Complexity Tracking

No constitution violations to justify. All gates pass.
