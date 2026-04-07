# Implementation Plan: Batch ISRC Prefetch in match_list

**Branch**: `003-batch-isrc-prefetch` | **Date**: 2026-04-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-batch-isrc-prefetch/spec.md`

## Summary

Eliminate the N+1 Spotify API calls that occur when `embed_matches=True` by introducing
`_prefetch_isrc_data` on `SpotifyMatcher`. Before any ISRC tags are written, all chosen
`SpotifyTrack` matches that lack cached ISRC data are batch-fetched using spotipy's
`tracks()` endpoint (max 50 per call), pre-populating `_data` so all subsequent `.isrc`
reads are served from memory with zero additional network requests.

Files changed: `matchers/spotify_matcher.py` only. No public API surface changes.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: spotipy 2.23.0 (`tracks()` batch endpoint), music-tag 0.4.3, tqdm 4.66.2  
**Storage**: ID3 / Vorbis / iTunes tags via `music-tag` (local files, written by `LocalTrack.isrc` setter)  
**Testing**: pytest via `uv run pytest tests/`  
**Target Platform**: macOS / Linux CLI  
**Project Type**: CLI tool  
**Performance Goals**: ISRC embedding network requests reduced from N to ⌈N/50⌉ for a playlist of N matched tracks; ≥80% wall-clock reduction for 100-track playlist  
**Constraints**: Spotify `/tracks` endpoint hard limit of 50 IDs per call; `SpotifyAPI` singleton uses `retries=0` (exceptions bubble on failure)  
**Scale/Scope**: Typical playlist size 20–300 tracks; single-user CLI tool

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Principle I (Clean Code)**: `_prefetch_isrc_data` does exactly one thing; batch-size
  limit extracted as `SPOTIFY_BATCH_SIZE = 50` module-level constant; all identifiers are
  precise (`needs_fetch`, `id_to_tracks`, `batch`); method stays under 30 lines; nesting ≤ 3.
- [x] **Principle II (SOLID)**: Prefetch is an internal implementation detail of the existing
  embedding concern in `SpotifyMatcher`; no class boundary crossed; no new responsibility
  introduced; `match_list` signature unchanged.
- [x] **Principle III (DRY)**: Batch size constant defined once; no logic duplicated.
- [x] **Principle IV (Readability First)**: This optimization is the measured bottleneck
  (N API calls → ⌈N/50⌉ calls); trade-off documented via spec + inline comment referencing
  the Spotify API limit.
- [x] **Principle V (Unit Tests)**: Tests to cover: all need fetch, none need fetch (skip),
  mixed, >50 tracks (2 batches), null item in response, full batch failure (WARNING check),
  `embed_matches=False` (no batch call). All mocked — no network.
- [x] **Principle VI (Type Safety)**: `_prefetch_isrc_data(matches: list[SpotifyTrack]) -> None`
  fully typed; `id_to_tracks: dict[str, list[SpotifyTrack]]`; passes `mypy` strict.

**Constitution Check**: ✅ PASS — no violations, no complexity justification required.

## Project Structure

### Documentation (this feature)

```text
specs/003-batch-isrc-prefetch/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
matchers/
└── spotify_matcher.py   # MODIFIED: add _prefetch_isrc_data(), restructure match_list()

tests/
└── matchers/
    └── test_spotify_matcher.py   # MODIFIED: add tests for _prefetch_isrc_data and updated match_list
```

**Structure Decision**: Single-file change. No new modules, no new classes. The batch
prefetch is a private method on the existing `SpotifyMatcher` class — consistent with
the project's pattern of keeping implementation details within the class that owns them.

## Complexity Tracking

No Constitution violations. No complexity justification required.
