# Tasks: ISRC-Based Track Matching and Embedding

**Input**: Design documents from `/specs/001-isrc-track-matching/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: REQUIRED per Constitution Principle V — every concrete class MUST have unit tests covering core logic, edge cases, and regression scenarios.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

---

## Phase 1: Setup (Project Structure)

**Purpose**: No new directories or dependencies needed. This project uses `uv` for dependency management. Confirm environment is ready.

- [ ] T001 Verify `uv run pytest tests/` passes on current main before any changes (baseline)
- [ ] T002 Verify `uv run ruff check . && uv run ruff format --check . && uv run mypy .` all pass on current main

**Checkpoint**: Green baseline confirmed — no pre-existing failures.

---

## Phase 2: Foundational (Blocking Prerequisites for All User Stories)

**Purpose**: Core infrastructure that ALL user stories depend on. Must be complete before Phase 3+.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T003 Add module-level constant `ISRC_PATTERN: re.Pattern[str] = re.compile(r"^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$")` to `matchers/spotify_matcher.py` (explicit type annotation required; also ensure `import re` is present at module scope)
- [ ] T004 [P] Add `isrc: str | None` optional parameter to `TrackMock.__init__` and an `isrc` read-only property in `tests/tracks/track_mock.py`; `isrc` is deliberately excluded from `__eq__` and `__hash__` — `TrackMock` identity is based on `spotify_ref`, not ISRC; add an inline comment stating this
- [ ] T005 [P] Add read-only `isrc` property to `SpotifyTrack` reading `self.data.get("external_ids", {}).get("isrc")` in `tracks/spotify_track.py`
- [ ] T006 [P] Add `isrc` read property to `LocalTrack` in `tracks/local_track.py`: MP3 reads `TSRC` frame via mutagen, FLAC reads `"isrc"` key via music_tag, M4A reads `----:com.apple.iTunes:ISRC` freeform atom (verify `_get_custom_tag("ISRC")` maps to this atom); normalization (uppercase + strip hyphens) MUST be extracted as a module-level private helper `_normalize_isrc(raw: str) -> str` in `local_track.py` — do not inline the manipulation; return `None` if tag is absent or empty
- [ ] T007 Add `isrc` write property (setter) to `LocalTrack` in `tracks/local_track.py`: MP3 writes `mutagen.id3.TSRC` frame, FLAC writes via music_tag `"isrc"` key, M4A uses `_set_custom_tag("ISRC")`; only writes if current `isrc` is `None`

**Checkpoint**: Foundation ready — ISRC constant, track properties, and test infrastructure are all in place. User story phases can now begin.

---

## Phase 3: User Story 1 - ISRC-Based Track Matching (Priority: P1) 🎯 MVP

**Goal**: When a local track has a valid ISRC tag, look it up in Spotify's catalog first; skip fuzzy search entirely if the ISRC matches.

**Independent Test**: Run `uv run pytest tests/matchers/test_spotify_matcher.py -v -k "isrc"` on a playlist of ISRC-tagged tracks and verify fuzzy search is never invoked.

### Tests for User Story 1 (REQUIRED — write first, confirm fail, then implement)

> **Testing infrastructure (applies to all matcher tests in Phases 3–5)**: All tests MUST patch `SpotifyMatcher._search` using `unittest.mock.patch.object(SpotifyMatcher, "_search")` — no real Spotify API calls are permitted. `SpotifyMatcher` instances MUST either be constructed directly (bypassing `get_instance()`) or the singleton MUST be reset via `Matcher._instance = None` in setUp/teardown to prevent state leakage between tests.

- [ ] T008 [P] [US1] Add test `test_match_uses_isrc_lookup_when_valid_isrc_present` to `tests/matchers/test_spotify_matcher.py`: use concrete ISRC `"USRC17607839"` on the track; patch `SpotifyMatcher._search` via `unittest.mock.patch.object` as a spy that returns a result for ISRC queries; assert `_search` is called exactly once with argument `"isrc:USRC17607839"` and no call contains a title/artist/album query
- [ ] T009 [P] [US1] Add test `test_match_returns_isrc_result_directly` to `tests/matchers/test_spotify_matcher.py`: stub `_search("isrc:...")` returning one `SpotifyTrack`; assert `match()` returns that track
- [ ] T010 [P] [US1] Add test `test_match_skips_isrc_lookup_for_malformed_isrc` to `tests/matchers/test_spotify_matcher.py`: track with `isrc="NOTVALID"`; assert `_search` is never called with `"isrc:"` prefix
- [ ] T011 [P] [US1] Add test `test_match_skips_isrc_lookup_when_no_isrc_tag` to `tests/matchers/test_spotify_matcher.py`: track with `isrc=None`; assert `_search` is not called with `"isrc:"` prefix (focuses on ISRC path being skipped; see T019 for verifying fuzzy path is invoked instead)
- [ ] T012 [P] [US1] Add tests for `LocalTrack.isrc` getter: mp3 with `TSRC` frame, FLAC with Vorbis `ISRC` comment, M4A with iTunes freeform tag, absent tag, mixed-case normalization, hyphenated form in `tests/tracks/test_local_track.py`; tests MUST patch `mutagen.mp3.MP3.__init__`, `mutagen.flac.FLAC.__init__`, and `mutagen.mp4.MP4.__init__` (or inject a stub `MutagenFileType`) to provide a fake tags dict — no real file I/O permitted
- [ ] T013 [P] [US1] Add test for `SpotifyTrack.isrc`: data with `external_ids.isrc`, data without `external_ids`, `external_ids` present but no `isrc` key in `tests/tracks/test_spotify_track.py`
- [ ] T031 [P] [US1] Add test `test_match_via_isrc_for_non_latin_track` to `tests/matchers/test_spotify_matcher.py`: track with Cyrillic/CJK artist/title metadata and a valid ISRC; assert ISRC lookup is used and match succeeds without fuzzy search (SC-002, constitution §V non-Latin mandate)
- [ ] T032 [P] [US1] Add test `test_match_logs_isrc_method_when_matched_via_isrc` to `tests/matchers/test_spotify_matcher.py`: valid ISRC match succeeds; assert log output contains indication that match was via ISRC (FR-008)
- [ ] T033 [P] [US2] Add test `test_match_logs_fuzzy_method_when_fallback_used` to `tests/matchers/test_spotify_matcher.py`: ISRC absent or lookup empty, fuzzy match succeeds; assert log output contains indication that match was via fuzzy search (FR-008)
- [ ] T034 [P] [US1] Add isolated unit tests for `_is_valid_isrc()` directly in `tests/matchers/test_spotify_matcher.py` — invoke the function without calling `match()`: `"USRC17607839"` → `True`; wrong length `"USRC176078"` (10 chars) → `False`; lowercase `"usrc17607839"` → `False` (normalization is the getter's responsibility; validator receives already-normalized input); `None` → `False`; empty string `""` → `False`; hyphenated `"US-RC1-76-07839"` → `False` (hyphens not stripped by validator)

### Implementation for User Story 1

- [ ] T014 [US1] Add ISRC validation helper `_is_valid_isrc(isrc: str | None) -> bool` using `ISRC_PATTERN` to `matchers/spotify_matcher.py`
- [ ] T015 [US1] Add ISRC-first lookup block to `SpotifyMatcher.match()` in `matchers/spotify_matcher.py`: after checking `spotify_ref` but before fuzzy search; call `_search(f"isrc:{isrc}")` if `_is_valid_isrc(track.isrc)` and return first result if found; `SpotifyTrack.isrc` is sourced from `data` already present in the `_search()` response — no second API call is made; log match method at `INFO` level (FR-008)
- [ ] T016 [US1] Handle API/network errors in ISRC lookup block in `matchers/spotify_matcher.py`: prefer `except (spotipy.exceptions.SpotifyException, requests.exceptions.RequestException)` for the known failure modes; `except Exception` is acceptable if additional exception types share the same fallback handling, provided the caught exception is always logged as a warning; bare `except:` is PROHIBITED per Constitution §I; fall through to fuzzy search on any caught exception (FR-004)

**Checkpoint**: User Story 1 fully functional. Tracks with valid ISRC tags are matched without fuzzy search. Malformed/absent ISRC correctly falls through. All US1 tests pass.

---

## Phase 4: User Story 2 - Fuzzy Search Fallback (Priority: P2)

**Goal**: Verify no regression in existing fuzzy matching for tracks without ISRC tags. All pre-existing behavior is preserved.

**Independent Test**: Run `uv run pytest tests/matchers/test_spotify_matcher.py -v -k "fuzzy or fallback or no_isrc"` — all existing and new fallback tests pass.

### Tests for User Story 2 (REQUIRED — write first, confirm fail, then implement)

- [ ] T017 [P] [US2] Add test `test_match_falls_back_to_fuzzy_when_isrc_lookup_returns_empty` to `tests/matchers/test_spotify_matcher.py`: valid ISRC, patch `SpotifyMatcher._search` via `unittest.mock.patch.object`; configure ISRC call to return `[]` and fuzzy call to return a result; assert `call_args_list` contains both an ISRC query followed by a fuzzy query (also covers the regional-market-unavailable edge case from spec)
- [ ] T018 [P] [US2] Add test `test_match_falls_back_to_fuzzy_on_api_error_during_isrc_lookup` to `tests/matchers/test_spotify_matcher.py`: valid ISRC, `_search("isrc:...")` raises exception; assert fallback to fuzzy and warning is logged
- [ ] T019 [P] [US2] Add test `test_match_without_isrc_invokes_only_fuzzy_search` to `tests/matchers/test_spotify_matcher.py`: track with `isrc=None`; assert fuzzy `_search` **is** invoked with title/artist/album query and no `"isrc:"` prefix appears in any call (complements T011 which only asserts the ISRC path is skipped)
- [ ] T020 [P] [US2] Confirm all pre-existing `test_spotify_matcher.py` tests still pass unchanged after Phase 3 changes (regression check task — no new code, just run + verify)
- [ ] T035 [P] [US1, US2, US3] Add test `test_match_list_handles_mixed_isrc_no_isrc_and_skip_tracks` to `tests/matchers/test_spotify_matcher.py`: call `match_list()` with 3 `TrackMock` instances — one with `isrc="USRC17607839"` (expect ISRC lookup), one with `isrc=None` (expect fuzzy search), one with `spotify_ref="SKIP"` (expect no lookup); patch `SpotifyMatcher._search` and inspect `call_args_list` to confirm ISRC query fires for track 1, fuzzy query fires for track 2, nothing fires for track 3; assert 2 tracks in the returned matched list

### Implementation for User Story 2

No new implementation needed. Fallback paths are already wired in T015–T016 (Phase 3). This phase is purely test validation.

**Checkpoint**: Backward compatibility confirmed. Tracks without ISRC match identically to before. All fallback tests pass alongside US1 tests.

---

## Phase 5: User Story 3 - ISRC Embedding After Match (Priority: P3)

**Goal**: After a successful match, write the Spotify track's ISRC back to the local file's tags if not already present. Gated by `--embed-matches` for `import`/`sync`; always active for `match`.

**Independent Test**: Run `uv run pytest tests/matchers/test_spotify_matcher.py -k "embed_isrc"` and separately check that `LocalTrack.isrc` setter writes correctly for each audio format.

### Tests for User Story 3 (REQUIRED — write first, confirm fail, then implement)

- [ ] T021 [P] [US3] Add test `test_embed_isrc_writes_isrc_to_local_track_after_match` to `tests/matchers/test_spotify_matcher.py`: track has no ISRC, match found, `embed_matches=True`; assert `local_track.isrc` is set to the Spotify track's ISRC
- [ ] T022 [P] [US3] Add test `test_embed_isrc_does_not_overwrite_existing_isrc` to `tests/matchers/test_spotify_matcher.py`: track already has ISRC tag; assert it is unchanged after match (FR-006)
- [ ] T023 [P] [US3] Add test `test_embed_isrc_skipped_when_embed_matches_false` to `tests/matchers/test_spotify_matcher.py`: `embed_matches=False`; assert `local_track.isrc` setter is never called
- [ ] T024 [P] [US3] Add test `test_embed_isrc_skipped_when_spotify_track_has_no_isrc` to `tests/matchers/test_spotify_matcher.py`: matched `SpotifyTrack.isrc` is `None`; assert `LocalTrack.isrc` setter is never invoked — use `unittest.mock.PropertyMock` on the `isrc` property and assert the setter's `call_count` is zero (no empty tag written)
- [ ] T025 [P] [US3] Add test `test_embed_isrc_skipped_for_skip_track` to `tests/matchers/test_spotify_matcher.py`: track marked SKIP; assert ISRC setter never called
- [ ] T026 [P] [US3] Add tests for `LocalTrack.isrc` setter: mp3 writes `TSRC` frame, FLAC writes Vorbis comment, M4A writes iTunes freeform tag, write failure (mocked OSError) logs warning and does not raise in `tests/tracks/test_local_track.py`; all tests MUST mock `MP3.save()`, `FLAC.save()`, and `MP4.save()` to prevent real filesystem writes; for success paths, assert `save()` is called exactly once

### Implementation for User Story 3

- [ ] T027 [US3] Extend `SpotifyMatcher._update_spotify_match_in_source_track()` in `matchers/spotify_matcher.py` to also write `source_track.isrc = match.isrc` when `match.isrc` is not `None` and `source_track.isrc` is `None`; add `isinstance(source_track, LocalTrack)` guard before the ISRC write — non-`LocalTrack` tracks lack the setter and MUST be skipped silently; add test `test_embed_isrc_skipped_for_non_local_track` asserting no `AttributeError` or write occurs when `source_track` is a `TrackMock`

**Checkpoint**: All three user stories complete and independently testable. ISRC embedding works per-format and respects no-overwrite and embed-gating rules.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Quality gates, logging completeness, and documentation.

- [ ] T028 [P] Add Google-style docstrings to all new/modified public properties and methods: `LocalTrack.isrc`, `SpotifyTrack.isrc`, `SpotifyMatcher._is_valid_isrc`, the ISRC lookup block in `match()`
- [ ] T029 [P] Run full quality gate: `uv run ruff format .`, `uv run ruff check .`, `uv run mypy .`, `uv run pytest tests/` — all must pass with zero errors
- [ ] T030 Update `specs/001-isrc-track-matching/checklists/requirements.md` — re-run all checklist items against final implementation

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
  └─→ Phase 2 (Foundational) — BLOCKS all user stories
        ├─→ Phase 3 (US1 - ISRC Matching) — MVP deliverable
        ├─→ Phase 4 (US2 - Fuzzy Fallback) — depends on Phase 3 implementation being present
        └─→ Phase 5 (US3 - Embedding) — depends on Phase 3 (needs match() wired first)
              └─→ Phase 6 (Polish)
```

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 2 only. Start here for MVP.
- **US2 (P2)**: Depends on Phase 3 implementation being present (tests the fallback paths of US1 changes).
- **US3 (P3)**: Depends on Phase 3 (match() must exist before embedding can be wired).

### Parallel Opportunities per Story

**Phase 2** (after T003): T004, T005, T006 can run in parallel (different files).

**Phase 3 tests** (T008–T013, T031–T032, T034): All 9 test tasks are parallelizable (different test scenarios). T033 and T035 (Phase 4) are also independently parallelizable with the US2 tests.

**Phase 3 implementation** (T014–T016): Sequential — T014 validator needed before T015 lookup, T016 follows T015.

**Phase 5 tests** (T021–T026): All 6 test tasks are parallelizable.

---

## Implementation Strategy

**Suggested MVP delivery**: Complete Phase 2 + Phase 3 only (US1 - ISRC Matching).

This alone delivers 100% of the core feature value: tracks with ISRC tags are matched deterministically without fuzzy search. US2 and US3 add robustness confirmation and the compounding embedding benefit.

**TDD order per phase**: Write tests first (confirm they fail) → implement → confirm tests pass → run quality gates.
