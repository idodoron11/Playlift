# Tasks: Decouple Matcher from Concrete Track Implementation

**Input**: Design documents from `/specs/006-fix-matcher-layer-violation/`
**Prerequisites**: plan.md ✅, spec.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no unresolved dependencies)
- **[Story]**: User story label — [US1] P1 · [US2] P2 · [US3] P3
- Exact file paths included in every implementation task

---

## Phase 1: Setup

No new project structure, files, or dependencies required — this is an in-place structural refactor within existing modules. Proceed directly to Phase 2.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Declare the two new ABCs and add `service_ref` to `Track`. Every user story depends on these being in place first.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T001 Add `ServiceTrack(Track, ABC)` and `EmbeddableTrack(ABC)` to `tracks/__init__.py`; add concrete `service_ref(service_name: str) -> str | None` method to `Track` returning `None` by default; declare `ServiceTrack` **before** `EmbeddableTrack` (its `embed_match` signature references `ServiceTrack`); add Google-style docstrings to all three new/modified public symbols (`ServiceTrack`, `EmbeddableTrack`, `Track.service_ref`)
- [X] T002 Update `SpotifyTrack` to extend `ServiceTrack`; add `permalink` property returning `self.track_url` and `service_name` property returning `"SPOTIFY"` in `tracks/spotify_track.py`; add Google-style docstrings to both new properties (depends on T001 — `ServiceTrack` must exist first)

**Checkpoint**: `ServiceTrack`, `EmbeddableTrack`, and `Track.service_ref` exist; `SpotifyTrack` satisfies `ServiceTrack`. All user story phases can now begin.

---

## Phase 3: User Story 1 — Matcher Delegates Match Persistence (Priority: P1) 🎯 MVP

**Goal**: The matcher embeds match data via `EmbeddableTrack.embed_match` and reads stored refs via `Track.service_ref` — zero references to `LocalTrack` or `_normalize_isrc` remain in the matcher layer.

**Independent Test**: Given a `Mock(spec=EmbeddableTrack)` as source and a `SpotifyTrack` as match, calling `SpotifyMatcher._update_spotify_match_in_source_track` results in `source.embed_match.assert_called_once_with(matched)` passing. Given a non-`EmbeddableTrack` source, the same call is a silent no-op.

### Tests for User Story 1 (REQUIRED — Constitution Principle V)

> **Write these tests FIRST, confirm they FAIL before implementing T004/T005**

- [X] T003 [P] [US1] Add `TestLocalTrackEmbedMatch(_LocalTrackTestBase)` to `tests/tracks/test_local_track.py` with 9 test methods:
  - `test_embed_match_writes_service_ref_when_unset`
  - `test_embed_match_skips_service_ref_when_already_matches`
  - `test_embed_match_updates_service_ref_when_differs`
  - `test_embed_match_does_not_touch_other_service_ref`
  - `test_embed_match_writes_isrc_when_missing`
  - `test_embed_match_skips_isrc_when_already_matches`
  - `test_embed_match_updates_isrc_when_differs`
  - `test_embed_match_skips_isrc_when_match_has_no_isrc`
  - `test_embed_match_normalizes_hyphenated_isrc_from_match`

### Implementation for User Story 1

- [X] T004 [US1] Add `service_ref(self, service_name: str) -> str | None` override (delegates to `self._get_custom_tag(service_name)`) and `embed_match(self, match: ServiceTrack) -> None` method to `LocalTrack` in `tracks/local_track.py`; add `EmbeddableTrack` to `LocalTrack` base classes; add Google-style docstrings to both new methods — Note: `_get_custom_tag` normalizes tag names to uppercase internally, so `service_ref("SPOTIFY")` and the existing `spotify_ref` property read the same underlying tag key (depends on T001, T002, T003 tests failing)
- [X] T005 [US1] Update `matchers/spotify_matcher.py`: remove `from tracks.local_track import LocalTrack, _normalize_isrc`; add `from tracks import EmbeddableTrack`; replace `_find_spotify_match_in_source_track` body with `return track.service_ref(SpotifyTrack.service_name)`; replace `_update_spotify_match_in_source_track` body with `if isinstance(source_track, EmbeddableTrack): source_track.embed_match(match)` (depends on T001, T002, T004)
- [X] T006 [US1] Update `TestEmbedIsrc` in `tests/matchers/test_spotify_matcher.py` (depends on T004, T005):
  - **T021, T022, T022b, T024, T027 sub-test** (call `_update_spotify_match_in_source_track` directly): replace `Mock(spec=LocalTrack)` + `PropertyMock` chains with `Mock(spec=EmbeddableTrack)`; assert `source.embed_match.assert_called_once_with(matched)` or `source.embed_match.assert_not_called()` as appropriate; remove per-test `from tracks.local_track import LocalTrack` imports
  - **T023** (`test_embed_isrc_skipped_when_embed_matches_false` — calls `match_list()`): keep `Mock(spec=LocalTrack)` (post-refactor `LocalTrack` IS-A `EmbeddableTrack`; using `EmbeddableTrack` spec would hide `service_ref` which the matcher calls on the read path inside `match_list`); remove `from tracks.local_track import LocalTrack` and replace with `from tracks import EmbeddableTrack; from tracks.local_track import LocalTrack` — keeping the LocalTrack import only for T023
  - **T025** (`test_embed_isrc_skipped_for_skip_track`): update comment from "isinstance guard" to "non-EmbeddableTrack source"; no mock spec change needed (uses `TrackMock`)

**Checkpoint**: `pytest tests/matchers/test_spotify_matcher.py -k "Embed"` and `pytest tests/tracks/test_local_track.py -k "EmbedMatch"` both pass. `grep -r "LocalTrack\|_normalize_isrc" matchers/` returns no matches.

---

## Phase 4: User Story 2 — New Service Extensibility (Priority: P2)

**Goal**: Demonstrate that a second service reference can be embedded into the same local audio file independently — no modifications to `Matcher`, `LocalTrack`, or any existing class are needed.

**Independent Test**: A `LocalTrack` that already has a `SPOTIFY` service ref can receive an embed for a `DEEZER` `ServiceTrack`; afterwards `service_ref("SPOTIFY")` and `service_ref("DEEZER")` each return the correct independent values.

### Tests for User Story 2 (REQUIRED — Constitution Principle V)

- [X] T007 [P] [US2] Add `TestLocalTrackServiceRefCoexistence(_LocalTrackTestBase)` to `tests/tracks/test_local_track.py` with tests:
  - `test_service_ref_returns_none_for_unknown_service`
  - `test_embed_match_does_not_overwrite_different_service_ref`
  - `test_two_service_refs_coexist_independently`

**Checkpoint**: Multi-service coexistence is verified in isolation. No changes to `SpotifyMatcher` or `LocalTrack` were required to make these tests pass.

---

## Phase 5: User Story 3 — ServiceTrack Contract on SpotifyTrack (Priority: P3)

**Goal**: Confirm that `SpotifyTrack` satisfies the `ServiceTrack` contract (non-null `permalink` and `service_name`), and that `LocalTrack` does NOT implement `ServiceTrack`.

**Independent Test**: `isinstance(spotify_track, ServiceTrack)` is `True`; `isinstance(local_track, ServiceTrack)` is `False`; `spotify_track.permalink` returns a non-empty URL; `spotify_track.service_name` returns `"SPOTIFY"`.

### Tests for User Story 3 (REQUIRED — Constitution Principle V)

- [X] T008 [P] [US3] Add `TestSpotifyTrackServiceContract` to `tests/tracks/test_spotify_track.py` with tests:
  - `test_permalink_returns_track_url`
  - `test_service_name_returns_spotify`
  - `test_spotify_track_is_service_track`
- [X] T009 [P] [US3] Add `TestTrackContracts` to `tests/tracks/test_local_track.py` with tests:
  - `test_local_track_is_embeddable_track`
  - `test_local_track_is_not_service_track`

**Checkpoint**: All three user stories are independently functional and verified.

---

## Phase N: Polish & Quality Gates

- [X] T010 [P] Run `uv run mypy .` and resolve any type errors introduced by new ABCs and overrides in `tracks/__init__.py`, `tracks/local_track.py`, `tracks/spotify_track.py`, and `matchers/spotify_matcher.py` (SC-005)
- [X] T011 [P] Run `uv run ruff check . && uv run ruff format .` and resolve any linting or formatting issues (SC-006)
- [X] T012 Run `uv run pytest tests/` and confirm the full test suite passes with no regressions (SC-003)
- [X] T013 [P] Static verification: confirm `grep -rn "LocalTrack\|_normalize_isrc" matchers/` returns no matches (SC-001, SC-002)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 2)**: No dependencies — start immediately
- **US1 (Phase 3)**: Depends on Phase 2 completion (T001, T002) — BLOCKED until Phase 2 is done
- **US2 (Phase 4)**: Depends on T004 (`LocalTrack.embed_match`) — can start once T004 is complete
- **US3 (Phase 5)**: Depends on T002 (`SpotifyTrack.service_name`, `permalink`) — can start once T002 is complete
- **Polish (Phase N)**: Depends on all implementation phases being complete

### User Story Dependencies

- **US1 (P1)**: Blocked by Phase 2 (T001 + T002). Tests (T003) can be written in parallel with Phase 2.
- **US2 (P2)**: Depends only on T004. Can start as soon as T004 is done — independent of T005/T006.
- **US3 (P3)**: Depends only on T002. Can start as soon as T002 is done — independent of US1/US2.

### Within Each User Story

- Tests written FIRST and must FAIL before implementation (TDD)
- `embed_match` implementation (T004) before matcher update (T005)
- Matcher update (T005) before matcher test update (T006)

### Parallel Opportunities

- T002 follows T001 (different file; `ServiceTrack` must be defined before `SpotifyTrack` can extend it)
- T003 (write failing tests) runs in parallel with T001+T002 (test file is independent)
- T007 runs in parallel with T005/T006 (different test file, only needs T004)
- T008 runs in parallel with T003/T004 (only needs T002)
- T009 runs in parallel with T008 (same test file, both only need T001+T002)
- T010, T011, T013 run in parallel (independent quality gates)

---

## Parallel Example: Phase 2 + Phase 3 Tests

```
# Phase 2 — run in parallel:
T001: Add ServiceTrack, EmbeddableTrack, Track.service_ref in tracks/__init__.py
T002: Add permalink, service_name to SpotifyTrack in tracks/spotify_track.py

# Phase 3 — T003 can run alongside Phase 2:
T003: Write TestLocalTrackEmbedMatch (9 tests) — confirm they FAIL

# Phase 3 implementation — after Phase 2 complete:
T004: Implement LocalTrack.embed_match + service_ref override
T005: Update SpotifyMatcher
T006: Update TestEmbedIsrc

# After T004 complete — run in parallel with T005/T006:
T007: TestLocalTrackServiceRefCoexistence (US2)
T008: TestSpotifyTrackServiceContract (US3 — after T002)
T009: TestTrackContracts (US3 — after T001+T002)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Foundational (T001, T002)
2. Complete Phase 3: User Story 1 (T003 → T004 → T005 → T006)
3. **STOP and VALIDATE**: `pytest tests/matchers/ tests/tracks/` + `mypy .` + `grep` SC check
4. All violations removed; all tests green → merge-ready MVP

### Incremental Delivery

1. Phase 2 (Foundation) → ABCs exist, `SpotifyTrack` satisfies contract
2. Phase 3 (US1) → Core DIP/SRP violation removed → **MVP: deployable**
3. Phase 4 (US2) → Multi-service coexistence verified by tests
4. Phase 5 (US3) → `ServiceTrack` contract formally verified
5. Phase N (Polish) → All quality gates clean

### Key Invariants to Preserve

- `spotify_ref` property on `LocalTrack` is **unchanged** — external callers (`cleanup.py`, `playlists/`) continue to work
- `isrc` getter/setter on `LocalTrack` is **unchanged** — existing ISRC tests pass without modification
- All `SpotifyMatcher` public methods (`match`, `suggest_match`, `match_list`) have **identical signatures** — zero behavioral change
