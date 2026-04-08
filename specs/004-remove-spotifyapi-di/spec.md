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

A developer writing a unit test for `SpotifyMatcher` constructs the matcher with a mock client passed directly to the constructor. No `patch()` context manager or singleton reset is needed. The existing `get_instance()` factory still works in production — it just constructs a `SpotifyMatcher()` with no argument, which defaults to the cached client.

**Why this priority**: `SpotifyMatcher` is the most-tested class. Removing patching from its tests has the highest payoff in test clarity and removes the manual `Matcher._Matcher__instance = None` reset hack.

**Independent Test**: A unit test constructs `SpotifyMatcher(client=mock_client)` directly, calls `match()` or `suggest_match()`, and asserts on the return value — with no `patch()` and no `setUp`/`tearDown` singleton manipulation.

**Acceptance Scenarios**:

1. **Given** a `SpotifyMatcher` constructed with a mock client, **When** `match()` is called, **Then** the mock client's methods are invoked and the result is based solely on the mock's return values.
2. **Given** a `SpotifyMatcher` constructed with no argument, **When** the matcher is used in production, **Then** it transparently uses the shared cached client.
3. **Given** the `Matcher` base class, **When** `SpotifyMatcher()` is constructed directly in a test, **Then** no `TypeError` is raised (the "already exists" guard is absent).

---

### User Story 3 - Inject client into SpotifyTrack (Priority: P3)

A developer writing a unit test for `SpotifyTrack` constructs the track with a mock client passed as a keyword argument. The `__new__`-bypass hack used in existing test helpers is no longer needed because the constructor accepts a mock directly.

**Why this priority**: `SpotifyTrack` is constructed in many places (matcher, playlist loader, test helpers). Cleaning up its constructor makes every downstream test helper simpler and removes a fragile test pattern.

**Independent Test**: A unit test constructs `SpotifyTrack(track_id, client=mock_client)` where `mock_client._get_id()` returns the expected ID, then asserts `track.track_id` and `track.isrc` without any `__new__` or patching.

**Acceptance Scenarios**:

1. **Given** a `SpotifyTrack` constructed with a mock client and pre-loaded data, **When** properties such as `title`, `artists`, `isrc` are accessed, **Then** the correct values are returned without any network call.
2. **Given** a `SpotifyTrack` constructed with a mock client and no data, **When** `data` is accessed, **Then** the mock client's `.track()` method is called exactly once and the result is cached.
3. **Given** a `SpotifyTrack` constructed with no client argument, **When** used in production, **Then** it transparently uses the shared cached client.

---

### User Story 4 - Inject client into SpotifyPlaylist (Priority: P3)

A developer writing a unit test for `SpotifyPlaylist` constructs the playlist with a mock client, so all API calls (load data, add tracks, remove tracks) are intercepted without patching.

**Why this priority**: Same testability improvement as SpotifyTrack; both are P3 because they are parallel work and neither blocks the other.

**Independent Test**: A unit test constructs `SpotifyPlaylist(playlist_id, client=mock_client)`, calls `.tracks`, and asserts that `mock_client.playlist()` was called — no `patch()` needed.

**Acceptance Scenarios**:

1. **Given** a `SpotifyPlaylist` constructed with a mock client, **When** `.tracks` is accessed, **Then** the mock client's `.playlist()` and `.next()` are called and the returned tracks are constructed with the same mock client.
2. **Given** a `SpotifyPlaylist` constructed with a mock client, **When** `add_tracks()` is called, **Then** the mock client's `.playlist_add_items()` is invoked in 100-track batches.
3. **Given** a `SpotifyPlaylist` constructed with no client argument, **When** used in production, **Then** it transparently uses the shared cached client.

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
- **FR-003**: `SpotifyMatcher`, `SpotifyTrack`, and `SpotifyPlaylist` must each accept an optional `client` parameter in their constructors; when omitted, they must default to the cached client from `get_spotify_client()`. The two `SpotifyPlaylist` classmethods — `create()` and `create_from_another_playlist()` — must also accept an optional `client` keyword parameter for the same reason; they default to `get_spotify_client()` when `None`.
- **FR-004**: `SpotifyPlaylist._load_data()` must propagate its own client instance to every `SpotifyTrack` it constructs, so the full object graph is injectable in tests.
- **FR-005**: The `Matcher` base class must allow direct construction (i.e., the "already exists" guard in `__init__` must be removed); `get_instance()` remains the recommended path in production.
- **FR-006**: All existing unit tests that previously used `patch("...SpotifyAPI")` or `SpotifyTrack.__new__` must be rewritten to use constructor injection with a mock client.
- **FR-007**: All `@pytest.mark.integration` tests must continue to pass without modification; they must resolve the client through `get_spotify_client()` transparently.
- **FR-008**: The refactored codebase must pass `ruff check`, `ruff format`, and `mypy` (strict mode) with zero errors.

### Key Entities

- **`get_spotify_client()`**: Module-level function in `api/spotify.py` that lazily creates and caches a single authenticated Spotify client for the lifetime of the process.
- **`spotipy.Spotify` client**: The third-party Spotify API client; consumed by `SpotifyMatcher`, `SpotifyTrack`, and `SpotifyPlaylist`. Injected via constructor in tests; sourced from `get_spotify_client()` in production.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero occurrences of `SpotifyAPI` in any `.py` file after the refactor.
- **SC-002**: Zero uses of `SpotifyTrack.__new__` or `Matcher._Matcher__instance` manipulation in any test file.
- **SC-003**: Zero `patch()` calls targeting `SpotifyAPI` in unit tests; all mocking is achieved via constructor injection.
- **SC-004**: All non-integration unit tests pass without a live Spotify connection.
- **SC-005**: `ruff check .`, `ruff format .`, and `mypy .` each exit with zero errors or warnings.
- **SC-006**: The number of `patch()` calls across unit test files decreases compared to before the refactor.

## Clarifications

### Session 2026-04-08

- Q: Should `SpotifyPlaylist.create()` and `create_from_another_playlist()` also accept a `client=` keyword parameter? → A: Yes — add `client: spotipy.Spotify | None = None` to both classmethods; they default to `get_spotify_client()` when `None`.

## Assumptions

- The `Singleton` metaclass in `singleton.py` is not used by `SpotifyAPI` and is unrelated to this refactor; it will not be modified.
- Integration tests (marked `@pytest.mark.integration`) require a live Spotify connection and valid config; they are out of scope for unit test improvements.
- No changes are needed in `main.py`, `sync_exported_playlists.py`, or `cleanup.py` — they call `SpotifyMatcher.get_instance()` or `SpotifyPlaylist(url)` which continue to work through the default-client path.
- Thread safety of the cached client is not a concern; the application is single-threaded.
