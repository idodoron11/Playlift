# Tasks: Decouple Playlist from SyncTarget (ISP / LSP Fix)

**Input**: Design documents from `/specs/005-decouple-playlist-synctarget/`
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ quickstart.md ✅

**Tests**: No new test tasks per spec SC-007 — the refactoring is validated entirely by the existing test suite, mypy, and ruff. No test assertions are modified.

**Organization**: 4 user stories → Foundational (US2 blocks all others) + 2 parallel cleanup phases (US1, US4) + validation (US3).

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1–US4 as defined in spec.md
- All paths are relative to repository root

---

## Phase 2: Foundational — Introduce SyncTarget ABC (US2 — P1) 🎯 MVP

**Goal**: Add `SyncTarget` as a standalone ABC in `playlists/__init__.py` and wire `SpotifyPlaylist` to it. This is the atomic prerequisite for all other user stories.

**Independent Test**: After T001 + T002, `uv run mypy .` exits with code 0 and `SyncTarget` is importable from `playlists`. `SpotifyPlaylist` inherits both `Playlist` and `SyncTarget`.

- [X] T001 [US2] Add `class SyncTarget(ABC)` with `@staticmethod @abstractmethod track_matcher() -> Matcher` and remove `track_matcher()` from `class Playlist` in `playlists/__init__.py`
- [X] T002 [US2] Change `class SpotifyPlaylist(Playlist)` to `class SpotifyPlaylist(Playlist, SyncTarget)` and add `SyncTarget` to the import from `playlists` in `playlists/spotify_playlist.py`

**Checkpoint**: `playlists` module exports `SyncTarget`; `SpotifyPlaylist` declares both base classes; `mypy` confirms zero errors on `playlists/` and `playlists/spotify_playlist.py`.

---

## Phase 3: User Story 1 — LocalPlaylist Cleanup (Priority: P1)

**Goal**: Remove the LSP-violating `track_matcher()` stub and orphaned `Matcher` import from `LocalPlaylist`, leaving it as a clean `Playlist`-only concrete class.

**Independent Test**: `LocalPlaylist` source file contains zero references to `Matcher` or `track_matcher` (SC-004). `mypy` reports `LocalPlaylist` as a valid concrete `Playlist` with no unimplemented abstract methods.

- [X] T003 [P] [US1] Remove `track_matcher()` static method and `from matchers import Matcher` import from `playlists/local_playlist.py`

**Checkpoint**: `LocalPlaylist` implements only `Playlist`; no `track_matcher` attribute; `mypy` reports no LSP violations.

---

## Phase 4: User Story 4 — PlaylistMock Cleanup (Priority: P2)

**Goal**: Remove the now-stale `track_matcher()` implementation and its two orphaned imports from `PlaylistMock` so it accurately reflects the trimmed `Playlist` contract.

**Independent Test**: `tests/playlists/playlist_mock.py` contains no `track_matcher()` method, no `Matcher` import, and no `MatcherMock` import (spec US4 acceptance scenario 1).

- [X] T004 [P] [US4] Remove `track_matcher()` static method, `from matchers import Matcher`, and `from tests.matchers.matcher_mock import MatcherMock` from `tests/playlists/playlist_mock.py`

**Checkpoint**: `PlaylistMock` is a clean `Playlist`-only test double; no orphaned imports; existing tests that use it continue to compile.

> **Note**: Phase 3 (T003) and Phase 4 (T004) touch different files with no shared dependency — they can be implemented in parallel after Phase 2 completes.

---

## Phase 5: User Story 3 — Validate Behavior Preservation (Priority: P2)

**Goal**: Confirm that all quality gates pass and zero existing behavior has changed.

**Independent Test**: All four commands exit with code 0.

- [X] T005 Run `uv run mypy .` and confirm zero errors — validates SC-001 and SC-005/SC-006
- [X] T006 [P] Run `uv run ruff check .` and confirm zero lint errors — validates SC-002
- [X] T007 [P] Run `uv run pytest tests/` and confirm all existing tests pass without modification — validates SC-003 and SC-007

**Checkpoint**: Feature complete. All success criteria SC-001 through SC-007 verified.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 2)**: No dependencies — start immediately. BLOCKS all other phases.
- **US1 (Phase 3)**: Depends on Phase 2 completion. `Playlist` must no longer declare `track_matcher()` before removing it from `LocalPlaylist`.
- **US4 (Phase 4)**: Depends on Phase 2 completion. Same reason as US1. **Can run in parallel with Phase 3** (different files).
- **US3/Polish (Phase 5)**: Depends on Phase 3 and Phase 4 both being complete.

### User Story Dependencies

- **US2 (P1, Foundational)**: No dependencies — start immediately
- **US1 (P1)**: Depends on US2 — cannot remove the stub until `Playlist` no longer declares the abstract method
- **US4 (P2)**: Depends on US2 — same reason; can run in parallel with US1
- **US3 (P2)**: Depends on US1 + US4 — validation of the completed state

### Within Each Phase

- T001 before T002 (T002 imports `SyncTarget` which T001 defines)
- T003 and T004 are independent of each other — parallel opportunity
- T005, T006, T007: T005 first to catch type errors early; T006 and T007 can run in parallel after T005

---

## Parallel Execution

### Suggested Parallel Batches

```bash
# Batch 1 — Foundational (sequential within batch)
T001 → T002

# Batch 2 — Parallel cleanup (after Batch 1 completes)
T003 || T004

# Batch 3 — Parallel validation (after Batch 2 completes)
T005 → (T006 || T007)
```

### Parallel Example: Phase 3 + Phase 4

```bash
# In two terminals simultaneously after Phase 2 is done:
# Terminal 1:
# Edit playlists/local_playlist.py (T003)

# Terminal 2:
# Edit tests/playlists/playlist_mock.py (T004)
```

---

## Implementation Strategy

**MVP Scope**: T001 + T002 (Phase 2) alone constitutes a deliverable increment — it introduces `SyncTarget`, satisfies US2 (the ISP goal), and leaves the codebase in a consistent state (mypy passes). T003 and T004 are clean-up steps that complete the picture.

**Incremental Delivery**:
1. **Commit 1** (T001 + T002): `refactor: introduce SyncTarget ABC, decouple from Playlist`
2. **Commit 2** (T003): `refactor: remove track_matcher stub from LocalPlaylist`
3. **Commit 3** (T004): `refactor: remove track_matcher stub from PlaylistMock`
4. **Commit 4** (T005–T007): `chore: verify all quality gates pass`

**Total tasks**: 7 | **Parallel opportunities**: 4 | **Estimated lines changed**: ~15
