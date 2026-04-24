# Data Model: Deezer Integration via ARL

**Feature**: `007-deezer-integration`  
**Date**: 2026-04-24

---

## Entities

### DeezerTrack

Represents a track in the Deezer catalog. Wraps a raw GW dict (all-caps keys) or a
public-API response dict (lowercase keys). Data is stored on construction; no lazy-loading
is needed since the GW search and ISRC responses already contain all required fields.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `_track_id` | `str` | `SNG_ID` (GW) or `id` (API) | Deezer numeric track ID as string |
| `_data` | `dict[str, Any]` | GW or API response | Raw payload; stored for `isrc`, `track_number` |
| `service_name` | `str` (class const) | `"DEEZER"` | Used as ID3 tag key |
| `permalink` | `str` (property) | Derived | `https://www.deezer.com/track/{_track_id}` |
| `title` | `str` (property) | `SNG_TITLE` / `title` | |
| `artists` | `list[str]` (property) | `ART_NAME` / `artist.name` | Wrapped in a list |
| `album` | `str` (property) | `ALB_TITLE` / `album.title` | |
| `duration` | `float` (property) | `DURATION` (seconds, str→float) | |
| `track_number` | `int` (property) | `TRACK_NUMBER` / `track_position` | Defaults to `0` if absent |
| `isrc` | `str \| None` (property) | `ISRC` / `isrc` | Normalized (uppercase, no hyphens) |

**Relationships**: `DeezerTrack` is produced by `DeezerMatcher` and consumed by `DeezerPlaylist`.

**Validation rules**:
- `_track_id` must be a non-empty string of digits.
- `permalink` is derived and always well-formed when `_track_id` is valid.

**Inherits from**: `ServiceTrack` → `Track`

---

### DeezerPlaylist

Represents a Deezer user playlist. Manages a live connection to the Deezer API for
mutations; tracks are loaded lazily on first access.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `_playlist_id` | `str` | Constructor arg | Deezer numeric playlist ID |
| `_deezer` | `Deezer` | Constructor arg (injected) | Authenticated `deezer-py` Deezer facade |
| `_tracks` | `list[DeezerTrack]` | Lazy-loaded | Cleared on mutation |

**Key operations**:

| Method | Behaviour |
|--------|-----------|
| `tracks` (property) | Lazy-load via `dz.gw.get_playlist_tracks()`; cached until next mutation |
| `add_tracks(tracks)` | Calls `dz.gw.add_songs_to_playlist()`; invalidates `_tracks` cache |
| `remove_track(tracks)` | Calls `dz.gw.remove_songs_from_playlist()`; invalidates `_tracks` cache |
| `create(name, public, *, deezer)` | Class method; calls `dz.gw.create_playlist()`; returns new instance |
| `create_from_another_playlist(name, source, public, *, deezer, autopilot, embed_matches)` | Class method; highest-level import facade called by the `deezer import` CLI command; orchestrates `create()` → `import_tracks()` in a single call and returns the new `DeezerPlaylist` instance |
| `import_tracks(tracks, autopilot, embed_matches)` | Resolves and adds tracks using `DeezerMatcher` |
| `track_matcher()` | Static method; returns `DeezerMatcher.get_instance()` |

**Inherits from**: `Playlist` → `TrackCollection`, `SyncTarget`

---

### DeezerMatcher

Encapsulates the four-step track resolution strategy for the Deezer catalog.

**Resolution order** (per FR-008):
1. **Cached ref**: `LocalTrack.service_ref("DEEZER")` returns a well-formed Deezer track URL (any variant accepted by the `DeezerRef` acceptance regex) → normalise to canonical form via `_normalise_deezer_url()`, construct `DeezerTrack` from the extracted numeric ID.
2. **SKIP sentinel**: cached ref is `"SKIP"` → raise `SkipTrackError`.
3. **ISRC lookup**: call `dz.api.get_track_by_ISRC(track.isrc)` → if found, return `DeezerTrack`.
4. **Fuzzy search**: call `dz.gw.search("{artist} {title}")` → apply `_match_constraints()` → return best candidate or `None`.

| Field | Type | Notes |
|-------|------|-------|
| `_deezer` | `Deezer` | Injected on construction |
| `__instance` | `DeezerMatcher \| None` | Class-level singleton cache |

**Key methods**:

| Method | Signature | Notes |
|--------|-----------|-------|
| `get_instance()` | `classmethod → DeezerMatcher` | Singleton; calls `get_deezer_client()` |
| `match(track)` | `(Track) → DeezerTrack \| None` | Applies four-step resolution; raises `SkipTrackError` on SKIP |
| `_match_by_cached_ref(track)` | `(Track) → DeezerTrack \| None` | Step 1 |
| `_match_by_isrc(track)` | `(Track) → DeezerTrack \| None` | Step 3; catches network errors → warn, return None |
| `_match_by_fuzzy_search(track)` | `(Track) → DeezerTrack \| None` | Step 4; catches network errors → warn, return None |
| `suggest_match(track)` | `(Track) → list[DeezerTrack]` | Used in interactive mode |
| `match_list(tracks, autopilot, embed_matches)` | `(Iterable[Track], bool, bool) → list[Track]` | Iterates with progress bar |
| `_match_constraints(source, suggestion)` | `staticmethod (Track, Track) → bool` | **Inherited from `Matcher` base class** (moved from `SpotifyMatcher` per D2 resolution); non-Latin artist bypass included; thresholds match existing Spotify behaviour |

**Inherits from**: `Matcher`

---

### DeezerAPI (module: `api/deezer.py`)

Thin module providing the singleton authenticated `Deezer` facade.

| Symbol | Type | Notes |
|--------|------|-------|
| `get_deezer_client()` | `() → Deezer` | `@functools.cache` singleton; calls `login_via_arl`; raises `DeezerAuthenticationError` on failure |
| `DeezerAuthenticationError` | `Exception` subclass | Raised when `login_via_arl()` returns `False` or `GWAPIError` indicates auth failure; message never echoes the ARL |

---

### CompareResult

A lightweight value object returned by any two-playlist comparison function. Defined as a plain `@dataclass` in `src/playlists/__init__.py`.

```python
from dataclasses import dataclass
from tracks import Track

@dataclass
class CompareResult:
    source_only: list[Track]
    target_only: list[Track]
```

| Field | Type | Notes |
|-------|------|-------|
| `source_only` | `list[Track]` | Tracks present in the source/first playlist but absent from the target |
| `target_only` | `list[Track]` | Tracks present in the target/second playlist but absent from the source |

Neither side is constrained to `LocalTrack` or any specific subtype. Compare functions accept any two `TrackCollection` instances and return `CompareResult`:

```python
compare_playlists(...)        -> CompareResult  # source: LocalPlaylist, target: SpotifyPlaylist
compare_deezer_playlists(...) -> CompareResult  # source: LocalPlaylist, target: DeezerPlaylist
```

Replaces the `tuple[list[LocalTrack], list[SpotifyTrack]]` return type of the existing `compare_playlists()` function.

---

### DeezerRef (tag `TXXX:DEEZER`)

A string persisted in local audio file metadata.

| Value | Meaning |
|-------|----------|
| `https://www.deezer.com/track/<numeric-id>` | Valid — canonical form (written); accepted on read |
| `https://deezer.com/track/<numeric-id>` | Valid on read — no `www.`; normalised to canonical |
| `https://[www.]deezer.com/<locale>/track/<numeric-id>` | Valid on read — locale prefix; normalised to canonical |
| `https://[www.]deezer.com[/<locale>]/track/<numeric-id>?<query>` | Valid on read — query string present; stripped during normalisation |
| `"SKIP"` | Intentionally excluded — skip without prompting |
| absent / malformed | Unmatched — proceed with ISRC or fuzzy resolution |

**Acceptance regex** (read): `^https://(www\.)?deezer\.com(/[a-z]{2}(-[a-z]{2})?)?/track/(\d+)(\?.*)?$`

**Written (canonical) form**: always `https://www.deezer.com/track/<id>` — `www.` present, no locale, no query string. The numeric ID is extracted from any accepted variant and the canonical URL is reconstructed. `DeezerTrack.permalink` always returns this form.

Stored via `LocalTrack.embed_match(deezer_track)` (calls `_set_custom_tag("DEEZER", deezer_track.permalink)`) or by the CLI passing `--embed-matches`.

---

## State Transitions

```
LocalTrack (unmatched)
        │
        ▼
  DeezerMatcher.match()
        │
   ┌────┴─────────────────────┐
   │                          │
   ▼                          ▼
Cached TXXX:DEEZER URL?    SKIP sentinel?
   │                          │
   ▼ yes                      ▼ yes
DeezerTrack (from URL)    SkipTrackError
   │
   ▼ no
ISRC lookup
   │
   ├─ found ──► DeezerTrack (from API)
   │
   └─ not found / no ISRC
        │
        ▼
  Fuzzy search
        │
        ├─ above threshold + autopilot ──► DeezerTrack (auto-accepted)
        ├─ below threshold + manual ──► user prompt ──► DeezerTrack or skip
        └─ no results ──► None (logged warning)
```

---

## Modifications to Existing Entities

### `Config` (src/config/__init__.py)

New property:
```python
@property
def deezer_arl(self) -> str:
    return self.config.get("DEEZER", "ARL")
```

### `config_template.ini`

New section appended:
```ini
[DEEZER]
ARL=
```

### `LocalTrack` (src/tracks/local_track.py)

No changes required. `service_ref("DEEZER")` and `embed_match(deezer_track)` already work via the existing generic `_get_custom_tag` / `_set_custom_tag` infrastructure.
