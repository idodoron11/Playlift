# Quickstart: Decouple Playlist from SyncTarget

**Feature**: 005-decouple-playlist-synctarget  
**Date**: 2026-04-21

## Prerequisites

- Python 3.11+
- `uv` installed
- Repository cloned and on branch `005-decouple-playlist-synctarget`

## Setup

```bash
cd /Users/idoron/dev/playlist-sync
uv sync
```

## Implementation Order

Apply changes in this order to keep the codebase valid at each step:

### Step 1: Add `SyncTarget` ABC + remove `track_matcher()` from `Playlist`

Edit `playlists/__init__.py`:
- Add `class SyncTarget(ABC)` with `@staticmethod @abstractmethod track_matcher() -> Matcher`
- Remove `track_matcher()` from `class Playlist`

### Step 2: Update `SpotifyPlaylist` base classes

Edit `playlists/spotify_playlist.py`:
- Change `class SpotifyPlaylist(Playlist)` → `class SpotifyPlaylist(Playlist, SyncTarget)`
- Add `SyncTarget` to the import from `playlists`

### Step 3: Remove stubs from `LocalPlaylist`

Edit `playlists/local_playlist.py`:
- Delete the `track_matcher()` method
- Remove `from matchers import Matcher`

### Step 4: Remove stubs from `PlaylistMock`

Edit `tests/playlists/playlist_mock.py`:
- Delete the `track_matcher()` method
- Remove `from matchers import Matcher`
- Remove `from tests.matchers.matcher_mock import MatcherMock`

## Validation

Run all quality gates after all changes:

```bash
uv run mypy .
uv run ruff check .
uv run ruff format --check .
uv run pytest tests/
```

All four commands must exit with code 0 and zero errors.
