# Feature Specification: ISRC-Based Track Matching and Embedding

**Feature Branch**: `001-isrc-track-matching`  
**Created**: 2026-04-04  
**Status**: Draft  
**Input**: User description: "I want to start use ISRCs for track identification and matching. Today, we use a fuzzy search, to match the local track to the spotify track using its title, artist and album. However, if the track already has an ISRC embedded in its tags (mp3, flac or m4a), we can use it directly. This is a much more reliable info to use for track matching. We can first try to match the track using its ISRC, and fallback to fuzzy search if it fails. In addition, once a track is matched, we should embed the ISRC in the local track's tags (if it is not already embedded)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - ISRC-Based Track Matching (Priority: P1)

A user imports or syncs a playlist, or runs a match pass. Some local tracks already have ISRC codes stored in their audio tags (from a previous rip, download, or from an earlier run). Instead of performing a fuzzy text search, the system reads the ISRC from the tag and looks up the Spotify track directly using that code. The match is returned instantly and with certainty — no guessing based on title/artist spelling variations.

**Why this priority**: This is the core value of the feature. ISRC matching is deterministic — one code maps to exactly one recording. It eliminates false positives from fuzzy search (e.g., a live version matching instead of the studio version) and is especially valuable for tracks with non-Latin names where fuzzy search is least reliable.

**Independent Test**: Can be fully tested by running an import (or sync, or match) on a playlist containing only tracks with ISRC tags and verifying that all matches are found without any fuzzy search being invoked.

**Acceptance Scenarios**:

1. **Given** a local track has a valid ISRC in its tags, **When** the matching process is triggered, **Then** the system uses the ISRC to find the Spotify track without performing a fuzzy search.
2. **Given** a local track has a valid ISRC in its tags, **When** the ISRC lookup returns a Spotify track, **Then** the returned track is used as the match result.
3. **Given** a local track has a valid ISRC in its tags, **When** the ISRC lookup returns no result, **Then** the system falls back to fuzzy search using title, artist, and album.
4. **Given** a local track has a malformed or empty ISRC tag (i.e., does not match `^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$`), **When** the matching process is triggered, **Then** the system skips ISRC lookup and proceeds directly with fuzzy search.

---

### User Story 2 - Fuzzy Search Fallback (Priority: P2)

A user imports a playlist where many local tracks have no ISRC in their tags (common for older rips or manually organized libraries). The system behaves exactly as before — fuzzy search is performed using title, artist, and album metadata — so existing functionality is fully preserved.

**Why this priority**: This ensures backward compatibility. The feature must not regress existing behavior for tracks without ISRCs. Every track without an ISRC must still go through the proven fuzzy matching path.

**Independent Test**: Can be fully tested by running an import (or sync, or match) on a playlist where no local tracks have ISRC tags and verifying that all matches proceed via fuzzy search as they did before this feature.

**Acceptance Scenarios**:

1. **Given** a local track has no ISRC tag, **When** the matching process is triggered, **Then** the system performs the existing fuzzy search using title, artist, and album.
2. **Given** a local track's ISRC lookup fails to find a match, **When** the system falls back to fuzzy search, **Then** the fuzzy search result is used as the match outcome.

---

### User Story 3 - ISRC Embedding After Match (Priority: P3)

After a local track is successfully matched to a Spotify track — whether via ISRC lookup or fuzzy search — the system writes the Spotify track's ISRC back into the local file's tags, if the ISRC is not already present. For `spotify match`, embedding always occurs (it is the command's purpose). For `spotify import` and `spotify sync`, embedding occurs only when `--embed-matches` is active. On the next run, that track can be matched via ISRC directly, skipping fuzzy search entirely.

**Why this priority**: This is a compounding improvement: each sync run enriches the local library. Over time, the proportion of tracks matched via fast ISRC lookup grows, and the dependency on imprecise fuzzy search decreases. It also acts as a persistent quality signal — ISRC-tagged tracks were verified against Spotify's catalog.

**Independent Test**: Can be fully tested by running an import on a playlist of untagged tracks, then verifying that after the run each matched local file has acquired an ISRC tag. A second run on the same playlist should then resolve all matches via ISRC.

**Acceptance Scenarios**:

1. **Given** a local track is successfully matched and its file has no ISRC tag, **When** the match is confirmed, **Then** the Spotify track's ISRC is written to the local file's tags.
2. **Given** a local track already has an ISRC tag, **When** the match is confirmed, **Then** the existing ISRC tag is left unchanged (no overwrite).
3. **Given** a match is confirmed but the local file cannot be written to (e.g., read-only), **When** the embedding step is attempted, **Then** a warning is logged and the sync continues without failure.
4. **Given** a local track is skipped (marked as SKIP), **When** no match is performed, **Then** no ISRC is written.

---

### Edge Cases

- What happens when a local track has an ISRC that exists in Spotify's catalog but the recording is not available in the user's regional market? → Fall back to fuzzy search.
- What happens when two Spotify tracks share the same ISRC (rare with reissues or compilations)? → Use the first result returned by the catalog.
- What happens when an ISRC tag is structurally valid (12 characters) but returns no catalog result? → Fall back to fuzzy search, log a warning with the ISRC value.
- What happens when the ISRC lookup fails due to a network or API error? → Treat as a non-match: fall back to fuzzy search and log a warning. The sync run is not aborted.
- What happens when a track is matched via fuzzy search and the matched Spotify track has no ISRC in its metadata? → Skip embedding; do not write an empty tag.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST read any existing ISRC value from a local track's audio tags (mp3, flac, and m4a formats) before initiating the matching process.
- **FR-002**: If an ISRC is found in the local track's tags, the system MUST validate its format (12-character alphanumeric string matching the pattern `^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$`) before attempting lookup. Only a structurally valid ISRC triggers a Spotify lookup; an invalid value is treated as absent and falls back to fuzzy search.
- **FR-003**: If the ISRC lookup yields a match, the system MUST use that result as the track match and skip fuzzy search for that track.
- **FR-004**: If the local track has no ISRC tag, the ISRC lookup returns no result, or the ISRC lookup fails due to a network or API error, the system MUST fall back to the existing fuzzy search using the track's title, artist, and album metadata. API or network errors MUST be logged as warnings and MUST NOT abort the sync.
- **FR-005**: After a successful match (via either ISRC lookup or fuzzy search), the system MUST write the matched Spotify track's ISRC into the local file's tags, provided the local file does not already have an ISRC tag, under these conditions: (a) always, when the command is `spotify match`; (b) only when `--embed-matches` is active, for `spotify import` and `spotify sync`. If the embedding condition is not met, no ISRC is written.
- **FR-006**: The system MUST NOT overwrite an existing ISRC tag on a local file.
- **FR-007**: If writing the ISRC tag to a local file fails for any reason, the system MUST log a warning and continue the sync without treating the write failure as a blocking error.
- **FR-008**: The system MUST indicate via `INFO`-level logging whether each track was matched via ISRC lookup or fuzzy search.

### Key Entities

- **ISRC (International Standard Recording Code)**: A 12-character alphanumeric code uniquely identifying a specific audio recording. Stored in local track tags and present in Spotify track metadata. Format: `CC-XXX-YY-NNNNN`.
- **Local Track**: An audio file (mp3, flac, or m4a) with embedded metadata tags. May carry an ISRC tag from a prior sync, a ripping tool, or a download service.
- **Spotify Track**: A track in the Spotify catalog, always associated with an ISRC in its metadata. The target of the matching process.
- **Match Result**: The outcome of the matching process for a given local track — a confirmed Spotify track reference (or SKIP), annotated with the method used (ISRC or fuzzy).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Local tracks with valid ISRC tags are matched without any fuzzy text comparison being performed — confirmed by observing zero fuzzy search invocations for those tracks.
- **SC-002**: Tracks that previously failed fuzzy matching due to title/artist encoding issues (e.g., Cyrillic, CJK characters) are successfully matched if their ISRC is present in their tags.
- **SC-003**: After a completed import or sync run with `--embed-matches` active, every matched local track that lacked an ISRC tag now has one written to its file — confirmed by reading tags after the run.
- **SC-004**: A second sync run on the same playlist (with `--embed-matches` active on the first run) resolves a higher proportion of tracks via ISRC lookup than the first run did, demonstrating the compounding improvement from embedding.
- **SC-005**: No regressions in match results for tracks that had no ISRC tag — they continue to be matched (or not) with the same outcome as before this feature.

## Clarifications

### Session 2026-04-04

- Q: Should ISRC embedding follow the existing `--embed-matches` flag or always happen on every match? → A: Follow the `--embed-matches` flag — consistent with how `SPOTIFY_REF` is written.
- Q: Should an API/network error during ISRC lookup propagate or fall back to fuzzy search? → A: Fall back to fuzzy search and log a warning; sync continues.
- Q: Should the system validate the ISRC format before attempting a Spotify lookup, or attempt with any non-empty string? → A: Validate format (`^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$`) first; skip lookup and fall back to fuzzy if invalid.
- Q: Does ISRC-based matching apply to `import` only, or also `sync` and `match`? → A: All three commands trigger the same matching logic for tracks without a `SPOTIFY_REF`; ISRC matching applies uniformly to any unmatched track regardless of which command triggered it.
- Q: Should `spotify match` get a `--embed-matches` flag for ISRC embedding, or leave it as-is? → A: Leave as-is — `match` always embeds unconditionally by design; no flag needed.

## Assumptions

- Local audio files are writable in the common case; read-only files are treated as an exceptional case handled gracefully with a warning.
- The Spotify catalog API supports lookup of tracks by ISRC (confirmed: Spotify's Search API supports `isrc:` query syntax).
- An ISRC stored in a local track's tags is validated for structural format (`^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$`) but is otherwise trusted as correct. No validation against the track's actual audio content is performed.
- ISRC embedding uses the same tag-writing mechanism already in place for writing `SPOTIFY_REF` tags (`music-tag` library); no new I/O library is required.
- The feature applies to all three supported audio formats (mp3, flac, m4a); "m4a" refers to the MP4 container format and covers both AAC and ALAC audio codecs — both use the same iTunes freeform tag (`----:com.apple.iTunes:ISRC`) for ISRC storage; format-specific ISRC tag field names are handled transparently by the existing tag library.
- Matching behavior for tracks explicitly marked as `SKIP` is unchanged — no ISRC lookup or embedding is performed for those tracks.
