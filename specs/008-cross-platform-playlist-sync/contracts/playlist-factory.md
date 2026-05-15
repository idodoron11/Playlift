# Contract: PlaylistFactory Public Interface

**Feature**: `008-cross-platform-playlist-sync`  
**Date**: 2026-05-15  
**Module**: `src/playlists/playlist_factory.py`

---

## `PlaylistFactory`

### Constructor

```python
PlaylistFactory(
    spotify_client: spotipy.Spotify,
    deezer_client: Deezer,
) -> None
```

**Preconditions**:
- `spotify_client` is an authenticated `spotipy.Spotify` instance
- `deezer_client` is an authenticated `Deezer` instance

**Postconditions**:
- Instance is ready; no network calls are made on construction

---

### `resolve()`

```python
def resolve(
    self,
    source: str,
    path_mapper: PathMapper | None = None,
) -> TrackCollection
```

**Preconditions**:
- `source` is a non-empty string

**Postconditions (success)**:

| Source format | Returns | Notes |
|---------------|---------|-------|
| `spotify:playlist:<id>` | `SpotifyPlaylist` | ID extracted by spotipy internally |
| `https://open.spotify.com/playlist/<id>[?...]` | `SpotifyPlaylist` | |
| `https://[www.]deezer.com[/<locale>]/playlist/<id>[?...]` | `DeezerPlaylist` | Numeric ID extracted from URL |
| Existing local file path | `LocalPlaylist` | `path_mapper` forwarded |
| Existing local directory path | `LocalLibrary` | |

**Raises**:

| Exception | Condition |
|-----------|-----------|
| `ValueError` | `source` is a service URL/URI **and** `path_mapper is not None` |
| `UnrecognisedSourceError` | `source` does not match any known format and is not a valid local path |

**Does not raise**:
- Platform API errors (e.g. playlist not found, auth failure) — these surface lazily when `TrackCollection.tracks` is accessed, not at construction time

---

## `SyncTarget.import_tracks()` (updated contract)

**Module**: `src/playlists/__init__.py`

```python
@abstractmethod
def import_tracks(
    self,
    tracks: Iterable[Track],
    autopilot: bool = False,
    embed_matches: bool = False,
) -> None
```

**Contract**:
- Resolves each track in `tracks` via `self.track_matcher().match_list(...)`
- Adds all successfully matched tracks to this playlist
- Skips unmatched tracks silently
- When `embed_matches=True`: writes the matched platform ref back to the source track **only if** the source track is an `EmbeddableTrack` instance. If not, the flag is silently ignored — no error, no warning.
- Must be idempotent with respect to the underlying platform playlist state: does not clear before adding (caller is responsible for clearing if needed)

**Implementations**: `SpotifyPlaylist.import_tracks()`, `DeezerPlaylist.import_tracks()` — both already satisfy this contract.
