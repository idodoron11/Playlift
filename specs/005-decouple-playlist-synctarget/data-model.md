# Data Model: Decouple Playlist from SyncTarget

**Feature**: 005-decouple-playlist-synctarget  
**Date**: 2026-04-21

## Type Hierarchy

### Before (current)

```
TrackCollection (ABC)
  └── Playlist (ABC)
        ├── tracks: Iterable[Track]         (abstract property)
        ├── track_matcher() -> Matcher      (abstract static)  ← PROBLEM
        ├── remove_track(list[Track])        (abstract)
        └── add_tracks(Track)                (abstract)
              ├── LocalPlaylist              (raises TypeError on track_matcher)
              ├── SpotifyPlaylist            (returns SpotifyMatcher.get_instance())
              └── PlaylistMock [test]        (returns MatcherMock.get_instance())
```

### After (target)

```
TrackCollection (ABC)
  └── Playlist (ABC)
        ├── tracks: Iterable[Track]         (abstract property)
        ├── remove_track(list[Track])        (abstract)
        └── add_tracks(Track)                (abstract)
              ├── LocalPlaylist              ← Playlist only
              ├── SpotifyPlaylist ──┐        ← Playlist + SyncTarget
              └── PlaylistMock     │ [test]  ← Playlist only
                                   │
SyncTarget (ABC)  ─────────────────┘
  └── track_matcher() -> Matcher   (abstract static)
```

## Entities

### `SyncTarget` (new ABC)

| Attribute | Type | Description |
|-----------|------|-------------|
| `track_matcher()` | `@staticmethod -> Matcher` | Returns the matcher instance for this sync destination platform |

- **Defined in**: `playlists/__init__.py`
- **Inherits from**: `ABC` only (fully orthogonal to `Playlist` and `TrackCollection`)
- **Implemented by**: `SpotifyPlaylist`
- **NOT implemented by**: `LocalPlaylist`, `PlaylistMock`

### `Playlist` (modified ABC)

| Change | Detail |
|--------|--------|
| Removed | `track_matcher() -> Matcher` abstract static method |
| Kept | `tracks` (abstract property), `remove_track()`, `add_tracks()` |

### `SpotifyPlaylist` (modified concrete class)

| Change | Detail |
|--------|--------|
| Base classes | `Playlist` → `Playlist, SyncTarget` |
| `track_matcher()` | Body unchanged — returns `SpotifyMatcher.get_instance()` |
| Import added | `from playlists import SyncTarget` |

### `LocalPlaylist` (modified concrete class)

| Change | Detail |
|--------|--------|
| Removed | `track_matcher()` static method (was raising `TypeError`) |
| Removed | `from matchers import Matcher` import |

### `PlaylistMock` (modified test double)

| Change | Detail |
|--------|--------|
| Removed | `track_matcher()` static method |
| Removed | `from matchers import Matcher` import |
| Removed | `from tests.matchers.matcher_mock import MatcherMock` import |

## Relationships

- `SyncTarget` ↔ `Playlist`: No inheritance relationship (orthogonal ABCs)
- `SyncTarget` → `Matcher`: Declares return type dependency
- `SpotifyPlaylist` → `Playlist`: Inherits track collection contract
- `SpotifyPlaylist` → `SyncTarget`: Inherits sync destination contract
- `LocalPlaylist` → `Playlist`: Inherits track collection contract only

## State Transitions

N/A — no state machines or lifecycle changes in this refactoring.

## Validation Rules

- `SyncTarget` must have exactly one abstract method (`track_matcher`)
- Any class inheriting `SyncTarget` must implement `track_matcher()` returning a `Matcher`
- Any class inheriting `Playlist` (without `SyncTarget`) must NOT be required to implement `track_matcher()`
