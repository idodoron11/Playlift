# Feature Specification: Batch ISRC Prefetch in match_list

**Feature Branch**: `003-batch-isrc-prefetch`  
**Created**: 2026-04-07  
**Status**: Draft  
**Input**: User description: "Batch ISRC prefetch in match_list — eliminate N+1 API calls when embed_matches is True"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Embed Matches Without API Slowdown (Priority: P1)

A developer runs the sync tool with `--embed-matches` on a large playlist (50+ tracks). Currently,
writing ISRC tags back to local files triggers one extra network request per track because the ISRC
data is not always present in the object returned by a prior search. After this change, those
requests are batched into a single call (up to 50 tracks per batch), so the operation completes in
a fraction of the prior time.

**Why this priority**: This is the core pain point. Embedding ISRCs is the only scenario that
triggers the N+1 behaviour. Eliminating it is the entire goal of this feature.

**Independent Test**: Run `python main.py spotify import <m3u-file>` with `--embed-matches` on a
playlist containing 10+ unmatched tracks (no `SPOTIFY_REF` in ID3 tags). Observe that exactly one
external batch call is made for ISRC data, not one per track.

**Acceptance Scenarios**:

1. **Given** a playlist of N matched tracks where none have ISRC data cached locally, **When** the
   user runs sync with `--embed-matches`, **Then** the tool makes at most ⌈N/50⌉ batch network
   requests for ISRC data instead of N individual requests.
2. **Given** a playlist where all matched tracks already have ISRC data available in memory from
   the search step, **When** the user runs sync with `--embed-matches`, **Then** no additional
   network requests are made for ISRC data.
3. **Given** a playlist with more than 50 matched tracks, **When** the user runs sync with
   `--embed-matches`, **Then** the tracks are split into batches of 50 and each batch is fetched
   with one request, all ISRCs are correctly written to local files.

---

### User Story 2 - No Overhead When Not Embedding (Priority: P2)

A developer runs the sync tool without `--embed-matches`. The new batching logic must not execute
at all in this path — no extra API calls, no extra processing.

**Why this priority**: The existing non-embedding flow must remain unchanged to avoid regressions
and unintended quota usage.

**Independent Test**: Run sync without `--embed-matches` and verify that the Spotify `tracks` batch
endpoint is never called.

**Acceptance Scenarios**:

1. **Given** any playlist, **When** the user runs sync without `--embed-matches`, **Then** no batch
   ISRC prefetch request is made and behaviour is identical to the current implementation.

---

### Edge Cases

- What happens when a batch request fails for one or more tracks? — ISRC embedding for all tracks
  in that batch is skipped, a `WARNING` is logged with the affected track count, and `spotify_ref`
  is still written normally for all tracks.
- What happens when a matched `SpotifyTrack` already has ISRC data available in memory? — It is
  excluded from the batch; no redundant request is made for it.
- What happens when there are 0 matched tracks? — No batch request is made; the prefetch step is a
  no-op.
- What happens when the playlist has exactly 50 or 51 matched tracks? — Exactly 1 or 2 batch
  requests are made respectively (boundary condition).
- What happens when the Spotify batch response returns `null` for an individual track (deleted or
  unavailable)? — ISRC embedding is skipped for that track only, a `DEBUG` log entry is emitted,
  and remaining tracks in the batch are processed normally.

## Clarifications

### Session 2026-04-07

- Q: How should the system determine when a track is eligible to be skipped from the batch prefetch? → A: `_data` is loaded **and** `external_ids.isrc` is present in it — a non-null `_data` without `external_ids` still requires a batch fetch.
- Q: Should batch prefetch failures be surfaced to the user, and if so at what granularity? → A: Log a `WARNING` per failed batch (not per track), including the count of affected tracks.
- Q: How should the system handle a `null` item in an otherwise successful batch response (e.g. deleted/unavailable track)? → A: Skip ISRC embedding for that track only, log at `DEBUG` level, continue for remaining tracks in the batch.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: When `embed_matches` is `True`, the system MUST batch-fetch full track data for all
  chosen matches before writing any ISRC tags, using at most ⌈N/50⌉ network requests.
- **FR-002**: The system MUST skip tracks from the batch request only when their in-memory data
  object is loaded **and** contains a non-empty `external_ids.isrc` value. A track whose data is
  loaded but lacks `external_ids.isrc` MUST still be included in the batch.
- **FR-003**: When `embed_matches` is `False`, the system MUST NOT make any batch ISRC prefetch
  request.
- **FR-004**: A failure in a batch prefetch request MUST NOT prevent `spotify_ref` from being
  written to any track's local file. ISRC embedding is skipped for all tracks in the failed batch.
  The system MUST emit a single `WARNING` log entry for the failed batch, including the number of
  tracks whose ISRC could not be embedded.
- **FR-005**: The system MUST correctly handle playlists larger than 50 matched tracks by splitting
  them into sequential batches of at most 50 tracks each.
- **FR-007**: When a batch response contains a `null` item for a specific track ID, the system MUST
  skip ISRC embedding for that track only, emit a `DEBUG` log entry, and continue processing all
  remaining tracks in the batch.
- **FR-006**: After a successful prefetch, all subsequent reads of a matched track's ISRC MUST be
  served from memory with no additional network calls.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a playlist of N tracks all requiring ISRC data, the number of outgoing ISRC
  network requests is reduced from N to ⌈N/50⌉.
- **SC-002**: For a playlist of 100 tracks with `--embed-matches`, the total wall-clock time for
  ISRC embedding is reduced by at least 80% compared to the current implementation.
- **SC-003**: Running sync without `--embed-matches` produces zero additional network requests
  versus the current implementation.
- **SC-004**: All ISRCs are written correctly to local files — byte-for-byte identical to those
  written by the current implementation.

## Assumptions

- The Spotify API batch track endpoint accepts up to 50 track IDs per request and returns full
  track objects including ISRC data in the `external_ids` field — consistent with documented
  Spotify Web API behaviour.
- `embed_matches` is the only code path that requires ISRC data from Spotify; no other existing
  path is impacted by this change.
- Tracks matched via ISRC lookup (not fuzzy search) may already have their data populated with
  `external_ids`; the prefetch logic should detect and skip these to avoid redundant calls.
- Batch prefetch failures are non-fatal; the tool's primary purpose (syncing track URIs to
  Spotify) is not affected if ISRC back-fill fails for individual tracks.
