# Tasks: Batch ISRC Prefetch in match_list

**Input**: Design documents from `/specs/003-batch-isrc-prefetch/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: REQUIRED per Constitution Principle V — write tests first, ensure they FAIL before implementing.

**Organization**: Grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description with file path`

- **[P]**: Can run in parallel (different files or independent within same phase)
- **[Story]**: User story tag (US1, US2)

---

## Phase 1: Setup

**Purpose**: Add the batch-size constant that all subsequent phases depend on.

- [X] T001 Add `SPOTIFY_BATCH_SIZE: int = 50` module-level constant to `matchers/spotify_matcher.py` (above class definition, with inline comment citing the Spotify API limit)

**Checkpoint**: Constant in place — Foundational phase can begin.

---

## Phase 2: Foundational — `_prefetch_isrc_data`

**Purpose**: Implement and fully test the new private method that both user stories depend on.
`_prefetch_isrc_data` is the single authoritative piece of prefetch logic; both US1 and US2
are tested end-to-end in their own phases but rely on this method being correct.

**⚠️ CRITICAL**: Write all tests in this phase FIRST. Ensure every test FAILS before implementing T008.

### Tests for Foundational Phase (write first — must FAIL before T008)

- [X] T002 [P] Add test `test_prefetch_isrc_data_fetches_tracks_with_no_data` — tracks with `_data=None` → `SpotifyAPI.tracks()` called with correct IDs, `_data` updated on each `SpotifyTrack` in `tests/matchers/test_spotify_matcher.py`
- [X] T003 [P] Add test `test_prefetch_isrc_data_skips_tracks_that_already_have_isrc` — tracks with `external_ids.isrc` already in `_data` → `SpotifyAPI.tracks()` never called in `tests/matchers/test_spotify_matcher.py`
- [X] T004 [P] Add test `test_prefetch_isrc_data_fetches_only_tracks_missing_isrc` — mix of loaded and unloaded tracks → batch contains only the unloaded IDs in `tests/matchers/test_spotify_matcher.py`
- [X] T005 [P] Add test `test_prefetch_isrc_data_splits_into_batches_of_50` — 51 tracks with no `_data` → `SpotifyAPI.tracks()` called exactly twice with correct batch sizes in `tests/matchers/test_spotify_matcher.py`
- [X] T006 [P] Add test `test_prefetch_isrc_data_logs_warning_and_continues_on_batch_failure` — `SpotifyAPI.tracks()` raises exception → `WARNING` logged with affected track count, no crash, other batches unaffected in `tests/matchers/test_spotify_matcher.py`
- [X] T007 [P] Add test `test_prefetch_isrc_data_skips_null_items_with_debug_log` — batch response contains `None` for one track → `DEBUG` logged for that track, `_data` updated on remaining tracks in `tests/matchers/test_spotify_matcher.py`

### Implementation for Foundational Phase

- [X] T008 Implement `_prefetch_isrc_data(self, matches: list[SpotifyTrack]) -> None` on `SpotifyMatcher` in `matchers/spotify_matcher.py` — see quickstart.md for full pseudocode (must make T002–T007 pass)

**Checkpoint**: All 6 foundational tests pass. `_prefetch_isrc_data` is independently verified before `match_list` is touched.

---

## Phase 3: User Story 1 — Embed Matches Without API Slowdown (Priority: P1) 🎯 MVP

**Goal**: Restructure `match_list` into a two-pass loop (collect → prefetch → embed) so that
`embed_matches=True` triggers at most ⌈N/50⌉ batch requests instead of N individual ones.

**Independent Test**: Run `uv run pytest tests/matchers/test_spotify_matcher.py -k "match_list"`.
All tests pass. The `SpotifyAPI.tracks()` mock is called at most ⌈N/50⌉ times regardless of N.

### Tests for User Story 1 (write first — must FAIL before T011)

- [X] T009 [P] [US1] Add test `test_match_list_with_embed_matches_calls_prefetch_once_per_batch` — `embed_matches=True`, N tracks all needing ISRC → `SpotifyAPI.tracks()` called ⌈N/50⌉ times, all ISRCs written to `LocalTrack` in `tests/matchers/test_spotify_matcher.py`
- [X] T010 [P] [US1] Add test `test_match_list_with_embed_matches_skips_prefetch_when_isrc_cached` — `embed_matches=True`, all matches already have `external_ids.isrc` in `_data` → `SpotifyAPI.tracks()` never called, `spotify_ref` still written to `LocalTrack` in `tests/matchers/test_spotify_matcher.py`

### Implementation for User Story 1

- [X] T011 [US1] Restructure `match_list` in `matchers/spotify_matcher.py` to two-pass design: (1) review loop collects `pairs_to_embed: list[tuple[Track, SpotifyTrack]]`; (2) `if pairs_to_embed:` calls `_prefetch_isrc_data` then embeds — see quickstart.md for full pseudocode (must make T009–T010 pass)

**Checkpoint**: User Story 1 independently testable and functional. `embed_matches=True` on a playlist of any size calls `_prefetch_isrc_data` once, not once per track.

---

## Phase 4: User Story 2 — No Overhead When Not Embedding (Priority: P2)

**Goal**: Verify that the `if pairs_to_embed:` guard (introduced in T011) ensures the prefetch
block is never entered when `embed_matches=False`. No implementation changes required beyond T011.

**Independent Test**: Run `uv run pytest tests/matchers/test_spotify_matcher.py -k "not_embedding"`.
Test passes. Zero calls to `SpotifyAPI.tracks()`.

### Tests for User Story 2 (write first — must FAIL before T011 merges)

- [X] T012 [P] [US2] Add test `test_match_list_without_embed_matches_never_calls_batch_endpoint` — `embed_matches=False`, any playlist → `SpotifyAPI.tracks()` never called, return value is the list of matched `SpotifyTrack` objects identical to current behaviour in `tests/matchers/test_spotify_matcher.py`

### Implementation for User Story 2

No additional implementation required. The `if pairs_to_embed:` guard in T011 fully satisfies US2
by keeping `pairs_to_embed` empty when `embed_matches=False`, preventing the prefetch block from
ever executing.

**Checkpoint**: User Stories 1 AND 2 independently verified. Full test suite passes.

---

## Final Phase: Polish & Quality Gates

- [X] T013 [P] Run `uv run ruff check .` — zero violations
- [X] T014 [P] Run `uv run ruff format .` — zero style violations
- [X] T015 [P] Run `uv run mypy .` — strict mode, zero errors
- [X] T016 Run `uv run pytest tests/` — all tests pass, none skipped without justification

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on T001 — write tests T002–T007 first, then implement T008
- **Phase 3 (US1)**: Depends on Phase 2 completion — write tests T009–T010 first, then implement T011
- **Phase 4 (US2)**: Depends on Phase 3 — T012 test can be written alongside T009–T010 in parallel; implementation is covered by T011
- **Final Phase**: Depends on all user story phases — run all quality gates together

### Parallel Opportunities Within Each Phase

- T002–T007 (foundational tests): all touch only the test file at different test functions → can be written in parallel
- T009, T010, T012 (US1+US2 tests): all touch only the test file → can be written in parallel
- T013–T015 (quality gates): independent tools → run in parallel

---

## Parallel Execution Examples

### Foundational Tests (T002–T007) — write all in parallel

```
T002: test_prefetch_isrc_data_fetches_tracks_with_no_data
T003: test_prefetch_isrc_data_skips_tracks_that_already_have_isrc
T004: test_prefetch_isrc_data_fetches_only_tracks_missing_isrc
T005: test_prefetch_isrc_data_splits_into_batches_of_50
T006: test_prefetch_isrc_data_logs_warning_and_continues_on_batch_failure
T007: test_prefetch_isrc_data_skips_null_items_with_debug_log
```

### US1 + US2 Tests (T009–T010, T012) — write all in parallel

```
T009: test_match_list_with_embed_matches_calls_prefetch_once_per_batch
T010: test_match_list_with_embed_matches_skips_prefetch_when_isrc_cached
T012: test_match_list_without_embed_matches_never_calls_batch_endpoint
```

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational tests + `_prefetch_isrc_data` (T002–T008)
3. Complete Phase 3: US1 tests + `match_list` restructure (T009–T011)
4. **STOP AND VALIDATE**: run `uv run pytest tests/matchers/` → all pass
5. Run quality gates (T013–T016)

### Incremental Delivery

- After Phase 3: US1 fully functional (`embed_matches=True` is optimised)
- After Phase 4: US2 verified (no-embed path confirmed clean)
- After Final Phase: feature branch ready for review
