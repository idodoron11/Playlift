# Implementation Plan: Decouple Matcher from Concrete Track Implementation

**Branch**: `006-fix-matcher-layer-violation` | **Date**: 2026-04-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-fix-matcher-layer-violation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Introduce two new ABCs — `ServiceTrack(Track)` and `EmbeddableTrack` — to remove the DIP and SRP violations in `SpotifyMatcher`. After this refactor: `SpotifyTrack` extends `ServiceTrack` (adding `permalink` + `service_name`); `Track` gains a concrete `service_ref(service_name) -> str | None` method (default `return None`); `LocalTrack` implements `EmbeddableTrack` (adding `embed_match`) and overrides `service_ref` to read from audio tags; the matcher calls `track.service_ref(SpotifyTrack.service_name)` directly on any `Track` (no `isinstance` on the read path), and delegates persistence via `source_track.embed_match(match)` guarded by `isinstance(source_track, EmbeddableTrack)`. `Matcher` ABC is unchanged. No behavioral changes.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: spotipy 2.23.0, music-tag 0.4.3, mutagen  
**Storage**: Local filesystem (ID3/FLAC/M4A audio tags via mutagen)  
**Testing**: pytest (via `uv run pytest tests/`)  
**Target Platform**: macOS / Linux CLI  
**Project Type**: CLI tool / library  
**Performance Goals**: N/A (structural refactoring only — no new runtime code paths)  
**Constraints**: Zero behavioral change; all existing tests must continue to pass  
**Scale/Scope**: 6 source files modified, 2 test files modified; ~80 lines net change

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Principle I (Clean Code)**: `ServiceTrack`, `EmbeddableTrack`, `service_ref`, `embed_match`, `service_name` are all precise, descriptive identifiers. `embed_match` body ≤ 10 lines. No magic literals — `"SPOTIFY"` is defined as a class property on `SpotifyTrack`; `SpotifyMatcher` reads it via `SpotifyTrack.service_name`. No nesting changes.
- [x] **Principle II (SOLID)**: This IS the SOLID fix — eliminates the DIP violation (D) and SRP violation (S). Constitution §II-D: "High-level modules depend on abstractions, not concrete classes." Constitution §II-I: "Spotify-specific methods MUST NOT appear on the base `Track`." `ServiceTrack` and `EmbeddableTrack` are small, focused interfaces. `EmbeddableTrack` is a single-method write contract. `service_ref` on `Track` removes the read-path `isinstance` entirely.
- [x] **Principle III (DRY)**: ISRC normalization logic (`_normalize_isrc`) remains in a single place in `local_track.py`. The embed logic previously duplicated in `_update_spotify_match_in_source_track` is removed and lives exclusively in `LocalTrack.embed_match`.
- [x] **Principle IV (Readability First)**: No performance trade-offs. Delegation via `embed_match` is simpler and more expressive than the existing `isinstance` + raw tag writes.
- [x] **Principle V (Unit Tests)**: `LocalTrack.embed_match` is a new concrete method — covered by `TestLocalTrackEmbedMatch` in `tests/tracks/test_local_track.py`. Edge cases covered: no ISRC on match, same ISRC already stored, different service tags coexisting. Matcher delegation covered by updated T021–T025.
- [x] **Principle VI (Type Safety)**: All new ABCs and overrides carry complete type hints. `embed_match(self, match: ServiceTrack) -> None` — type-safe by construction (cannot pass a `LocalTrack` as match). Code must pass `mypy` strict mode; `from __future__ import annotations` added where needed.
- [x] **Quality Gates**: `ruff format .`, `ruff check .`, `mypy .`, `pytest tests/` all must pass as SC-005 and SC-006.

## Project Structure

### Documentation (this feature)

```text
specs/006-fix-matcher-layer-violation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── service-track.md       # ServiceTrack ABC contract
│   └── embeddable-track.md    # EmbeddableTrack ABC contract
└── spec.md              # Feature specification
```

### Source Code (files modified by this feature)

```text
tracks/
├── __init__.py           # Add ServiceTrack(Track, ABC), EmbeddableTrack(ABC); add concrete service_ref to Track
├── local_track.py        # Add EmbeddableTrack to bases; override service_ref; add embed_match
└── spotify_track.py      # Add ServiceTrack to bases; add permalink, service_name

matchers/
└── spotify_matcher.py    # Remove LocalTrack/_normalize_isrc imports; import EmbeddableTrack;
                         # read path uses track.service_ref(SpotifyTrack.service_name) directly

tests/
├── matchers/
│   └── test_spotify_matcher.py  # Update TestEmbedIsrc (T021–T025/T027) to delegation assertions
└── tracks/
    └── test_local_track.py      # Add TestLocalTrackEmbedMatch
```

**Structure Decision**: No new source files or directories. All changes are within existing modules. `ServiceTrack` and `EmbeddableTrack` are co-located in `tracks/__init__.py` alongside `Track` for a single import surface.

## Complexity Tracking

No constitution violations to justify. All gates pass.
