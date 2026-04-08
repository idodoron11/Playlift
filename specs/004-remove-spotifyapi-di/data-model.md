# Data Model: Remove SpotifyAPI Singleton — Constructor Injection Refactor

**Branch**: `004-remove-spotifyapi-di`  
**Date**: 2026-04-08

This refactor introduces no new domain entities. All changes are to **function and constructor
signatures** in existing modules. This document records every API surface change as a
contract-style data model.

---

## Module: `api/spotify.py`

### Before

```python
class SpotifyAPI:
    @classmethod
    def get_instance(cls) -> spotipy.Spotify: ...
```

### After

```python
@functools.cache
def get_spotify_client() -> spotipy.Spotify:
    """Return the singleton authenticated Spotify client.

    Creates and caches a single spotipy.Spotify instance on first call using
    credentials from CONFIG. Subsequent calls return the cached instance.

    Returns:
        An authenticated spotipy.Spotify client.
    """
```

**Key properties**:
- Decorated with `@functools.cache` — first call creates the client; all subsequent
  calls return the same object.
- No module-level mutable state.
- Test resets: `get_spotify_client.cache_clear()`.
- `SpotifyAPI` class removed entirely.

---

## Class: `SpotifyMatcher` (`matchers/spotify_matcher.py`)

### New constructor

```python
def __init__(self, client: spotipy.Spotify | None = None) -> None:
    self._client: spotipy.Spotify = client or get_spotify_client()
```

**Invariant**: `self._client` is always a non-`None` `spotipy.Spotify` instance after
construction.

### `_search` signature change

| Before | After |
|--------|-------|
| `@staticmethod` `def _search(query: str) -> list[SpotifyTrack]` | `def _search(self, query: str) -> list[SpotifyTrack]` |

Internal callers inside the class: `SpotifyMatcher._search(q)` → `self._search(q)` (3 sites).

### Removed dependency

`SpotifyAPI` import removed. `get_spotify_client` imported from `api.spotify`.

---

## Class: `SpotifyTrack` (`tracks/spotify_track.py`)

### New constructor

```python
def __init__(
    self,
    track_url: str,
    data: dict[str, Any] | None = None,
    *,
    client: spotipy.Spotify | None = None,
) -> None:
    self._client: spotipy.Spotify = client or get_spotify_client()
    self._id = self._client._get_id("track", track_url)
    self._data: dict[str, Any] | None = data
    if self._data and self._data["id"] != self._id:
        raise ValueError("The data object does not match the track id")
```

**Notes**:
- `client=` is keyword-only (placed after `*`).
- `self._client._get_id(...)` replaces `SpotifyAPI.get_instance()._get_id(...)`.
- `data` property uses `self._client.track(self._id)` instead of
  `SpotifyAPI.get_instance().track(self._id)`.

---

## Class: `SpotifyPlaylist` (`playlists/spotify_playlist.py`)

### New constructor

```python
def __init__(
    self,
    playlist_url: str | None = None,
    data: dict[str, Any] | None = None,
    *,
    client: spotipy.Spotify | None = None,
) -> None:
    self._client: spotipy.Spotify = client or get_spotify_client()
    self._id = self._client._get_id("playlist", playlist_url)
    ...
```

### Classmethod: `create`

```python
@classmethod
def create(
    cls,
    playlist_name: str,
    public: bool = False,
    *,
    client: spotipy.Spotify | None = None,
) -> "SpotifyPlaylist":
    resolved_client = client or get_spotify_client()
    user_id = resolved_client.current_user()["id"]
    playlist_resp = resolved_client.user_playlist_create(user_id, playlist_name, public=public)
    return cls(playlist_resp["id"], client=resolved_client)
```

### Classmethod: `create_from_another_playlist`

```python
@classmethod
def create_from_another_playlist(
    cls,
    playlist_name: str,
    source_playlist: TrackCollection,
    public: bool = False,
    autopilot: bool = False,
    embed_matches: bool = False,
    *,
    client: spotipy.Spotify | None = None,
) -> "SpotifyPlaylist":
    sp_tracks = SpotifyPlaylist.track_matcher().match_list(
        source_playlist.tracks, autopilot=autopilot, embed_matches=embed_matches
    )
    new_playlist = cls.create(playlist_name, public=public, client=client)
    new_playlist.add_tracks(sp_tracks)
    return new_playlist
```

### `_load_data` change

`SpotifyTrack` constructed with `client=self._client`:

```python
self._tracks.append(SpotifyTrack(api_track["track"]["id"], data=api_track["track"], client=self._client))
```

All 6 `SpotifyAPI.get_instance()` call sites replaced with `self._client`.

---

## Class: `Matcher` (`matchers/__init__.py`)

### Guard removed

```python
# BEFORE:
def __init__(self) -> None:
    if Matcher.__instance is not None:
        raise TypeError("An instance of this class already exists")

# AFTER:
def __init__(self) -> None:
    pass  # or body removed entirely if no other logic
```

`get_instance()` remains the production-safe factory.

---

## Test API Changes

### `tests/matchers/test_spotify_matcher.py`

| Before | After |
|--------|-------|
| `_MatcherTestBase(TestCase)` with `setUp`/`tearDown` resetting `Matcher._Matcher__instance = None` | `@pytest.fixture def matcher(mock_client)` that returns `SpotifyMatcher(client=mock_client)` |
| `_make_spotify_track(...)` using `SpotifyTrack.__new__(SpotifyTrack)` | `_make_spotify_track(...)` using `SpotifyTrack(id, data=data, client=MagicMock())` where mock `_get_id` returns `id` |
| `_make_spotify_track_no_data(...)` using `SpotifyTrack.__new__(SpotifyTrack)` | `SpotifyTrack(id, client=mock_client)` where `mock_client._get_id.return_value = id` |
| `patch("matchers.spotify_matcher.SpotifyAPI")` context managers | Direct `self._client` on the fixture-injected matcher |
| `unittest.TestCase` base class | Plain pytest functions + fixtures |

### `tests/playlists/test_spotify_playlist.py`

New non-integration unit test class added:

```python
@pytest.fixture
def mock_client() -> MagicMock: ...

@pytest.fixture
def spotify_playlist(mock_client: MagicMock) -> SpotifyPlaylist: ...

class TestSpotifyPlaylistUnit:
    def test_tracks_calls_playlist_api_and_returns_tracks(...) -> None: ...
    def test_tracks_paginates_with_next(...) -> None: ...
    def test_add_tracks_calls_playlist_add_items_in_batches(...) -> None: ...
    def test_remove_track_calls_playlist_remove_in_batches(...) -> None: ...
    def test_create_calls_current_user_and_user_playlist_create(...) -> None: ...
    def test_create_from_another_playlist_creates_and_adds_tracks(...) -> None: ...
```

Existing `@pytest.mark.integration` tests in the file are untouched.

---

## Dependency Change Summary

| File | Import removed | Import added |
|------|---------------|--------------|
| `api/spotify.py` | — | `import functools` |
| `matchers/spotify_matcher.py` | `from api.spotify import SpotifyAPI` | `from api.spotify import get_spotify_client` |
| `tracks/spotify_track.py` | `from api.spotify import SpotifyAPI` | `from api.spotify import get_spotify_client` |
| `playlists/spotify_playlist.py` | `from api.spotify import SpotifyAPI` | `from api.spotify import get_spotify_client` |
