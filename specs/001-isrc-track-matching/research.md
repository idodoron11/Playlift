# Research: ISRC-Based Track Matching and Embedding

**Date**: 2026-04-04 | **Feature**: 001-isrc-track-matching

## Research Task 1: ISRC Tag Storage Across Audio Formats

**Question**: How is ISRC stored in mp3, flac, and m4a tags? Can the existing `_get_custom_tag`/`_set_custom_tag` pattern be reused?

### Findings

ISRC is stored as a **standard tag** in all three formats, not a custom tag:

| Format | Tag Frame | Key in mutagen | Notes |
|--------|-----------|----------------|-------|
| MP3 | `TSRC` (ID3v2.3+) | `TSRC` | Standard ID3 frame, not a `TXXX:` custom frame |
| FLAC | Vorbis comment `ISRC` | `isrc` | Standard Vorbis comment key |
| M4A/MP4 | No standard atom | `----:com.apple.iTunes:ISRC` | iTunes freeform tag (same pattern as SPOTIFY) |

**Decision**: Use a **hybrid approach**:
- For **MP3**: Read/write the standard `TSRC` frame (not `TXXX:ISRC`), since ISRC has its own dedicated ID3 frame. Use `mutagen.id3.TSRC` class.
- For **FLAC**: Use `music_tag`'s standard tag access with key `"isrc"` — it maps to the Vorbis `ISRC` comment.
- For **M4A**: Reuse the existing `_get_custom_tag`/`_set_custom_tag` pattern since M4A uses freeform iTunes tags for ISRC anyway.

**Rationale**: Using the standard `TSRC` frame for MP3 ensures compatibility with other music software that reads ISRC from the standard field. The `_get_custom_tag` pattern uses `TXXX:` which would store it as a non-standard custom tag that other tools wouldn't recognize.

**Alternative considered**: Using `_get_custom_tag("ISRC")` uniformly for all formats. Rejected because MP3 files already have a standard `TSRC` frame for ISRC, and storing it in `TXXX:ISRC` would create a non-standard location that other tools wouldn't find.

## Research Task 2: Spotify Search API `isrc:` Query Behavior

**Question**: How does the Spotify Search API respond to `isrc:` queries? What's the response shape when there are 0, 1, or multiple results?

### Findings

- **Query syntax**: `SpotifyAPI.get_instance().search("isrc:USRC17607839", limit=1)`
- **Response shape**: Same as regular search — `response["tracks"]["items"]` is a list
- **0 results**: `response["tracks"]["total"] == 0`, `items` is empty list
- **1 result**: `items` has exactly 1 track dict (most common case for ISRC)
- **Multiple results**: Rare but possible (reissues, compilations with same ISRC). `items` returns multiple tracks; spec says use first result.
- **ISRC not found in catalog**: Same as 0 results — empty items list
- **Regional availability**: Spotify may return the track even if not available in user's market; playback would fail but search succeeds. The spec says fall back to fuzzy in this case, but detecting this reliably is complex. Simplification: accept the first result. Regional filtering is out of scope.

**Decision**: Reuse the existing `SpotifyMatcher._search()` static method with the `isrc:` query string. It already handles the response parsing and returns `list[SpotifyTrack]`. Take `[0]` if non-empty; otherwise fall back.

**Alternative considered**: Adding a dedicated `search_by_isrc()` method to `SpotifyAPI`. Rejected because `SpotifyAPI` is a thin singleton wrapper around `spotipy.Spotify` — adding methods to it is an anti-pattern. The search call belongs in `SpotifyMatcher` where all search logic lives.

## Research Task 3: ISRC Availability on Spotify Track Objects

**Question**: Does the Spotify API always return ISRC in track metadata? Where is it in the response dict?

### Findings

- **Location**: `track_data["external_ids"]["isrc"]`
- **Availability**: Present on virtually all tracks. The `external_ids` dict may also contain `ean` and `upc` codes.
- **Sparse data tracks**: Some tracks (e.g., local files uploaded to Spotify, podcast episodes) may not have `external_ids` at all. Safe access required.
- **Response from search vs. track endpoint**: Search results include `external_ids` in the track items, so no additional API call needed when matching via fuzzy search.

**Decision**: Add an `isrc` property to `SpotifyTrack` that reads `self.data.get("external_ids", {}).get("isrc")`. Returns `str | None`.

## Research Task 4: ISRC Format Validation

**Question**: What's the exact ISRC format, and should validation be case-sensitive?

### Findings

- **Official format**: 12 characters: `CC` (2-letter country) + `XXX` (3-char registrant) + `YY` (2-digit year) + `NNNNN` (5-digit designation)
- **Pattern**: `^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$` (12 chars total, as specified in spec)
- **Case**: ISRCs are officially uppercase, but tags in the wild may store them in mixed case
- **Hyphens**: The display format uses hyphens (`US-RC1-23-00001`) but the stored format in tags is typically without hyphens (`USRC12300001`)

**Decision**: Normalize ISRC to uppercase and strip hyphens before validation. Validate against `^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$`. Define as module-level constant `ISRC_PATTERN`.

**Alternative considered**: Strict case match only. Rejected because real-world tags frequently store ISRCs in mixed case.

## Summary of Decisions

| Topic | Decision |
|-------|----------|
| ISRC tag reading (MP3) | Standard `TSRC` frame via mutagen |
| ISRC tag reading (FLAC) | `music_tag` standard `"isrc"` key |
| ISRC tag reading (M4A) | `_get_custom_tag("ISRC")` (freeform iTunes tag) |
| ISRC tag writing | Same split: `TSRC` for MP3, `music_tag` for FLAC, `_set_custom_tag` for M4A |
| Spotify ISRC lookup | `SpotifyMatcher._search("isrc:{code}")` — reuse existing search infra |
| SpotifyTrack ISRC | New property: `self.data.get("external_ids", {}).get("isrc")` |
| Validation | Normalize to uppercase, strip hyphens, validate `^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$` |
| No new classes | All changes are property/method additions to existing classes |
