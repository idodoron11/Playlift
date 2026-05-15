# Data Model: Cross-Platform Playlist Sync

**Feature**: `008-cross-platform-playlist-sync`  
**Date**: 2026-05-15

## New Entity: `PlaylistFactory`

**Location**: `src/playlists/playlist_factory.py`  
**Layer**: Playlist (sits above Matcher and API; at the same level as `SpotifyPlaylist`, `DeezerPlaylist`)

### Responsibility

Single responsibility: given a source string (local path, Spotify URI/URL, or Deezer URL) and an optional `PathMapper`, construct and return the appropriate `TrackCollection`.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `_spotify_client` | `spotipy.Spotify` | Injected Spotify API client |
| `_deezer_client` | `Deezer` | Injected Deezer API client |

### Public Interface

```
resolve(source: str, path_mapper: PathMapper | None = None) -> TrackCollection
```

**Behaviour**:
1. If `source` is a service URL/URI **and** `path_mapper` is not `None` → raise `InvalidPathMappingError`
2. If `_is_spotify_source(source)` → return `SpotifyPlaylist(source, client=self._spotify_client)`
3. If `_is_deezer_source(source)` → return `DeezerPlaylist(_extract_deezer_playlist_id(source), deezer=self._deezer_client)`
4. If `os.path.isdir(source)` → return `LocalLibrary(source)`
5. If `os.path.isfile(source)` → return `LocalPlaylist(source, path_mapper=path_mapper)`
6. Otherwise → raise `UnrecognisedSourceError`

### Private Helpers (module-level constants + functions)

```
SPOTIFY_URI_PREFIX: str = "spotify:playlist:"
SPOTIFY_URL_FRAGMENT: str = "open.spotify.com/playlist/"
DEEZER_PLAYLIST_URL_PATTERN: re.Pattern[str]  # matches deezer.com/.*/playlist/<id>

_is_spotify_source(source: str) -> bool
_is_deezer_source(source: str) -> bool
_extract_deezer_playlist_id(source: str) -> str
```

---

## Modified Entity: `SyncTarget` (abstract base)

**Location**: `src/playlists/__init__.py`

### Change

Add `import_tracks()` as an `@abstractmethod`. Both `SpotifyPlaylist` and `DeezerPlaylist` already implement this exact signature — they become compliant overrides without any code changes.

```
import_tracks(
    tracks: Iterable[Track],
    autopilot: bool = False,
    embed_matches: bool = False,
) -> None
```

**Semantics**:
- Resolves each source `Track` to a platform-specific track via the class's `track_matcher()`
- Adds successfully matched tracks to the playlist
- Silently skips unmatched tracks
- If `embed_matches=True` **and** the source track is `EmbeddableTrack`, writes the platform ref back to the track's metadata — otherwise silently ignored

---

## New Entity: `UnrecognisedSourceError`

**Location**: `src/exceptions.py`  
**Parent**: `PlaylistSyncError`

Raised by `PlaylistFactory.resolve()` when the source string is not a local file path, local directory path, Spotify URI/URL, or Deezer URL. Caught by `resolve_source()` in `main.py` and converted to `click.UsageError`.

---

## Relationships

```
main.py
  └─ calls ──────────────► PlaylistFactory.resolve(source) → TrackCollection
                                │
                                ├─ SpotifyPlaylist(source)   (if Spotify source)
                                ├─ DeezerPlaylist(id)        (if Deezer source)
                                ├─ LocalPlaylist(source)     (if local file)
                                └─ LocalLibrary(source)      (if local dir)

SyncTarget (abstract)
  ├─ import_tracks() [NEW abstract method]
  ├─ track_matcher() [existing]
  └─ implementations: SpotifyPlaylist, DeezerPlaylist [unchanged]
```

---

## Validation Rules

| Rule | Constraint |
|------|-----------|
| Spotify URI | Must start with `spotify:playlist:` |
| Spotify HTTPS URL | Must contain `open.spotify.com/playlist/` |
| Deezer HTTPS URL | Must match `deezer\.com(/[a-z]{2})?/playlist/(\d+)` |
| Local path | Must be an existing file or directory at resolution time |
| `path_mapper` + service source | Invalid combination → `InvalidPathMappingError` |
| Unknown source | → `UnrecognisedSourceError` |

## State Transitions

`PlaylistFactory` is stateless — it holds injected clients but creates no mutable state. Each `resolve()` call is independent.
