---

description: "Task list for 002-fix-isrc-mp4-bugs"
---

# Tasks: Fix Three M4A ISRC Tag Bugs

**Input**: Design documents from `/specs/002-fix-isrc-mp4-bugs/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Extract the repeated iTunes freeform prefix literal into a named constant before touching any bug-specific logic. This is a prerequisite for all three bug fixes and must be done first to avoid introducing it multiple times.

- [X] T001 Extract `_ITUNES_FREEFORM_PREFIX = "----:com.apple.iTunes:"` as a module-level constant in `tracks/local_track.py`, replacing the two existing inline string literals in `_get_custom_tag` and `_set_custom_tag`

---

## Phase 2: User Story 1 — M4A ISRC duplicate prevention (Priority: P1)

**Story goal**: An M4A file with a pre-existing lowercase-keyed ISRC atom (`----:com.apple.iTunes:isrc`) is not duplicated when `spotify match` runs.

**Independent test criteria**: After this phase, `TestLocalTrackIsrcGetterM4a` has a passing test that constructs a mock MP4 with a lowercase ISRC key and asserts the getter returns the value instead of `None`. A second test confirms the setter does not call `save()` when that key already exists.

- [X] T002 [US1] Write failing test `test_isrc_returns_value_from_lowercase_itunes_key` in `tests/tracks/test_local_track.py` — mock MP4 tags dict keyed as `----:com.apple.iTunes:isrc` (lowercase), assert `track.isrc == "USSM19604431"` (currently fails: returns `None`)
- [X] T003 [US1] Write failing test `test_isrc_setter_skips_write_when_lowercase_key_exists` in `tests/tracks/test_local_track.py` — same lowercase-keyed mock, call `track.isrc = "USSM19604431"`, assert `mock_mp4.save.assert_not_called()` (currently fails: save is called)
- [X] T004 [US1] Implement Bug 1 fix in `tracks/local_track.py`: add case-insensitive fallback scan in `_get_custom_tag` — when the exact-case key is not found in an MP4 tags dict, scan all keys for a case-insensitive match using `next(...)` before returning `None`
- [X] T005 [P] [US1] Verify T002 and T003 now pass: `uv run pytest tests/tracks/test_local_track.py -v`

---

## Phase 3: User Story 2 — ISRC comparison normalization (Priority: P2)

**Story goal**: A local track (M4A, MP3, or FLAC) with ISRC `"USSM19604431"` is not overwritten when Spotify returns `"USSM1-9604431"` (same value, different formatting) on any file format.

**Independent test criteria**: After this phase, `tests/matchers/test_spotify_matcher.py` has a passing test that mocks `_update_spotify_match_in_source_track` with a hyphenated Spotify ISRC and asserts the track setter is never invoked.

- [X] T006 [US2] Write failing test `test_update_match_skips_isrc_write_when_normalized_values_match` in `tests/matchers/test_spotify_matcher.py` — mock a `LocalTrack` with `isrc = "USSM19604431"` and a `SpotifyTrack` with `isrc = "USSM1-9604431"`, call `_update_spotify_match_in_source_track`, assert `source_track.isrc` setter is never called (currently fails: setter is invoked)
- [X] T007 [US2] Implement Bug 3 fix in `matchers/spotify_matcher.py`: import `_normalize_isrc` from `tracks.local_track` and change condition to `source_track.isrc != _normalize_isrc(match.isrc)` — skip write only when semantically equal, update otherwise
- [X] T008 [P] [US2] Verify T006 now passes: `uv run pytest tests/matchers/test_spotify_matcher.py -v`

---

## Phase 4: User Story 3 — MP4 freeform write type (Priority: P3)

**Story goal**: Custom tags written to M4A files are stored as proper `MP4FreeForm` objects with UTF-8 encoding, not raw `bytes`.

**Independent test criteria**: After this phase, `TestLocalTrackIsrcSetterM4a` has a passing test that captures the value written via `__setitem__` and asserts it is `list[MP4FreeForm]`, not `bytes`.

- [X] T009 [US3] Write failing test `test_isrc_setter_writes_mp4freeform_not_raw_bytes` in `tests/tracks/test_local_track.py` — capture the value passed to `mock_mp4.tags.__setitem__`, assert `isinstance(value, list)` and `all(isinstance(v, MP4FreeForm) for v in value)` (currently fails: value is `bytes`)
- [X] T010 [US3] Implement Bug 2 fix in `tracks/local_track.py`: add `MP4FreeForm` to the `from mutagen.mp4 import` line and change the M4A write in `_set_custom_tag` from `value.encode("utf-8")` to `[MP4FreeForm(value.encode("utf-8"))]`
- [X] T011 [P] [US3] Verify T009 now passes: `uv run pytest tests/tracks/test_local_track.py -v`

---

## Phase 5: Polish & Quality Gates

**Purpose**: Confirm all tests pass, types check out, and linting is clean.

- [X] T012 [P] Run full test suite and confirm no regressions: `uv run pytest tests/`
- [X] T013 [P] Run type checker: `uv run mypy .`
- [X] T014 [P] Run linter and formatter: `uv run ruff check . ; uv run ruff format .`

---

## Dependencies

```
T001 (constant extraction)
  └─► T002, T003 (Bug 1 failing tests)
        └─► T004 (Bug 1 fix)
              └─► T005 (verify Bug 1)

T006 (Bug 3 failing test) — independent of T001
  └─► T007 (Bug 3 fix)
        └─► T008 (verify Bug 3)

T009 (Bug 2 failing test) — independent of T001
  └─► T010 (Bug 2 fix)
        └─► T011 (verify Bug 2)

T005, T008, T011 → T012, T013, T014 (quality gates)
```

## Parallel Execution

**US1, US2, US3** are independent after T001 completes:

```
T001
├── T002 → T003 → T004 → T005
├── T006 → T007 → T008          (parallel with US1 after T001)
└── T009 → T010 → T011          (parallel with US1/US2 after T001)
```

Quality gates (T012–T014) run in parallel after all story phases complete.

## Implementation Strategy

**MVP scope**: T001 + US1 (T002–T005). This is the live-confirmed bug. US2 and US3 can follow independently.

**Recommended order**: US1 → US2 → US3 to match priority order and confirm the primary bug is fixed before addressing secondary issues.
