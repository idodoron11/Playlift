# Research: Cross-Platform Playlist Sync

**Feature**: `008-cross-platform-playlist-sync`  
**Date**: 2026-05-15

## Resolved Technical Unknowns

---

### RES-001: Does `SpotifyPlaylist` already handle both URIs and HTTPS URLs?

**Decision**: Yes — no URL extraction needed in `PlaylistFactory` for Spotify sources.

**Rationale**: spotipy's `_get_id("playlist", url)` internally matches two regex patterns:
- Spotify URI: `^spotify:(?:track|artist|album|playlist|...):([0-9A-Za-z]+)$`
- Spotify HTTPS URL: `^https?://open.spotify.com/(intl-\w\w/)?playlist/([0-9A-Za-z]+)(\?.*)?$`

Both URI and HTTPS URL formats are normalised to the bare playlist ID inside the `SpotifyPlaylist.__init__`. `PlaylistFactory` can therefore pass the raw source string directly: `SpotifyPlaylist(source, client=spotify_client)`.

**Alternatives considered**: Extracting the ID before construction — rejected, as it would duplicate logic already present in spotipy.

---

### RES-002: Does `DeezerPlaylist.__init__` accept URLs, or only raw numeric IDs?

**Decision**: `DeezerPlaylist` only accepts raw numeric IDs. `PlaylistFactory` must extract the ID from the URL before constructing `DeezerPlaylist`.

**Rationale**: `DeezerPlaylist.__init__` stores `str(playlist_id)` directly as `self._playlist_id` and passes it verbatim to `self._deezer.gw.get_playlist_tracks(self._playlist_id)`. The GW API expects a numeric string.

**Regex pattern** (following the established pattern in `src/tracks/deezer_track.py`):
```python
DEEZER_PLAYLIST_URL_PATTERN: re.Pattern[str] = re.compile(
    r"^https?://(www\.)?deezer\.com(/[a-z]{2}(-[a-z]{2})?)?/playlist/(\d+)(\?.*)?$"
)
```
Group 4 captures the numeric playlist ID.

**Alternatives considered**: Adding URL parsing to `DeezerPlaylist.__init__` — rejected, as that would give `DeezerPlaylist` a second responsibility (URL parsing) and is out of scope for this feature.

---

### RES-003: Is there a circular import risk in creating `src/playlists/playlist_factory.py`?

**Decision**: No circular import risk. `PlaylistFactory` can safely import from `spotify_playlist.py` and `deezer_playlist.py`.

**Rationale**: Both concrete playlist modules import from `playlists/__init__.py` (base classes) and layers below (matchers, tracks, api). Neither imports from `playlist_factory.py` (which doesn't exist yet) or from `main.py`. The new file sits at the same layer level as the other playlist modules and only imports downward.

Import chain (no cycles):
```
main.py → playlist_factory.py → spotify_playlist.py → spotify_matcher.py → api/spotify.py
                               → deezer_playlist.py  → deezer_matcher.py  → api/deezer.py
                               → playlists/__init__.py
                               → local_playlist.py
                               → local_library.py
```

---

### RES-004: What existing exceptions are defined in `src/exceptions.py`?

**Current state**:
```python
class PlaylistSyncError(Exception): ...
class SkipTrackError(PlaylistSyncError): ...
class InvalidPathMappingError(PlaylistSyncError): ...
```

**Decision**: Add `UnrecognisedSourceError(PlaylistSyncError)` for the case where a source string is not a local path, Spotify URI/URL, or Deezer URL. This is raised by `PlaylistFactory.resolve()` and caught by `resolve_source()` in `main.py`, which converts it to `click.UsageError`.

**Alternatives considered**: Raising bare `ValueError` — rejected per Constitution Principle VI (custom exception classes required for each distinct failure mode).

---

## Summary of Decisions

| # | Decision | Chosen Approach | Rationale |
|---|----------|-----------------|-----------|
| RES-001 | Spotify URL/URI handling | Pass raw string to `SpotifyPlaylist()` | spotipy normalises both internally |
| RES-002 | Deezer URL handling | Extract ID in `PlaylistFactory` with regex | `DeezerPlaylist` only accepts numeric IDs |
| RES-003 | Import structure | New file at `src/playlists/playlist_factory.py` | No circular risks; correct layer position |
| RES-004 | Error type | New `UnrecognisedSourceError(PlaylistSyncError)` in `exceptions.py` | Constitution VI requires domain exceptions |
