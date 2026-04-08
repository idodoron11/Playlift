# Tasks: Remove SpotifyAPI Singleton — Constructor Injection Refactor

**Input**: Design documents from `/specs/004-remove-spotifyapi-di/`
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ quickstart.md ✅

**Tests**: Required per Constitution Principle V. All test tasks rewrite or add tests using
constructor injection — no `patch("...SpotifyAPI")`, no `SpotifyTrack.__new__`, no singleton
reset hacks.

**Skill applied**: refactor — surgical changes preserving production behaviour.

---

## Phase 1: Setup — Remove `SpotifyAPI`, expose `get_spotify_client()`

**Purpose**: Replace the singleton class with a `@functools.cache` function. This is the
composition root that all downstream classes depend on. Must complete before Phases 2–4.

**⚠️ CRITICAL**: All user story phases depend on this phase. No other implementation can
begin until T001 is complete.

- [X] T001 Rewrite `api/spotify.py`: delete `SpotifyAPI` class; add `@functools.cache def get_spotify_client() -> spotipy.Spotify` with Google docstring; add `import functools`; keep `SpotifyOAuth` scopes and `retries=0` comment unchanged

**Checkpoint**: `api/spotify.py` exports `get_spotify_client`; `SpotifyAPI` is gone. All
other files will still import `SpotifyAPI` and must be updated in Phases 2–4 in parallel.

---

## Phase 2: Foundational — Remove `Matcher.__init__` guard (blocks US2)

**Purpose**: Allow `SpotifyMatcher` to be constructed directly in tests without acquiring
the singleton slot. Must complete before Phase 4 (T006, US2 tests).

**⚠️ CRITICAL**: US2 unit tests (T006) require direct construction of `SpotifyMatcher`.

- [X] T002 Modify `matchers/__init__.py`: remove `if Matcher.__instance is not None: raise TypeError(...)` body from `Matcher.__init__`; leave `__init__` signature and `get_instance()` unchanged

**Checkpoint**: `SpotifyMatcher()` can be constructed directly without raising. `get_instance()` continues to protect the singleton slot.

---

## Phase 3: User Story 1 — `get_spotify_client()` in all call sites (Priority: P1) 🎯 MVP

**Goal**: Every module that previously called `SpotifyAPI.get_instance()` now calls
`get_spotify_client()` directly (where no DI is needed) or stores `self._client` from the
constructor (Phases 4–6). After this phase, zero `SpotifyAPI` references remain.

**Independent Test**: `grep -r "SpotifyAPI" . --include="*.py"` returns zero results.

### Implementation for User Story 1

- [X] T003 [P] [US1] Modify `matchers/spotify_matcher.py`: remove `from api.spotify import SpotifyAPI`; add `import spotipy`; add `__init__(self, client: spotipy.Spotify | None = None) -> None` that raises `ValueError` when `client is None` and stores `self._client`; replace 2 `SpotifyAPI.get_instance()` calls in `_prefetch_isrc_data` with `self._client`; convert `@staticmethod def _search` to instance method `def _search(self, query: str)`; update 3 `SpotifyMatcher._search(q)` call sites to `self._search(q)`; pass `client=self._client` to every `SpotifyTrack(...)` created inside `_search`; fix `_search` to use `limit=50` (integer) and check `not response["tracks"]["items"]` instead of `total == 0`
- [X] T004 [P] [US1] Modify `tracks/spotify_track.py`: remove `from api.spotify import SpotifyAPI`; add `from typing import TYPE_CHECKING` guard importing `spotipy` only for type-checking; add keyword-only `*, client: spotipy.Spotify | None = None` param to `__init__`; raise `ValueError` when `client is None`; store `self._client = client`; replace `SpotifyAPI.get_instance()._get_id(...)` with `self._client._get_id(...)`; replace `SpotifyAPI.get_instance().track(...)` in `data` property with `self._client.track(...)`
- [X] T005 [P] [US1] Modify `playlists/spotify_playlist.py`: remove `from api.spotify import SpotifyAPI`; add `import spotipy`; add keyword-only `*, client: spotipy.Spotify | None = None` to `__init__` — raise `ValueError` when `client is None`, store `self._client`; replace all `SpotifyAPI.get_instance()` call sites with `self._client`; pass `client=self._client` to every `SpotifyTrack(...)` in `_load_data`; fix `_load_data` pagination to check `if not api_tracks.get("next"): break` instead of looping on truthiness; add `*, client: spotipy.Spotify | None = None` to `create()` — raise `ValueError` when `None`, forward `client=client` to `cls(...)`; add `*, client: spotipy.Spotify` (required keyword arg, no default) to `create_from_another_playlist()` and forward to `cls.create(..., client=client)`

**Checkpoint**: `grep -r "SpotifyAPI" . --include="*.py"` returns zero results. `uv run python -c "from api.spotify import get_spotify_client"` exits cleanly (no network call).

---

## Phase 4: User Story 2 — Rewrite `SpotifyMatcher` unit tests (Priority: P2)

**Goal**: Replace the `_MatcherTestBase` class + `patch("...SpotifyAPI")` pattern with
pytest fixtures and constructor injection. Zero `patch()` calls targeting `SpotifyAPI` remain.

**Independent Test**: `uv run pytest tests/matchers/test_spotify_matcher.py -m "not integration" -v` passes with no `patch` targeting `SpotifyAPI` and no `Matcher._Matcher__instance` manipulation.

### Tests for User Story 2

- [X] T006 [US2] Rewrite `tests/matchers/test_spotify_matcher.py` unit tests:
  - Add `@pytest.fixture def mock_client() -> MagicMock` using `spec=spotipy.Spotify`
  - Add `@pytest.fixture def matcher(mock_client) -> SpotifyMatcher` returning `SpotifyMatcher(client=mock_client)`
  - Rewrite `_make_spotify_track(track_id, isrc)` helper: drop `SpotifyTrack.__new__`; use `SpotifyTrack(track_id, data=data, client=MagicMock(spec=spotipy.Spotify))` where the mock's `_get_id` returns `track_id`
  - Rewrite `_make_spotify_track_no_data(track_id)` helper: drop `SpotifyTrack.__new__`; use `SpotifyTrack(track_id, client=mock)` where `mock._get_id.return_value = track_id` and `mock.track` is not configured (will raise on access, correctly simulating unloaded state)
  - Delete `_MatcherTestBase` class entirely; convert its subclasses to plain pytest classes using the `matcher` fixture
  - Rewrite each test in `TestPrefetchIsrcData` and `TestMatchListBatchPrefetch`: replace `patch("matchers.spotify_matcher.SpotifyAPI")` blocks with direct access to `matcher._client` (which is already `mock_client` from the fixture); assert `mock_client.tracks.assert_called_once_with(...)` directly
  - Keep `patch.object(SpotifyMatcher, "_search")` patches in `TestMatchIsrc` unchanged (R-006: these work on instance methods identically)
  - Keep all `@pytest.mark.integration` tests in `TestSpotifyMatcher` completely unchanged
  - Convert `_build_matcher_with_suggestions()` instance method to a standalone helper function `_build_matcher_with_suggestions(mock_client: MagicMock, sp_tracks: list[SpotifyTrack]) -> SpotifyMatcher` that calls `SpotifyMatcher(client=mock_client)` and monkeypatches `_match_list`
  - Rename test classes from `unittest.TestCase` subclasses to plain classes; do **not** remove the `TestCase` import — it is still required by `TestSpotifyMatcher` (the integration class, which is kept unchanged)

**Checkpoint**: `uv run pytest tests/matchers/test_spotify_matcher.py -m "not integration" -v` — all unit tests green. `grep "SpotifyAPI\|__new__\|Matcher__instance" tests/matchers/test_spotify_matcher.py` — zero results.

---

## Phase 5: User Story 3 — Update `SpotifyTrack` unit tests (Priority: P3)

**Goal**: Drop `__new__` bypass pattern from test helpers in `tests/tracks/test_spotify_track.py`.

**Independent Test**: `uv run pytest tests/tracks/test_spotify_track.py -m "not integration" -v` passes; `grep "__new__" tests/tracks/test_spotify_track.py` returns zero results.

### Tests for User Story 3

- [X] T007 [P] [US3] Rewrite test helpers in `tests/tracks/test_spotify_track.py`: replace any `SpotifyTrack.__new__` usage with `SpotifyTrack(track_id, data=data, client=mock_client)` where `mock_client = MagicMock(spec=spotipy.Spotify)` and `mock_client._get_id.return_value = track_id`; add `@pytest.fixture def mock_client()` if not already present; update all affected test functions to use the fixture

**Checkpoint**: `uv run pytest tests/tracks/test_spotify_track.py -m "not integration" -v` passes. `grep "SpotifyTrack.__new__" tests/tracks/test_spotify_track.py` returns zero results.

---

## Phase 6: User Story 4 — Add `SpotifyPlaylist` unit tests (Priority: P3)

**Goal**: Add a full unit test class for `SpotifyPlaylist` — the class currently has zero unit
tests. All new tests use the injectable `client=` constructor and classmethod parameters.

**Independent Test**: `uv run pytest tests/playlists/test_spotify_playlist.py -m "not integration" -v` includes at least 6 new passing unit tests; none require a live Spotify connection.

### Tests for User Story 4

- [X] T008 [P] [US4] Add unit test class `TestSpotifyPlaylistUnit` to `tests/playlists/test_spotify_playlist.py`:
  - Add module-level constants: `PLAYLIST_ID`, `PLAYLIST_NAME`, `TRACK_ID_1`, `TRACK_ID_2`
  - Add `@pytest.fixture def mock_client() -> MagicMock` with `spec=spotipy.Spotify`; configure `mock_client._get_id.side_effect = lambda type_, url: url` (pass-through for IDs already in ID form)
  - Add `@pytest.fixture def spotify_playlist(mock_client) -> SpotifyPlaylist` returning `SpotifyPlaylist(PLAYLIST_ID, client=mock_client)`
  - `test_tracks_loads_data_via_playlist_api`: configure `mock_client.playlist()` to return a minimal `{"id": PLAYLIST_ID, "name": PLAYLIST_NAME, "tracks": {"items": [{"track": {"id": TRACK_ID_1, ...}}], "next": None}}`; access `spotify_playlist.tracks`; assert `mock_client.playlist.assert_called_once_with(PLAYLIST_ID)` and `len(tracks) == 1`
  - `test_tracks_paginates_until_next_is_none`: configure `mock_client.playlist()` to return first page with `"next": "url"`, `mock_client.next()` to return second page with `"next": None`; access `.tracks`; assert 2 tracks returned and `mock_client.next.assert_called_once()`
  - `test_add_tracks_calls_playlist_add_items`: call `spotify_playlist.add_tracks([mock_track])` where `mock_track.track_id = TRACK_ID_1`; assert `mock_client.playlist_add_items.assert_called_once()`
  - `test_add_tracks_batches_in_chunks_of_100`: call `add_tracks` with 101 mock tracks; assert `mock_client.playlist_add_items.call_count == 2`
  - `test_remove_track_calls_playlist_remove`: call `spotify_playlist.remove_track([mock_track])`; assert `mock_client.playlist_remove_all_occurrences_of_items.assert_called_once()`
  - `test_create_uses_injected_client`: call `SpotifyPlaylist.create(PLAYLIST_NAME, client=mock_client)` with `mock_client.current_user.return_value = {"id": "user1"}` and `mock_client.user_playlist_create.return_value = {"id": PLAYLIST_ID}`; assert `mock_client.current_user.assert_called_once()` and the returned playlist's `playlist_id == PLAYLIST_ID`

**Checkpoint**: `uv run pytest tests/playlists/test_spotify_playlist.py -m "not integration" -v` — 6+ new tests green. Existing integration tests are completely unchanged.

---

## Final Phase: Polish & Verification

**Purpose**: Run all quality gates and confirm all success criteria from the spec.

- [X] T009 [P] Run `uv run ruff format .` — must produce no changes (exit 0)
- [X] T010 [P] Run `uv run ruff check .` — must produce zero violations
- [X] T011 [P] Run `uv run mypy .` — must produce zero errors in strict mode
- [X] T012 Run `uv run pytest tests/ -m "not integration" -v` — all unit tests must pass
- [X] T013 Verify SC-001: `grep -r "SpotifyAPI" . --include="*.py"` — zero results
- [X] T014 Verify SC-002: `grep -r "SpotifyTrack.__new__\|Matcher__instance" . --include="*.py"` — zero results
- [X] T015 Verify SC-003: `grep -r 'patch.*SpotifyAPI' . --include="*.py"` — zero results
- [X] T016 Verify FR-007: `uv run pytest tests/ -m "integration" -v` — must exit with the same pass/fail result as before the refactor (skip if no live Spotify config is available; document skip with reason)
- [X] T017 Verify SC-006: run `grep -rc 'patch(' tests/ --include="*.py"` and confirm the total count is lower than the pre-refactor baseline; record both counts in a commit message or PR description

---

## Dependencies

```
T001 (Phase 1 — api/spotify.py)
  └── T002 (Phase 2 — Matcher guard) ─────────────────────┐
  ├── T003 (Phase 3 — SpotifyMatcher source)               │
  ├── T004 (Phase 3 — SpotifyTrack source)                 │
  └── T005 (Phase 3 — SpotifyPlaylist source)              │
        │                                                   │
        ├── T006 (Phase 4 — SpotifyMatcher tests) ←────────┘
        ├── T007 (Phase 5 — SpotifyTrack tests)
        └── T008 (Phase 6 — SpotifyPlaylist tests)
              │
              └── T009–T015 (Final — quality gates)
```

T003, T004, T005 are parallel (different files, no inter-dependency).
T006, T007, T008 are parallel (different test files, no inter-dependency).
T009, T010, T011 are parallel (different tools).

---

## Parallel Execution Examples

### Phase 3 (after T001 + T002 complete)
Execute T003, T004, T005 simultaneously — each modifies a different source file.

### Tests phase (after T003–T005 complete)
Execute T006, T007, T008 simultaneously — each modifies a different test file.

### Final phase (after T006–T008 complete)
Execute T009, T010, T011 simultaneously — independent quality-gate commands.

---

## Implementation Strategy

**MVP scope**: T001 alone (Phase 1) is a deployable MVP — it removes `SpotifyAPI` from
`api/spotify.py`. However, without Phases 2–6 the remaining source files still import the
deleted class and all tests break. The true MVP for this refactor is **Phases 1–3** (T001–T005):
all production code compiles and all existing integration tests pass at that point.

**Recommended delivery order**:
1. T001 → T002 (sequential, ~15 min)
2. T003 + T004 + T005 in parallel (~20 min total)
3. T006 + T007 + T008 in parallel (~30 min total)
4. T009–T015 (quality gates + verification, ~5 min)

**Total estimated scope**: 15 tasks across 6 phases.
