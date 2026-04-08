# Quickstart: Remove SpotifyAPI Singleton — Constructor Injection Refactor

**Branch**: `004-remove-spotifyapi-di`

## Prerequisites

```bash
uv sync
```

## Verify the refactor is complete

### 1. Zero `SpotifyAPI` references

```bash
grep -r "SpotifyAPI" . --include="*.py"
# Expected: no output
```

### 2. Zero test anti-patterns removed

```bash
grep -r "SpotifyTrack.__new__\|Matcher__instance" . --include="*.py"
# Expected: no output
```

### 3. Quality gates

```bash
uv run ruff format .
uv run ruff check .
uv run mypy .
uv run pytest tests/ -m "not integration"
```

All four commands must exit with code 0.

## Run unit tests only (no Spotify connection required)

```bash
uv run pytest tests/ -m "not integration" -v
```

## Run integration tests (requires valid `~/.playlist_sync/config.ini`)

```bash
uv run pytest tests/ -m "integration" -v
```

## Test the new injection API manually

```python
from unittest.mock import MagicMock
import spotipy

mock_client = MagicMock(spec=spotipy.Spotify)
mock_client._get_id.return_value = "abc123"

# SpotifyTrack — no network call
from tracks.spotify_track import SpotifyTrack
mock_client.track.return_value = {
    "id": "abc123", "name": "Song", "artists": [{"name": "Artist"}],
    "album": {"name": "Album"}, "duration_ms": 200000, "track_number": 1,
    "external_ids": {"isrc": "USRC17607839"},
}
track = SpotifyTrack("abc123", client=mock_client)
assert track.title == "Song"

# SpotifyMatcher — no network call
from matchers.spotify_matcher import SpotifyMatcher
matcher = SpotifyMatcher(client=mock_client)
mock_client.search.return_value = {"tracks": {"total": 0, "items": []}}
result = matcher.match(track)
assert result is None
```
