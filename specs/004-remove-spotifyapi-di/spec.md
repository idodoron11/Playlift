# Feature Specification: Remove SpotifyAPI Singleton — Constructor Injection Refactor

**Feature Branch**: `004-remove-spotifyapi-di`  
**Created**: 2026-04-08  
**Status**: Draft  
**Input**: User description: "Remove SpotifyAPI singleton and inject spotipy.Spotify via constructor DI"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Replace SpotifyAPI with a simple function (Priority: P1)

A developer accessing the Spotify client calls a plain function — `get_spotify_client()` — instead of navigating a custom singleton class. The function returns the same cached client on every call. The `SpotifyAPI` class and its `get_instance()` method no longer exist anywhere in the codebase.

**Why this priority**: Everything else depends on this. It is the composition root that all three downstream classes will use as their default client source. Removing the class eliminates the singleton anti-pattern at its origin.

**Independent Test**: Verified by calling `get_spotify_client()` twice and asserting both calls return the same object, without any `SpotifyAPI` import being required anywhere in the codebase.

**Acceptance Scenarios**:

1. **Given** a configured environment, **When** `get_spotify_client()` is called multiple times, **Then** the same client instance is returned every time (lazy, cached behaviour).
2. **Given** no prior call to `get_spotify_client()`, **When** the module is imported, **Then** no authentication or network activity occurs (lazy init).
3. **Given** the codebase, **When** searching for `SpotifyAPI`, **Then** zero occurrences are found in any source or test file.

---

### User Story 2 - Inject client into SpotifyMatcher (Priority: P2)

A developer writing a unit test for `SpotifyMatcher` constructs the matcher with a mock client passed directly to the constructor. No `patch()` context manager or singleton reset is needed. The existing `get_instance()` factory still works in production — it explicitly passes `client=get_spotify_client()` when constructing the singleton instance.

**Why this priority**: `SpotifyMatcher` is the most-tested class. Removing patching from its tests has the highest payoff in test clarity and removes the manual `Matcher._Matcher__instance = None` reset hack.

**Independent Test**: A unit test constructs `SpotifyMatcher(client=mock_client)` directly, calls `match()` or `suggest_match()`, and asserts on the return value — with no `patch()` and no `setUp`/`tearDown` singleton manipulation.

**Acceptance Scenarios**:

1. **Given** a `SpotifyMatcher` constructed with a mock client, **When** `match()` is called, **Then** the mock client's methods are invoked and the result is based solely on the mock's return values.
2. **Given** the production path via `Matcher.get_instance()`, **When** the singleton is first constructed, **Then** `get_spotify_client()` is passed explicitly as `client=` — no silent global look-up inside the class.
3. **Given** the `Matcher` base class, **When** `SpotifyMatcher()` is constructed directly in a test, **Then** no `TypeError` is raised (the "already exists" guard is absent).

---

### User Story 3 - Inject client into SpotifyTrack (Priority: P3)

A developer writing a unit test for `SpotifyTrack` constructs the track with a mock client passed as a keyword argument. The `__new__`-bypass hack used in existing test helpers is no longer needed because the constructor accepts a mock directly.

**Why this priority**: `SpotifyTrack` is constructed in many places (matcher, playlist loader, test helpers). Cleaning up its constructor makes every downstream test helper simpler and removes a fragile test pattern.

**Independent Test**: A unit test constructs `SpotifyTrack(track_id, client=mock_client)` where `mock_client._get_id()` returns the expected ID, then asserts `track.track_id` and `track.isrc` without any `__new__` or patching.

**Acceptance Scenarios**:

1. **Given** a `SpotifyTrack` constructed with a mock client and pre-loaded data, **When** properties such as `title`, `artists`, `isrc` are accessed, **Then** the correct values are returned without any network call.
2. **Given** a `SpotifyTrack` constructed with a mock client and no data, **When** `data` is accessed, **Then** the mock client's `.track()` method is called exactly once and the result is cached.
3. **Given** a `SpotifyTrack` constructed with no client argument, **When** the constructor is called, **Then** a `ValueError` is raised immediately — all call sites must supply the client explicitly (typically `get_spotify_client()` in production).

---

### User Story 4 - Inject client into SpotifyPlaylist and add unit tests (Priority: P3)

A developer writing a unit test for `SpotifyPlaylist` constructs the playlist with a mock client, so all API calls (load data, add tracks, remove tracks, create) are intercepted without patching. Because `SpotifyPlaylist` currently has zero unit tests (all tests are integration), this refactor introduces a full unit test suite for the class using the newly injected client.

**Why this priority**: Same testability improvement as SpotifyTrack; both are P3 because they are parallel work and neither blocks the other. The testing instructions require every public class to have unit tests — this refactor is the natural moment to remedy the gap.

**Independent Test**: A unit test constructs `SpotifyPlaylist(playlist_id, client=mock_client)`, calls `.tracks`, and asserts that `mock_client.playlist()` was called — no `patch()` needed.

**Acceptance Scenarios**:

1. **Given** a `SpotifyPlaylist` constructed with a mock client, **When** `.tracks` is accessed, **Then** the mock client's `.playlist()` and `.next()` are called and the returned `SpotifyTrack` objects are constructed with the same mock client.
2. **Given** a `SpotifyPlaylist` constructed with a mock client, **When** `add_tracks()` is called, **Then** the mock client's `.playlist_add_items()` is invoked in 100-track batches.
3. **Given** a `SpotifyPlaylist` constructed with a mock client, **When** `remove_track()` is called, **Then** the mock client's `.playlist_remove_all_occurrences_of_items()` is invoked in 100-track batches.
4. **Given** a mock client passed to `SpotifyPlaylist.create()`, **When** the classmethod is called, **Then** it uses the provided client (not the global) to look up the current user and create the playlist.
5. **Given** a `SpotifyPlaylist` constructed with no client argument, **When** the constructor is called, **Then** a `ValueError` is raised immediately — all call sites must supply the client explicitly (typically `get_spotify_client()` in production).

---

### Edge Cases

- What happens when `get_spotify_client()` is called before the config file exists? The config load failure is unchanged — it raises at call time, not at import time.
- What happens when a `SpotifyTrack` is created by the playlist loader? It must receive the same client instance the playlist was constructed with.
- What happens when `SpotifyMatcher.get_instance()` is called after a test constructed a `SpotifyMatcher(client=mock)` directly? The singleton is independent of direct construction; `get_instance()` manages its own instance.
- What happens with the `Matcher.__init__` guard that raises `TypeError` if an instance already exists? It must be removed so direct construction in tests is possible without the singleton being set.
- What happens with `SpotifyPlaylist.create()` and `SpotifyPlaylist.create_from_another_playlist()` in unit tests? Both classmethods must accept `client=` so they can be tested without patching `get_spotify_client()`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `SpotifyAPI` class must be removed entirely; no file in the codebase may reference it after the refactor.
- **FR-002**: A public `get_spotify_client()` function must replace `SpotifyAPI.get_instance()`, returning the same cached client on repeated calls with no network activity before the first call.
- **FR-003**: `SpotifyMatcher`, `SpotifyTrack`, and `SpotifyPlaylist` must each accept a `client` keyword-only parameter in their constructors; passing `None` (or omitting it) raises `ValueError` at runtime — all callers must supply a real client explicitly. `SpotifyPlaylist.create()` follows the same pattern (`*, client: spotipy.Spotify | None = None`, raises on `None`). `SpotifyPlaylist.create_from_another_playlist()` declares `client` as a required keyword argument (`*, client: spotipy.Spotify`). In production, all call sites in `main.py`, `cleanup.py`, and `playlists/compare.py` pass `client=get_spotify_client()` explicitly; `Matcher.get_instance()` does the same when constructing the singleton.
- **FR-004**: `SpotifyPlaylist._load_data()` must propagate its own client instance to every `SpotifyTrack` it constructs, so the full object graph is injectable in tests.
- **FR-005**: The `Matcher` base class must allow direct construction (i.e., the "already exists" guard in `__init__` must be removed); `get_instance()` remains the recommended path in production.
- **FR-006**: All existing unit tests that previously used `patch("...SpotifyAPI")` or `SpotifyTrack.__new__` must be rewritten to use constructor injection with a mock client.
- **FR-007**: All `@pytest.mark.integration` tests must continue to pass without modification; they must resolve the client through `get_spotify_client()` transparently.
- **FR-008**: The refactored codebase must pass `ruff check`, `ruff format`, and `mypy` (strict mode) with zero errors.
- **FR-009**: New unit tests must be added for `SpotifyPlaylist` covering at minimum: `tracks` property (with pagination), `add_tracks()`, `remove_track()`, `create()`, and `create_from_another_playlist()` — all using a mock client injected via constructor or classmethod parameter.

### Key Entities

- **`get_spotify_client()`**: Module-level function in `api/spotify.py` that lazily creates and caches a single authenticated Spotify client for the lifetime of the process.
- **`spotipy.Spotify` client**: The third-party Spotify API client; consumed by `SpotifyMatcher`, `SpotifyTrack`, and `SpotifyPlaylist`. Injected via constructor in tests; sourced from `get_spotify_client()` in production.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero occurrences of `SpotifyAPI` in any `.py` file after the refactor.
- **SC-002**: Zero uses of `SpotifyTrack.__new__` or `Matcher._Matcher__instance` manipulation in any test file.
- **SC-003**: Zero `patch()` calls targeting `SpotifyAPI` in unit tests; all mocking is achieved via constructor injection.
- **SC-004**: All non-integration unit tests pass without a live Spotify connection, including the newly added `SpotifyPlaylist` unit tests.
- **SC-005**: `ruff check .`, `ruff format .`, and `mypy .` each exit with zero errors or warnings.
- **SC-006**: The number of `patch()` calls across unit test files decreases compared to before the refactor.

## Clarifications

### Session 2026-04-08

- Q: Should `SpotifyPlaylist.create()` and `create_from_another_playlist()` also accept a `client=` keyword parameter? → A: Yes. `create()` uses `*, client: spotipy.Spotify | None = None` and raises `ValueError` when `None`. `create_from_another_playlist()` declares `client` as a required keyword argument (`*, client: spotipy.Spotify`).
- Q: How should `get_spotify_client()` be tested? → A: No unit test; it is a pure infrastructure function covered implicitly by integration tests.
- Q: Should new `SpotifyPlaylist` unit tests be written as part of this refactor? → A: Yes — add unit tests covering `tracks`, `add_tracks()`, `remove_track()`, `create()`, and `create_from_another_playlist()` using a mock client.

## Assumptions

- The `Singleton` metaclass in `singleton.py` is not used by `SpotifyAPI` and is unrelated to this refactor; it will not be modified.
- Integration tests (marked `@pytest.mark.integration`) require a live Spotify connection and valid config; they are out of scope for unit test improvements.
- `main.py` and `cleanup.py` were updated to import `get_spotify_client` and pass `client=get_spotify_client()` at each `SpotifyPlaylist` and `SpotifyTrack` construction site. `sync_exported_playlists.py` was not modified because it delegates entirely through `SpotifyMatcher.get_instance()` and `SpotifyPlaylist.create_from_another_playlist()` which are called with the client through other paths.
- Thread safety of the cached client is not a concern; the application is single-threaded.
- `get_spotify_client()` is excluded from unit test coverage; it is a pure infrastructure boundary function (analogous to `CONFIG` loading) and is exercised by integration tests.
