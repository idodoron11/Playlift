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

- [ ] T003 Add module-level constant `ISRC_PATTERN = re.compile(r"^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$")` to `matchers/spotify_matcher.py`
- [ ] T004 [P] Add `isrc: str | None` optional parameter to `TrackMock.__init__` and an `isrc` read-only property in `tests/tracks/track_mock.py`
- [ ] T005 [P] Add read-only `isrc` property to `SpotifyTrack` reading `self.data.get("external_ids", {}).get("isrc")` in `tracks/spotify_track.py`
- [ ] T006 [P] Add `isrc` read property to `LocalTrack` in `tracks/local_track.py`: MP3 reads `TSRC` frame via mutagen, FLAC reads `"isrc"` key via music_tag, M4A uses `_get_custom_tag("ISRC")`; normalize to uppercase and strip hyphens; return `None` if absent
- [ ] T007 Add `isrc` write property (setter) to `LocalTrack` in `tracks/local_track.py`: MP3 writes `mutagen.id3.TSRC` frame, FLAC writes via music_tag `"isrc"` key, M4A uses `_set_custom_tag("ISRC")`; only writes if current `isrc` is `None`

**Checkpoint**: Foundation ready — ISRC constant, track properties, and test infrastructure are all in place. User story phases can now begin.

---

## Phase 3: User Story 1 - ISRC-Based Track Matching (Priority: P1) 🎯 MVP

**Goal**: When a local track has a valid ISRC tag, look it up in Spotify's catalog first; skip fuzzy search entirely if the ISRC matches.

**Independent Test**: Run `uv run pytest tests/matchers/test_spotify_matcher.py -v -k "isrc"` on a playlist of ISRC-tagged tracks and verify fuzzy search is never invoked.

### Tests for User Story 1 (REQUIRED — write first, confirm fail, then implement)

- [ ] T008 [P] [US1] Add test `test_match_uses_isrc_lookup_when_valid_isrc_present` to `tests/matchers/test_spotify_matcher.py`: mock `_search` to capture calls; assert it is called with `"isrc:XXXXXXXXXXXX"` and fuzzy search is never called
- [ ] T009 [P] [US1] Add test `test_match_returns_isrc_result_directly` to `tests/matchers/test_spotify_matcher.py`: stub `_search("isrc:...")` returning one `SpotifyTrack`; assert `match()` returns that track
- [ ] T010 [P] [US1] Add test `test_match_skips_isrc_lookup_for_malformed_isrc` to `tests/matchers/test_spotify_matcher.py`: track with `isrc="NOTVALID"`; assert `_search` is never called with `"isrc:"` prefix
- [ ] T011 [P] [US1] Add test `test_match_skips_isrc_lookup_when_no_isrc_tag` to `tests/matchers/test_spotify_matcher.py`: track with `isrc=None`; assert `_search` is not called with `"isrc:"` prefix
- [ ] T012 [P] [US1] Add tests for `LocalTrack.isrc` getter: mp3 with `TSRC` frame, FLAC with Vorbis `ISRC` comment, M4A with iTunes freeform tag, absent tag, mixed-case normalization, hyphenated form in `tests/tracks/test_local_track.py`
- [ ] T013 [P] [US1] Add test for `SpotifyTrack.isrc`: data with `external_ids.isrc`, data without `external_ids`, `external_ids` present but no `isrc` key in `tests/tracks/test_spotify_track.py`

### Implementation for User Story 1

- [ ] T014 [US1] Add ISRC validation helper `_is_valid_isrc(isrc: str | None) -> bool` using `ISRC_PATTERN` to `matchers/spotify_matcher.py`
- [ ] T015 [US1] Add ISRC-first lookup block to `SpotifyMatcher.match()` in `matchers/spotify_matcher.py`: after checking `spotify_ref` but before fuzzy search; call `_search(f"isrc:{isrc}")` if `_is_valid_isrc(track.isrc)` and return first result if found; log method used (FR-008)
- [ ] T016 [US1] Handle API/network errors in ISRC lookup block in `matchers/spotify_matcher.py`: wrap the `_search` call in try/except, log warning on exception, fall through to fuzzy search (FR-004)

**Checkpoint**: User Story 1 fully functional. Tracks with valid ISRC tags are matched without fuzzy search. Malformed/absent ISRC correctly falls through. All US1 tests pass.

---

## Phase 4: User Story 2 - Fuzzy Search Fallback (Priority: P2)

**Goal**: Verify no regression in existing fuzzy matching for tracks without ISRC tags. All pre-existing behavior is preserved.

**Independent Test**: Run `uv run pytest tests/matchers/test_spotify_matcher.py -v -k "fuzzy or fallback or no_isrc"` — all existing and new fallback tests pass.

### Tests for User Story 2 (REQUIRED — write first, confirm fail, then implement)

- [ ] T017 [P] [US2] Add test `test_match_falls_back_to_fuzzy_when_isrc_lookup_returns_empty` to `tests/matchers/test_spotify_matcher.py`: valid ISRC, `_search("isrc:...")` returns `[]`; assert fuzzy search is then invoked
- [ ] T018 [P] [US2] Add test `test_match_falls_back_to_fuzzy_on_api_error_during_isrc_lookup` to `tests/matchers/test_spotify_matcher.py`: valid ISRC, `_search("isrc:...")` raises exception; assert fallback to fuzzy and warning is logged
- [ ] T019 [P] [US2] Add test `test_match_without_isrc_invokes_only_fuzzy_search` to `tests/matchers/test_spotify_matcher.py`: track with `isrc=None`; assert only fuzzy `_search` is called (no `"isrc:"` prefix at all)
- [ ] T020 [P] [US2] Confirm all pre-existing `test_spotify_matcher.py` tests still pass unchanged after Phase 3 changes (regression check task — no new code, just run + verify)

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
- [ ] T024 [P] [US3] Add test `test_embed_isrc_skipped_when_spotify_track_has_no_isrc` to `tests/matchers/test_spotify_matcher.py`: matched `SpotifyTrack.isrc` is `None`; assert no write attempt (no empty tag written)
- [ ] T025 [P] [US3] Add test `test_embed_isrc_skipped_for_skip_track` to `tests/matchers/test_spotify_matcher.py`: track marked SKIP; assert ISRC setter never called
- [ ] T026 [P] [US3] Add tests for `LocalTrack.isrc` setter: mp3 writes `TSRC` frame, FLAC writes Vorbis comment, M4A writes iTunes freeform tag, write failure (mocked OSError) logs warning and does not raise in `tests/tracks/test_local_track.py`

### Implementation for User Story 3

- [ ] T027 [US3] Extend `SpotifyMatcher._update_spotify_match_in_source_track()` in `matchers/spotify_matcher.py` to also write `source_track.isrc = match.isrc` when `match.isrc` is not `None` and `source_track.isrc` is `None`

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

**Phase 3 tests** (T008–T013): All 6 test tasks are parallelizable (different test scenarios).

**Phase 3 implementation** (T014–T016): Sequential — T074 validator needed before T015 lookup, T016 follows T015.

**Phase 5 tests** (T021–T026): All 6 test tasks are parallelizable.

---

## Implementation Strategy

**Suggested MVP delivery**: Complete Phase 2 + Phase 3 only (US1 - ISRC Matching).

This alone delivers 100% of the core feature value: tracks with ISRC tags are matched deterministically without fuzzy search. US2 and US3 add robustness confirmation and the compounding embedding benefit.

**TDD order per phase**: Write tests first (confirm they fail) → implement → confirm tests pass → run quality gates.
