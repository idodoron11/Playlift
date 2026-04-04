# Implementation Plan: ISRC-Based Track Matching and Embedding

**Branch**: `001-isrc-track-matching` | **Date**: 2026-04-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-isrc-track-matching/spec.md`

## Summary

Add ISRC-based track matching as a deterministic first-pass before fuzzy search. When a local track has a valid ISRC in its audio tags, look it up in Spotify's catalog via `isrc:` query syntax. If found, use that match directly; otherwise fall back to the existing fuzzy search. After any successful match (when embedding is active), write the Spotify track's ISRC back into the local file's tags so future runs can skip fuzzy search.

## Technical Context

**Language/Version**: Python ≥ 3.11  
**Primary Dependencies**: `spotipy==2.23.0` (Spotify API), `music-tag==0.4.3` (tag read/write), `mutagen` (low-level tag access), `click==8.1.7` (CLI)  
**Storage**: Local audio files (mp3, flac, m4a) with embedded ID3/Vorbis/MP4 tags  
**Testing**: `pytest` with fakes (`FakeLocalTrack`, `TrackMock`) and spies (`SpotifyPlaylistSpy`)  
**Target Platform**: macOS/Linux CLI  
**Project Type**: CLI tool  
**Performance Goals**: N/A — single-user tool, dominated by Spotify API latency  
**Constraints**: No new dependencies; must fit within existing `music-tag` + `mutagen` tag infrastructure  
**Scale/Scope**: Personal music libraries (hundreds to low thousands of tracks per playlist)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Principle I (Clean Code)**: All new identifiers are precise and descriptive (`isrc`, `isrc_ref`, `search_by_isrc`, `is_valid_isrc`); no magic literals (ISRC regex is a module-level constant); functions stay under ~30 lines; nesting ≤ 3 levels.
- [x] **Principle II (SOLID)**: ISRC reading is LocalTrack's responsibility (it owns tag I/O); ISRC lookup is SpotifyMatcher's responsibility (it owns matching strategy); ISRC exposure on SpotifyTrack is SpotifyTrack's responsibility (it owns API data extraction). No new classes needed — additions extend existing responsibilities.
- [x] **Principle III (DRY)**: ISRC validation regex defined once as a module constant; tag read/write reuses existing `_get_custom_tag`/`_set_custom_tag` infrastructure; no duplication of search logic.
- [x] **Principle IV (Readability First)**: No performance optimization needed; ISRC lookup is a simple API call.
- [x] **Principle V (Unit Tests)**: Tests planned for: ISRC validation, ISRC property read/write on LocalTrack, ISRC property on SpotifyTrack, matcher ISRC-first flow, fallback to fuzzy, embedding after match, SKIP handling, malformed ISRC handling. All isolated via fakes.
- [x] **Principle VI (Type Safety)**: All new properties and methods will have complete type hints; `isrc` property returns `str | None`; validation function returns `bool`.
- [x] **Quality Gates**: `ruff format .`, `ruff check .`, `mypy .`, `pytest tests/` all pass.

## Project Structure

### Documentation (this feature)

```text
specs/001-isrc-track-matching/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
tracks/
├── local_track.py       # Add: isrc property (read/write via _get_custom_tag/_set_custom_tag)
└── spotify_track.py     # Add: isrc property (read from data["external_ids"]["isrc"])

matchers/
└── spotify_matcher.py   # Add: ISRC validation + ISRC-first lookup in match() flow

tests/
├── tracks/
│   ├── test_local_track.py   # Add/extend: ISRC read/write tests (new file or extend existing)
│   ├── test_spotify_track.py # Add: ISRC property test
│   └── track_mock.py         # Add: optional isrc field to TrackMock
└── matchers/
    └── test_spotify_matcher.py  # Add: ISRC-first matching, fallback, validation, embedding tests
```

**Structure Decision**: No new directories or modules. All changes fit within existing modules following the established layered architecture (Tracks → Matchers → API).

## Complexity Tracking

No constitution violations. No complexity justifications needed.
