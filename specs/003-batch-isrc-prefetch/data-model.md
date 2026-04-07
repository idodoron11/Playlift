# Data Model: Batch ISRC Prefetch in match_list

**Feature**: `003-batch-isrc-prefetch`  
**Date**: 2026-04-07

---

## Overview

This feature introduces no new entities, no new persistent data, and no schema changes.
It optimises an in-memory data flow within `SpotifyMatcher.match_list`.

---

## Existing Entities Involved

### `SpotifyTrack`

**Location**: `tracks/spotify_track.py`

| Field | Type | Description |
|-------|------|-------------|
| `_id` | `str` | Spotify track ID (extracted from URL at construction) |
| `_data` | `dict[str, Any] \| None` | Lazily-loaded full track object from the Spotify API. `None` until first accessed or explicitly set. |

**Key property accessed by this feature**:

```
_data["external_ids"]["isrc"]  →  str | None
```

**Mutability**: `_data` is set in-place by `_prefetch_isrc_data`. Once set, it satisfies
all subsequent reads of `.isrc`, `.artists`, `.title`, etc. with no network call.

---

### `LocalTrack`

**Location**: `tracks/local_track.py`

| Field | Type | Description |
|-------|------|-------------|
| `isrc` (property) | `str \| None` | Read from / written to format-appropriate tag (TSRC for MP3, Vorbis `isrc` for FLAC, iTunes freeform for M4A) |
| `spotify_ref` (property) | `str \| None` | Stored as ID3 `TXXX:SPOTIFY_REF` |

**Write path triggered by this feature** (unchanged in behaviour, optimised in timing):
After prefetch, `LocalTrack.isrc = match.isrc` writes the normalised ISRC to the local file.

---

## Data Flow (post-feature)

```
match_list(tracks, embed_matches=True)
        │
        ▼
Pass 1: User review loop
        │  collects →  pairs_to_embed: list[tuple[Track, SpotifyTrack]]
        ▼
_prefetch_isrc_data(chosen_matches)
        │
        ├── filter: SpotifyTrack objects lacking external_ids.isrc in _data
        ├── de-duplicate IDs  →  id_to_tracks: dict[str, list[SpotifyTrack]]
        ├── chunk into batches of SPOTIFY_BATCH_SIZE (50)
        ├── call SpotifyAPI.get_instance().tracks(batch_ids)  [1 call per batch]
        └── mutate _data on each SpotifyTrack in id_to_tracks[track_id]
        │
        ▼
Pass 2: Embed loop
        │
        └── _update_spotify_match_in_source_track(source_track, match)
                 → match.isrc  [served from _data, no network call]
                 → source_track.isrc = normalised_isrc  [writes to local file]
```

---

## Constant

| Name | Value | Location | Rationale |
|------|-------|----------|-----------|
| `SPOTIFY_BATCH_SIZE` | `50` | `matchers/spotify_matcher.py` (module level) | Spotify Web API hard limit for `/tracks` endpoint |

---

## State Transitions for `SpotifyTrack._data`

| Before prefetch | Condition | After prefetch |
|-----------------|-----------|----------------|
| `None` | Track was built from cached `spotify_ref` only | Full track object with `external_ids.isrc` |
| `{...}` without `external_ids.isrc` | Populated from search result that omitted `external_ids` | Full track object with `external_ids.isrc` |
| `{...}` with `external_ids.isrc` present | Already complete | Unchanged (excluded from batch) |
| Any | Batch request failed | Unchanged (error logged, no mutation) |
| Any | Spotify returns `None` for this track ID | Unchanged (`DEBUG` logged, no mutation) |
