# Plan: Cross-Platform Playlist Sync

## TL;DR
Enable syncing any `TrackCollection` (local file, SpotifyPlaylist, DeezerPlaylist) into any `SyncTarget` (Spotify, Deezer). The matchers already handle non-local `Track` objects gracefully. Gaps: (1) `SyncTarget` lacks `import_tracks` abstract method; (2) source URL/ID detection and TrackCollection construction belongs in a dedicated `PlatformResolver` class; (3) CLI commands wire it all together.

## Decisions
- `embed_matches` on a non-local source → silently ignored (matchers already check `isinstance(track, EmbeddableTrack)`)
- Source type → auto-detected from URL/URI format
- `--from-path`/`--to-path` + service source → raise `click.BadParameter`
- `compare` command → out of scope
- `PlaylistFactory` lives at `src/playlists/playlist_factory.py` (NOT `api/`) — it constructs playlist objects, so it sits at the Playlist layer; placing it in `api/` would invert the CLI→Playlist→Matcher→API layering

---

## Phase 1: Formalise the interface

**File:** `src/playlists/__init__.py`

1. Add `import_tracks(tracks: Iterable[Track], autopilot: bool = False, embed_matches: bool = False) -> None` as `@abstractmethod` to `SyncTarget`.
   - Both `SpotifyPlaylist` and `DeezerPlaylist` already implement this signature — they become valid overrides.

---

## Phase 2: PlaylistFactory class

**File:** `src/playlists/playlist_factory.py` *(new file)*

2. Define `PlaylistFactory` with constructor injection:
   - `__init__(self, spotify_client: spotipy.Spotify, deezer_client: Deezer) -> None`

3. Add `resolve(self, source: str, path_mapper: PathMapper | None = None) -> TrackCollection`:
   - Service source + `path_mapper` → `raise ValueError("path mapping not supported for service playlists")`
   - `_is_spotify_source(source)` → `SpotifyPlaylist(source, client=self._spotify_client)`
   - `_is_deezer_source(source)` → `DeezerPlaylist(_extract_deezer_playlist_id(source), deezer=self._deezer_client)`
   - Otherwise → `LocalLibrary(source)` if dir, `LocalPlaylist(source, path_mapper=path_mapper)` if file, else `raise ValueError`

4. Add private static helpers:
   - `_is_spotify_source(source: str) -> bool` — matches `spotify:playlist:*` or `open.spotify.com/playlist/*`
   - `_is_deezer_source(source: str) -> bool` — matches `deezer.com/.*/playlist/` or a purely numeric string
   - `_extract_deezer_playlist_id(source: str) -> str` — regex extracts numeric ID from URL, or returns string as-is

---

## Phase 3: Wire into main.py

**File:** `src/main.py`

5. Add `_build_playlist_factory() -> PlaylistFactory` helper:
   - Calls `get_spotify_client()` and `get_deezer_client()` (wraps `DeezerAuthenticationError` → `click.ClickException`)
   - Returns a constructed `PlaylistFactory`

6. Add `resolve_source(source: str, path_mapper: PathMapper | None = None) -> TrackCollection`:
   - Calls `_build_playlist_factory().resolve(source, path_mapper)`
   - Wraps `ValueError` from resolver (path_mapper + service source) → `click.BadParameter`

---

## Phase 4: Update CLI commands *(parallel)*

**File:** `src/main.py`

For each command, replace `get_playlist(src/source, path_mapper=...)` with `resolve_source(src/source, path_mapper=...)`. No other changes.

7. `cli_spotify_import`
8. `cli_spotify_sync`
9. `cli_deezer_import`
10. `cli_deezer_sync`

Note: Deezer commands already call `get_deezer_client()` before the source resolution. `_build_playlist_factory()` calls it again — returns the same singleton. The `DeezerAuthenticationError` handling that exists in those commands can be removed (now handled centrally in `_build_playlist_factory()`).

---

## Relevant Files
- `src/playlists/__init__.py` — add `import_tracks` to `SyncTarget`
- `src/playlists/playlist_factory.py` — new file: `PlaylistFactory` class
- `src/main.py` — add `_build_playlist_factory()` + `resolve_source()`, update 4 commands, remove now-redundant `get_deezer_client()` auth-error handling from individual commands
- `src/playlists/spotify_playlist.py` — no change
- `src/playlists/deezer_playlist.py` — no change
- `src/matchers/spotify_matcher.py` — no change
- `src/matchers/deezer_matcher.py` — no change

---

## Verification
1. `uv run ruff check . && uv run ruff format .`
2. `uv run mypy .`
3. `uv run pytest tests/` (existing tests must pass)
4. New unit tests for `PlaylistFactory.resolve()` covering:
   - local file path → `LocalPlaylist`
   - local dir path → `LocalLibrary`
   - Spotify URI (`spotify:playlist:ID`)
   - Spotify HTTPS URL (`open.spotify.com/playlist/ID`)
   - Deezer HTTPS URL (`deezer.com/en/playlist/ID`)
   - Deezer numeric ID
   - path_mapper + service source → `ValueError`
5. Manual: `python main.py deezer import -s "spotify:playlist:ID" -d "Test"` — Spotify→Deezer
6. Manual: `python main.py spotify import -s "https://www.deezer.com/en/playlist/ID" -d "Test"` — Deezer→Spotify

---

## Out of Scope
- `compare` / `match` cross-platform support
- `@override` annotations on existing implementations
