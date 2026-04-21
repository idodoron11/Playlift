# Feature Specification: Decouple Playlist from SyncTarget (ISP / LSP Fix)

**Feature Branch**: `005-decouple-playlist-synctarget`  
**Created**: 2026-04-21  
**Status**: Draft  
**Input**: User description: "Introduce SyncTarget ABC to decouple Playlist from Matcher — LSP and ISP fix"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Developer: LocalPlaylist no longer carries a dead matcher stub (Priority: P1)

A developer reading or extending `LocalPlaylist` must not encounter a method that raises `TypeError` at runtime. The class should only declare contracts it fulfills.

**Why this priority**: This is the root LSP violation. It is the clearest observable breakage and the most likely to mislead future contributors.

**Independent Test**: After the change, confirm `LocalPlaylist` has no `track_matcher` attribute and no `Matcher` import. Confirm `mypy` reports no LSP or override errors for `LocalPlaylist`.

**Acceptance Scenarios**:

1. **Given** the codebase after refactoring, **When** a developer inspects `LocalPlaylist`, **Then** there is no `track_matcher()` method and no import of `Matcher`.
2. **Given** a type checker runs against the codebase, **When** it checks `LocalPlaylist`, **Then** no LSP violation is reported and `LocalPlaylist` is a valid concrete `Playlist` with no unimplemented abstract methods.
3. **Given** code typed as `Playlist`, **When** passed a `LocalPlaylist` instance, **Then** it works correctly and `track_matcher()` is not accessible through the `Playlist` interface.

---

### User Story 2 — Developer: SyncTarget is a distinct, explicit contract (Priority: P1)

A developer implementing a new sync-capable playlist (e.g., a future `AppleMusicPlaylist`) should find a clear, named interface to implement — separate from the basic playlist contract.

**Why this priority**: This is the positive outcome of the ISP fix: the abstraction becomes intentional and reusable, not accidental.

**Independent Test**: Confirm `SyncTarget` exists as a standalone ABC in `playlists/__init__.py` with a single abstract method `track_matcher()`. Confirm `SpotifyPlaylist` declares it as a base class alongside `Playlist`.

**Acceptance Scenarios**:

1. **Given** the refactored `playlists/__init__.py`, **When** a developer looks for the sync-target contract, **Then** they find `class SyncTarget(ABC)` with `@staticmethod @abstractmethod track_matcher() -> Matcher`.
2. **Given** `SpotifyPlaylist`'s class definition, **When** inspected, **Then** it explicitly declares both `Playlist` and `SyncTarget` as base classes.
3. **Given** code typed as `SyncTarget`, **When** it calls `track_matcher()`, **Then** mypy accepts the call without errors.

---

### User Story 3 — Developer: All existing runtime behavior is preserved (Priority: P2)

The `spotify import`, `spotify sync`, and playlist comparison commands continue to work identically after the refactoring. No functional logic changes in any direction.

**Why this priority**: A refactoring that breaks behavior is not a refactoring. Runtime correctness is a constraint, not a goal.

**Independent Test**: Run the full test suite; all existing tests pass without modification to any test assertion.

**Acceptance Scenarios**:

1. **Given** the refactored codebase, **When** the full test suite runs, **Then** all tests pass with no failures or errors.
2. **Given** `SpotifyPlaylist.track_matcher()`, **When** called, **Then** it returns `SpotifyMatcher.get_instance()` exactly as before.
3. **Given** `SpotifyPlaylist.create_from_another_playlist()` and `import_tracks()`, **When** called, **Then** they invoke `track_matcher()` and produce the same results as before.

---

### User Story 4 — Developer: Test doubles reflect the new contract (Priority: P2)

`PlaylistMock` is a test double for `Playlist`. Since `Playlist` no longer declares `track_matcher()`, `PlaylistMock` must not implement it either. Tests that need matcher behavior should use `SpotifyPlaylist` mocks or inject a matcher explicitly.

**Why this priority**: Stale test doubles create a false sense of coverage and can hide the real contract from future contributors.

**Independent Test**: After the change, `PlaylistMock` has no `track_matcher()` method and no orphaned imports. All tests using `PlaylistMock` continue to pass without modification.

**Acceptance Scenarios**:

1. **Given** `tests/playlists/playlist_mock.py`, **When** inspected, **Then** it contains no `track_matcher()` method, no `Matcher` import, and no `MatcherMock` import.
2. **Given** all tests that use `PlaylistMock`, **When** they run, **Then** they pass without errors or modifications to test assertions.

---

### Edge Cases

- A class that inherits from `Playlist` but not `SyncTarget` must **not** be required to implement `track_matcher()` — mypy must confirm this is not an error.
- A class that inherits from `SyncTarget` but not `Playlist` must satisfy only the `track_matcher()` contract — the design must support this even if no such class currently exists.
- `patch.object(SpotifyPlaylist, "track_matcher", ...)` in existing tests must continue to work after `track_matcher()` moves from the `Playlist` contract to `SyncTarget`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `Playlist` ABC MUST NOT declare `track_matcher()` as an abstract method after this change.
- **FR-002**: A new `SyncTarget` ABC MUST be introduced in `playlists/__init__.py` and MUST declare `@staticmethod @abstractmethod track_matcher() -> Matcher`.
- **FR-003**: `SpotifyPlaylist` MUST declare both `Playlist` and `SyncTarget` as base classes.
- **FR-004**: `LocalPlaylist` MUST NOT implement `track_matcher()` and MUST NOT import `Matcher`.
- **FR-005**: `PlaylistMock` MUST NOT implement `track_matcher()` and MUST NOT import `Matcher` or `MatcherMock`.
- **FR-006**: The body of `SpotifyPlaylist.track_matcher()` MUST remain unchanged — it returns `SpotifyMatcher.get_instance()`.
- **FR-007**: All existing call sites of `track_matcher()` (inside `spotify_playlist.py` and `main.py`) MUST continue to function correctly without modification.
- **FR-008**: The full test suite MUST pass after all changes with no test assertions modified.
- **FR-009**: The type checker MUST report zero errors after all changes.
- **FR-010**: The linter MUST report zero errors after all changes.

### Key Entities

- **`Playlist` (ABC)**: Represents any ordered collection of tracks with add/remove capabilities. Does not know about matching or sync destinations.
- **`SyncTarget` (ABC)**: Represents a platform that tracks can be matched and synced *into*. Declares `track_matcher()` as the single point of entry for match resolution. **Fully orthogonal to `Playlist` and `TrackCollection`** — no inheritance relationship between them.
- **`SpotifyPlaylist`**: Implements both `Playlist` (track collection) and `SyncTarget` (matchable Spotify destination).
- **`LocalPlaylist`**: Implements `Playlist` only — a read/write local m3u file; no sync destination concept.
- **`PlaylistMock`**: Test double for `Playlist` only — must reflect the trimmed `Playlist` contract, not `SyncTarget`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Type checker exits with code 0 (`uv run mypy .` passes) — zero new errors introduced.
- **SC-002**: Linter exits with code 0 (`uv run ruff check .` passes) — zero new errors introduced.
- **SC-003**: All existing tests pass without modifying any test assertion (`uv run pytest tests/` exits with code 0).
- **SC-004**: `LocalPlaylist` source file contains zero references to `Matcher`, `MatcherMock`, or `track_matcher`.
- **SC-005**: `SyncTarget` is importable from `playlists` and is an abstract base class with exactly one abstract method (`track_matcher`).
- **SC-006**: `SpotifyPlaylist`'s class declaration includes both `Playlist` and `SyncTarget` as base classes — verified by mypy and code inspection; no new test assertion required.
- **SC-007**: No new test files are required and no existing test assertions are modified — the refactoring is fully validated by the existing test suite plus the type checker and linter.

## Clarifications

### Session 2026-04-21

- Q: Should `SyncTarget` be fully orthogonal to `Playlist`/`TrackCollection`, or should it extend one of them? → A: Fully orthogonal — `SyncTarget` is a standalone ABC with no inheritance relationship to `Playlist` or `TrackCollection`.
- Q: Should the `SyncTarget` type relationship be verified by an automated test assertion, or is mypy + code inspection sufficient? → A: mypy + code inspection sufficient — no new test assertions required.

## Assumptions

- This refactoring is purely structural — no runtime behavior changes for any existing feature or CLI command.
- `PlaylistMock.track_matcher()` is never called directly by any test (confirmed by codebase inspection); removing it does not break any test assertion.
- `patch.object(SpotifyPlaylist, "track_matcher", ...)` in `test_spotify_playlist.py` remains valid because `track_matcher` continues to exist on `SpotifyPlaylist` — it is simply declared via the `SyncTarget` base class rather than `Playlist`.
- No code outside the four modified files references `track_matcher()` through a `Playlist`-typed variable (confirmed by codebase inspection).
- `SyncTarget` is placed in `playlists/__init__.py` for consistency with `Playlist` and `TrackCollection` — no new module file is introduced.
