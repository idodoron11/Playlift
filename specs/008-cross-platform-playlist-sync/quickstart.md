# Quickstart: Cross-Platform Playlist Sync

**Feature**: `008-cross-platform-playlist-sync`  
**Date**: 2026-05-15

## What Changes

After this feature, the `--source` argument of `import` and `sync` commands accepts **any** of these formats in addition to local `.m3u` files:

| Format | Example |
|--------|---------|
| Spotify URI | `spotify:playlist:37i9dQZF1DXcBWIGoYBM5M` |
| Spotify HTTPS URL | `https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M` |
| Deezer HTTPS URL | `https://www.deezer.com/en/playlist/1313621735` |

No new flags. No changes to existing local-file usage.

---

## CLI Examples

### Spotify → Deezer (import)

```bash
uv run python main.py deezer import \
  --source "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M" \
  --destination "My Deezer Playlist"
```

### Deezer → Spotify (import)

```bash
uv run python main.py spotify import \
  --source "https://www.deezer.com/en/playlist/1313621735" \
  --destination "My Spotify Playlist"
```

### Spotify → Deezer (sync an existing playlist)

```bash
uv run python main.py deezer sync \
  --source "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M" \
  --destination "9876543210"
```

### Existing local workflow (unchanged)

```bash
# Unchanged — still works exactly as before
uv run python main.py spotify import \
  --source "/path/to/playlist.m3u" \
  --destination "My Spotify Playlist"
```

### `--autopilot` works the same way

```bash
uv run python main.py deezer import \
  --source "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" \
  --destination "My Deezer Playlist" \
  --autopilot
```

---

## Error Cases

### Path remapping with a service source (rejected immediately)

```bash
uv run python main.py spotify import \
  --source "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M" \
  --destination "Test" \
  --from-path "/old" --to-path "/new"
# Error: --from-path/--to-path cannot be used with a service playlist source
```

### Unrecognised source string

```bash
uv run python main.py spotify import \
  --source "not-a-valid-source" \
  --destination "Test"
# Error: Unrecognised source: "not-a-valid-source"
```

---

## Using `PlaylistFactory` Programmatically

```python
from playlists.playlist_factory import PlaylistFactory
from api.spotify import get_spotify_client
from api.deezer import get_deezer_client

factory = PlaylistFactory(
    spotify_client=get_spotify_client(),
    deezer_client=get_deezer_client(),
)

# Resolves to SpotifyPlaylist
source = factory.resolve("spotify:playlist:37i9dQZF1DXcBWIGoYBM5M")

# Resolves to DeezerPlaylist
source = factory.resolve("https://www.deezer.com/en/playlist/1313621735")

# Resolves to LocalPlaylist
source = factory.resolve("/path/to/playlist.m3u")
```

---

## Supported Source × Destination Matrix

| Source ↓ \ Destination → | Spotify | Deezer |
|--------------------------|---------|--------|
| Local `.m3u` file | ✅ | ✅ |
| Local music directory | ✅ | ✅ |
| Spotify playlist | ✅ | ✅ |
| Deezer playlist | ✅ | ✅ |
| ~~Local (as destination)~~ | ❌ | ❌ |
