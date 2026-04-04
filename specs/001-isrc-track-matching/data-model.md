# Data Model: ISRC-Based Track Matching and Embedding

**Date**: 2026-04-04 | **Feature**: 001-isrc-track-matching

## Entities

### LocalTrack (modified)

Existing entity. Additions:

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `isrc` | `str \| None` | Audio file tag | Read from `TSRC` (MP3), `isrc` Vorbis comment (FLAC), `----:com.apple.iTunes:ISRC` (M4A). `None` if absent or empty. |

**Behavior**:
- Read: Normalize to uppercase, strip hyphens; return `None` if tag absent
- Write: Only when `embed_matches` is active (or `match` command); only if current value is `None`; log warning on write failure
- Validation: Not done at the property level; validation is the matcher's responsibility before attempting lookup

### SpotifyTrack (modified)

Existing entity. Additions:

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `isrc` | `str \| None` | `data["external_ids"]["isrc"]` | `None` if `external_ids` missing or no `isrc` key. Read-only. |

### ISRC Value Object (no new class)

Not a separate class — just a `str` that passes format validation:
- Pattern: `^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$`
- 12 characters, uppercase, no hyphens (normalized from storage)
- Defined as module constant `ISRC_PATTERN` in `matchers/spotify_matcher.py`

### Match Result (conceptual — no new class)

The matching flow produces a `SpotifyTrack | None`. The method used (ISRC vs. fuzzy) is logged but not stored in the return type. No new data structure needed.

## Relationships

```
LocalTrack --[has tag]--> ISRC (str | None)
SpotifyTrack --[has field]--> ISRC (str | None)
SpotifyMatcher --[reads]--> LocalTrack.isrc
SpotifyMatcher --[reads]--> SpotifyTrack.isrc
SpotifyMatcher --[writes]--> LocalTrack.isrc (via embed)
```

## State Transitions

### LocalTrack.isrc Lifecycle

```
[No ISRC tag] --(matched + embed active)--> [ISRC written from SpotifyTrack]
[ISRC present] --(any match run)--> [ISRC unchanged — FR-006 no-overwrite]
[ISRC present, malformed] --(match run)--> [ISRC unchanged; skipped for lookup]
```

### Matching Flow State

```
track.spotify_ref exists? --> YES: return existing match (no ISRC involved)
                          --> "SKIP": raise SkipTrackException
                          --> NO: check track.isrc
                                    |
                            isrc valid? --> YES: search by ISRC
                                        |         |
                                        |   found? --> YES: return match (log: "matched via ISRC")
                                        |         --> NO: fall through to fuzzy
                                        --> NO: skip to fuzzy
                                    |
                              fuzzy search (existing logic)
                                    |
                              embed ISRC if conditions met
```

## Validation Rules

| Rule | Where Enforced |
|------|----------------|
| ISRC format: `^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$` | `SpotifyMatcher` before lookup |
| No overwrite of existing ISRC tag | `SpotifyMatcher._update_spotify_match_in_source_track` |
| Write gated by `embed_matches` | `SpotifyMatcher.match_list` (already gates `_update_*`) |
| Write failure is non-fatal | `LocalTrack._set_custom_tag` (already catches and logs) |
