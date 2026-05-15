# Tasks: Cross-Platform Playlist Sync

**Feature**: `008-cross-platform-playlist-sync`
**Input**: Design documents from `/specs/008-cross-platform-playlist-sync/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/playlist-factory.md ✅, quickstart.md ✅

**Tests**: Required per Constitution Principle V. Test tasks are included within each user story phase.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (operates on different files; no outstanding dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths are included in every description

---

## Phase 1: Setup

**Purpose**: Prepare the test module so the new test file can be discovered by pytest.

- [X] T001 Create `tests/playlists/__init__.py` to enable pytest discovery for the playlist test module

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core additions that MUST exist before any user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Add `UnrecognisedSourceError(PlaylistSyncError)` to `src/exceptions.py`
- [X] T003 Add `import_tracks(tracks, autopilot, embed_matches)` as `@abstractmethod` to `SyncTarget` in `src/playlists/__init__.py`

**Checkpoint**: `UnrecognisedSourceError` importable, `SyncTarget` contract formalised — user story implementation can now begin.

---

## Phase 3: User Story 1 — Import a Service Playlist into Another Platform (Priority: P1) 🎯 MVP

**Goal**: Enable `deezer import` and `spotify import` to accept a Spotify URI/URL or Deezer URL as `--source`, auto-detect the source platform, and create the destination playlist from matched tracks.

**Independent Test**: Run `deezer import --source "spotify:playlist:<id>" --destination "Name"` (with a mocked API); verify a `DeezerPlaylist` is created and `import_tracks` is called with the resolved track collection.

### Tests for User Story 1 (REQUIRED — Constitution Principle V)

> **Write these tests FIRST — they must fail before the implementation exists.**

- [X] T004 [P] [US1] Create `tests/playlists/test_playlist_factory.py` with unit tests for `PlaylistFactory.resolve()` covering: Spotify URI → `SpotifyPlaylist`, Spotify HTTPS URL → `SpotifyPlaylist`, Deezer HTTPS URL → `DeezerPlaylist` (correct numeric ID extracted), `path_mapper` + service source → `InvalidPathMappingError`, unrecognised source string → `UnrecognisedSourceError`
- [X] T017 [US1] Add parametrised tests to `tests/playlists/test_playlist_factory.py` covering all six source×destination dispatch paths confirming `resolve()` returns the correct `TrackCollection` subtype for each source format: local file, local directory, Spotify URI, Spotify URL, Deezer URL — covering FR-007 and SC-002 (Depends on T004 — file creation)

### Implementation for User Story 1

- [X] T005 [US1] Create `src/playlists/playlist_factory.py` with module-level constants (`SPOTIFY_URI_PREFIX`, `SPOTIFY_URL_FRAGMENT`, `DEEZER_PLAYLIST_URL_PATTERN`) and private module-level helpers (`_is_spotify_source`, `_is_deezer_source`, `_extract_deezer_playlist_id`)
- [X] T006 [US1] Implement `PlaylistFactory.__init__(spotify_client, deezer_client)` and `PlaylistFactory.resolve(source, path_mapper)` with full dispatch logic and guards in `src/playlists/playlist_factory.py`
- [X] T007 [US1] Add `_build_playlist_factory()` (constructs `PlaylistFactory` from authenticated clients; existing `_build_path_mapper()` is retained and called by each command before `resolve_source()`) and `resolve_source()` (calls `factory.resolve()`, catches both `UnrecognisedSourceError` **and** `InvalidPathMappingError`, converts each to `click.UsageError` with a user-readable message) to `src/main.py`
- [X] T008 [US1] Update `cli_spotify_import` and `cli_deezer_import` in `src/main.py` to replace `get_playlist()` calls with `resolve_source()`, silently ignore `--embed-matches` when source is a service URL, and raise `click.UsageError` when `--from-path`/`--to-path` is combined with a service source
- [X] T018 [US1] Add try/except around `.tracks` iteration in `cli_spotify_import`, `cli_spotify_sync`, `cli_deezer_import`, and `cli_deezer_sync` in `src/main.py` to catch platform API errors (e.g. `spotipy.SpotifyException`, Deezer API errors) and re-raise as `click.ClickException` with a clear error message — ensures source playlist fetch failure exits immediately without modifying the destination playlist (FR-011)

**Checkpoint**: `spotify import` and `deezer import` now accept service playlist sources; existing local `.m3u` import still works.

---

## Phase 4: User Story 2 — Sync an Existing Service Playlist from Another Platform (Priority: P2)

**Goal**: Enable `deezer sync` and `spotify sync` to accept a service playlist URL/URI as `--source`, so an existing destination playlist is cleared and repopulated with freshly matched tracks.

**Independent Test**: Run `deezer sync --source "spotify:playlist:<id>" --destination "<deezer-id>"` (with a mocked API); verify the destination playlist is cleared and `import_tracks` is called with the resolved track collection.

### Tests for User Story 2 (REQUIRED — Constitution Principle V)

- [X] T009 [US2] Extend `tests/playlists/test_playlist_factory.py` with unit tests for `PlaylistFactory.resolve()` — symmetric to T004 — confirming the same Spotify URI, Spotify URL, and Deezer URL dispatch cases apply to sync-command inputs (Depends on T004 — file creation)

### Implementation for User Story 2

- [X] T010 [US2] Update `cli_spotify_sync` and `cli_deezer_sync` in `src/main.py` to replace `get_playlist()` calls with `resolve_source()`, applying the same `--embed-matches` ignore and `--from-path`/`--to-path` guard as the import commands

**Checkpoint**: All four CLI commands (`spotify import`, `spotify sync`, `deezer import`, `deezer sync`) now accept service playlist sources.

---

## Phase 5: User Story 3 — Existing Local-to-Service Workflows Are Unchanged (Priority: P1)

> **Note**: US3 carries Priority P1 but is sequenced after US2 (P2) because regression validation logically depends on both US1 and US2 being complete. This is a dependency constraint, not a priority downgrade.

**Goal**: Confirm zero regressions — all local `.m3u` and directory sync/import workflows behave identically to before this feature.

**Independent Test**: Run existing `spotify import --source <m3u-file>` and `deezer sync --source <m3u-file>` commands; verify identical behavior to before this feature.

### Tests for User Story 3 (REQUIRED — Constitution Principle V)

- [X] T011 [US3] Add regression tests to `tests/playlists/test_playlist_factory.py` covering: local `.m3u` file → `LocalPlaylist` (with and without `path_mapper`), local directory → `LocalLibrary`, `path_mapper` correctly forwarded for local sources (Depends on T004 — file creation)

### Validation for User Story 3

- [X] T012 [US3] Run `uv run pytest tests/` from repo root and confirm all pre-existing tests pass alongside the new ones (zero regressions)

**Checkpoint**: Full test suite green; regression coverage confirmed.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Code quality gates and final validation.

- [X] T013 [P] Run `uv run ruff format . && uv run ruff check .` and fix any style or lint violations in modified files (`src/exceptions.py`, `src/playlists/__init__.py`, `src/playlists/playlist_factory.py`, `src/main.py`)
- [X] T014 [P] Run `uv run mypy .` and resolve any type errors in modified and new files
- [X] T015 Migrate ALL remaining `get_playlist()` call sites in `src/main.py` — including `match`, `compare`, and `duplicates` commands — to `resolve_source()`, then delete `get_playlist()` entirely. Consistent source resolution throughout the module is required (Constitution Principle III — DRY).
- [ ] T016 Validate the quickstart.md smoke-test scenarios end-to-end (cross-platform import and sync) against the implemented CLI
- [X] T019 Add Google-style docstrings to `PlaylistFactory`, `PlaylistFactory.resolve()`, `_build_playlist_factory()`, `resolve_source()`, and `UnrecognisedSourceError` in `src/playlists/playlist_factory.py`, `src/main.py`, and `src/exceptions.py` per Constitution Principle VI

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — **BLOCKS all user story work**
- **US1 (Phase 3)**: Depends on Phase 2 — this is the MVP; deliver first
- **US2 (Phase 4)**: Depends on Phase 2 — can start in parallel with Phase 3 if staffed (US2 only touches `cli_spotify_sync`/`cli_deezer_sync`, which are different functions from US1's `import` commands)
- **US3 (Phase 5)**: Depends on Phase 3 AND Phase 4 — regression validation runs last
- **Polish (Phase 6)**: Depends on Phase 5

### User Story Dependencies

| Story | Priority | Can start after | Parallel with |
|-------|----------|-----------------|---------------|
| US1 — Import service playlist | P1 | Phase 2 | US2 (different functions) |
| US2 — Sync service playlist | P2 | Phase 2 | US1 (different functions) |
| US3 — Regression validation | P1 | US1 + US2 complete | — |

### Within Each User Story

- T004 and T017 (Phase 3) MUST be written and **fail** before US1 implementation begins
- T009 and T011 depend on T004 (file creation) — they MUST NOT start until T004 is complete
- Module constants and helpers (T005) before `resolve()` implementation (T006)
- `PlaylistFactory` complete (T006) before `main.py` integration (T007, T008)
- `resolve_source()` helper (T007) before command updates (T008, T010, T018)

---

## Parallel Execution Examples

### User Story 1 (single developer, sequential)

```
Phase 1 → Phase 2 (T002, T003) → T004, T017 (tests, fail) → T005 → T006 → T007 → T008 → T018 → verify tests pass
```

### User Story 1 + User Story 2 (two developers in parallel after Phase 2)

```
Developer A: T004 → T017 → T005 → T006 → T007 → T008 → T018   (US1 — import commands + API error handling)
Developer B: [after T004] T009 → T010                            (US2 — sync commands)
Both merge → Phase 5 (T011, T012) → Phase 6
```

---

## Implementation Strategy

**MVP Scope**: Phase 1 + Phase 2 + Phase 3 (US1) — delivers the core value (cross-platform import) and all supporting infrastructure.

**Incremental Delivery**:
1. Phase 1–3: Cross-platform import works; sync still local-only
2. Add Phase 4: Cross-platform sync works; all six source×destination combinations live
3. Add Phase 5–6: Full regression coverage + quality gates signed off

**Key Files Changed** (per plan.md):
- `src/exceptions.py` — add `UnrecognisedSourceError` (T002)
- `src/playlists/__init__.py` — add `import_tracks` abstractmethod to `SyncTarget` (T003)
- `src/playlists/playlist_factory.py` — new file (T005, T006)
- `src/main.py` — add helpers, update all commands including `match`, `compare`, `duplicates` (T007, T008, T010, T015, T018)
- `tests/playlists/__init__.py` — new file (T001)
- `tests/playlists/test_playlist_factory.py` — new file (T004, T009, T011, T017)
