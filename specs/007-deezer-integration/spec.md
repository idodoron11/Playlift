# Feature Specification: Deezer Integration via ARL

**Feature Branch**: `007-deezer-integration`  
**Created**: 2026-04-24  
**Status**: Draft  
**Input**: User description: "Deezer Integration via ARL — sync/import/match local playlists and tracks to Deezer"

## Clarifications

### Session 2026-04-24

- Q: What format should be stored in the `TXXX:DEEZER` tag? → A: Always write the canonical form `https://www.deezer.com/track/<id>` (with `www.`, no locale, no query string). On read, accept any Deezer track URL variant — `www.` optional, locale segment optional, query string optional (e.g., `https://deezer.com/en/track/12345?utm_source=sharing`) — extract the numeric ID, and normalise to the canonical form before use.
- Q: How should transient network errors be handled during matching or playlist operations? → A: Log a warning for the failed track/operation and continue with the rest
- Q: Should the ARL cookie value appear in log output or error messages? → A: Never — the ARL must not be included in any log, error message, or terminal output
- Q: When `deezer import` is run for a playlist whose name already exists on Deezer, what should happen? → A: Always create a new playlist; `import` never overwrites an existing one (use `sync` to update)

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Import a local playlist to Deezer (Priority: P1)

A user has a local `.m3u` playlist and wants to create a matching Deezer playlist. They run `deezer import` with a path to the `.m3u` file. The tool resolves each track to a Deezer catalog entry (see User Stories 6–8 for resolution rules), creates a new Deezer playlist, and adds all matched tracks. Matched IDs are optionally written back as `TXXX:DEEZER` tags.

**Why this priority**: This is the core value proposition — bridging local music libraries and Deezer. All other commands depend on the concepts introduced here.

**Independent Test**: Can be fully tested by pointing `deezer import` at a small `.m3u` file and verifying a new Deezer playlist is created with the expected tracks. Delivers standalone value without any other Deezer command being implemented.

**Acceptance Scenarios**:

1. **Given** a valid `.m3u` file and a configured ARL, **When** `deezer import <playlist.m3u>` is run, **Then** a new Deezer playlist is created containing all matched tracks.
2. **Given** `--embed-matches` is passed, **When** a track is matched, **Then** `TXXX:DEEZER` is written to the local audio file.
3. **Given** `--autopilot` is passed and a match confidence is above the configured threshold, **When** matching runs, **Then** the match is accepted automatically without user prompt.
4. **Given** `--public` is passed, **When** the playlist is created, **Then** the Deezer playlist is created as public; otherwise it defaults to private.

---

### User Story 2 — Sync a local playlist to an existing Deezer playlist (Priority: P2)

A user has already imported a playlist to Deezer and wants to keep it in sync with an updated local `.m3u` file. They run `deezer sync` with the local file path and the Deezer playlist URI/ID. The command adds tracks that are in the local file but missing from Deezer, removes tracks present in Deezer but absent from the local file, and optionally writes resolved `TXXX:DEEZER` tags back to local files.

**Why this priority**: Ongoing sync is the most frequent usage after an initial import; without it users would need to recreate playlists from scratch after every local edit.

**Independent Test**: Can be fully tested by modifying a `.m3u` file after a previous import and verifying the Deezer playlist reflects the additions and removals.

**Acceptance Scenarios**:

1. **Given** a local playlist with new tracks not yet in the Deezer playlist, **When** `deezer sync <playlist.m3u> <deezer-playlist-id>` runs, **Then** the missing tracks are added to the Deezer playlist.
2. **Given** the Deezer playlist contains tracks that were removed from the local `.m3u`, **When** sync runs, **Then** those tracks are removed from the Deezer playlist.
3. **Given** `--embed-matches` is passed, **When** a track is resolved during sync, **Then** `TXXX:DEEZER` is written to the local audio file.
4. **Given** `--sort-tracks` is passed, **When** sync completes, **Then** the Deezer playlist track order matches the local `.m3u` order.
5. **Given** `--from-path`/`--to-path` remapping flags are passed, **When** sync resolves file paths, **Then** the path prefix is substituted before looking up local files.

---

### User Story 3 — Pre-populate match tags without touching Deezer (Priority: P2)

A user wants to review or cache Deezer track matches before committing to an import or sync. They run `deezer match` against one or more `.m3u` files. The command resolves each track's Deezer match and always writes `TXXX:DEEZER` tags to the local files — embedding is unconditional for this command. It does not create or modify any Deezer playlist.

**Why this priority**: Matching can be slow (network calls); pre-populating tags makes subsequent import/sync faster and lets users manually review matches (e.g., set `"SKIP"`) before syncing.

**Independent Test**: Can be fully tested by running `deezer match` and verifying that `TXXX:DEEZER` tags are written to the local files and no Deezer playlist is created or modified.

**Acceptance Scenarios**:

1. **Given** a local `.m3u` file with unmatched tracks, **When** `deezer match` runs, **Then** `TXXX:DEEZER` tags are written to all auto-resolved tracks.
2. **Given** a track already has a `TXXX:DEEZER` tag, **When** `deezer match` runs, **Then** the existing tag is preserved and no new lookup is performed.
3. **Given** a match cannot be found for a track, **When** matching completes, **Then** the track is skipped with a logged warning and no tag is written.

---

### User Story 4 — Compare a local playlist against a Deezer playlist (Priority: P3)

A user wants to audit differences between their local `.m3u` and an existing Deezer playlist. They run `deezer compare` and receive a human-readable diff showing tracks present in one but not the other.

**Why this priority**: Auditing is useful but not blocking; users can get value from import/sync without it.

**Independent Test**: Can be fully tested by deliberately adding a track to the Deezer playlist that is absent from the local file and verifying it appears in the compare output.

**Acceptance Scenarios**:

1. **Given** a local `.m3u` and a Deezer playlist URI, **When** `deezer compare` runs, **Then** the output lists tracks only in the local file and tracks only in Deezer separately.
2. **Given** both sides are identical, **When** compare runs, **Then** the output reports no differences.

---

### User Story 5 — Detect duplicate tracks in a local playlist (Priority: P3)

A user suspects they have duplicated tracks in a `.m3u` file (same `TXXX:DEEZER` value appearing more than once). Running `deezer duplicates` reports all duplicate groups.

**Why this priority**: Utility feature; low-friction but not critical to core sync workflow.

**Independent Test**: Can be fully tested by creating a `.m3u` with two entries sharing the same `TXXX:DEEZER` tag value and verifying both appear in the duplicates report.

**Acceptance Scenarios**:

1. **Given** a local `.m3u` file where two tracks share the same `TXXX:DEEZER` value, **When** `deezer duplicates` runs, **Then** both tracks are reported as duplicates.
2. **Given** no duplicate `TXXX:DEEZER` values exist, **When** `deezer duplicates` runs, **Then** the output reports no duplicates.

---

### User Story 6 — Honor a cached TXXX:DEEZER tag in all matching operations (Priority: P1)

A user has already run `deezer match` (or a prior import with `--embed-matches`) and their local audio files have `TXXX:DEEZER` tags. Any subsequent command that invokes the matcher must read the cached tag first and use it directly, skipping all network lookups. If the tag value is `"SKIP"`, the track is silently excluded from Deezer operations.

**Why this priority**: Cached tags are the fastest and most reliable resolution path. Respecting them across all commands is fundamental to the tool's usability and prevents unnecessary Deezer API calls on every run.

**Independent Test**: Can be fully tested independently of any specific command by pre-setting `TXXX:DEEZER` on local files and running any matching operation (import/sync/match), then verifying no Deezer search API call is made.

**Acceptance Scenarios**:

1. **Given** a local track has a valid `TXXX:DEEZER` tag, **When** any matching operation runs, **Then** the cached reference is used directly and no ISRC lookup or fuzzy search is performed.
2. **Given** a local track has `TXXX:DEEZER` set to `"SKIP"`, **When** any matching operation runs, **Then** the track is excluded from all Deezer playlist operations without prompting or logging an error.
3. **Given** a local track has a `TXXX:DEEZER` tag containing a malformed or unrecognisable value, **When** matching runs, **Then** the tag is treated as absent and the matcher proceeds to ISRC lookup or fuzzy search.

---

### User Story 7 — Resolve an unmatched track via ISRC lookup (Priority: P1)

A user's local audio files carry ISRC metadata. When a track has no valid cached `TXXX:DEEZER` tag, the matcher uses the ISRC to query the Deezer catalog for an exact match, avoiding the uncertainty of fuzzy search.

**Why this priority**: ISRC lookup yields a deterministic, exact match with 100% accuracy when the track is in the Deezer catalog. It is the primary resolution path for unmatched tracks and affects all five commands.

**Independent Test**: Can be fully tested by providing a local track with a known ISRC, no `TXXX:DEEZER` tag, and verifying the matcher returns the correct Deezer track without invoking fuzzy search.

**Acceptance Scenarios**:

1. **Given** a local track has no valid `TXXX:DEEZER` tag and has an ISRC that exists in the Deezer catalog, **When** matching runs, **Then** the track is matched via ISRC lookup and fuzzy search is not invoked.
2. **Given** a local track has an ISRC that is not found in the Deezer catalog, **When** ISRC lookup completes, **Then** the matcher falls through to fuzzy search.
3. **Given** a local track has no ISRC tag at all, **When** matching runs, **Then** ISRC lookup is skipped and fuzzy search is used directly.

---

### User Story 8 — Resolve an unmatched track via fuzzy search (Priority: P2)

A user's local audio files lack ISRC metadata, or the ISRC produced no result. The matcher falls back to a fuzzy title/artist search against the Deezer catalog, presenting the best candidate for user confirmation (or auto-accepting it in `--autopilot` mode).

**Why this priority**: Fuzzy search is the last-resort fallback and handles the majority of real-world cases where ISRC is unavailable. It is less deterministic than ISRC lookup, so user confirmation or a confidence threshold gate is required.

**Independent Test**: Can be fully tested by providing a local track with no ISRC and no cached `TXXX:DEEZER` tag, then verifying a fuzzy search is issued and the returned candidate is presented for confirmation.

**Acceptance Scenarios**:

1. **Given** a local track has no valid `TXXX:DEEZER` tag and no resolvable ISRC, **When** matching runs, **Then** a fuzzy title/artist search is issued against the Deezer catalog.
2. **Given** fuzzy search returns a candidate above the confidence threshold and `--autopilot` is active, **When** matching runs, **Then** the candidate is accepted automatically and `TXXX:DEEZER` is updated if `--embed-matches` is set.
3. **Given** fuzzy search returns a candidate below the confidence threshold, **When** matching runs without `--autopilot`, **Then** the user is prompted to accept, reject, or skip the candidate.
4. **Given** fuzzy search returns no candidates at all, **When** matching completes, **Then** the track is left unmatched, a warning is logged, and no `TXXX:DEEZER` tag is written.
5. **Given** the track has a non-Latin (Cyrillic or CJK) artist or title, **When** fuzzy search runs, **Then** the query is sent to Deezer as-is without transliteration; if no result is returned, a warning is logged.

---

### Edge Cases

- What happens when a transient network error (timeout, 5xx response) occurs while resolving a single track? The error is logged as a warning, the track is left unmatched, and processing continues with the remaining tracks.
- What happens when `deezer import` is run for a playlist name that already exists on Deezer? A new playlist is always created; Deezer allows duplicate names and the existing playlist is never modified by `import`.
- What happens when the ARL cookie is expired or invalid? The tool must report a clear authentication error (without echoing the ARL value) and exit without making playlist changes.
- What happens when a Deezer playlist ID does not exist or is inaccessible with the given ARL? A descriptive error is shown and no local tags are modified.
- What happens when a local audio file cannot be opened for tag writing (e.g., read-only)? The match result is logged as a warning and processing continues for remaining tracks.
- What happens when the local `.m3u` file references a path that does not exist? The track is skipped with a warning; other tracks continue to be processed.
- What happens when both ISRC lookup and fuzzy search return no results for a track? The track is left unmatched; if `--autopilot` is not set, the user is prompted whether to skip.
- What happens when non-Latin artist or track names (Cyrillic, CJK) are used in fuzzy search? The search query is sent as-is; if no results are returned, the track is treated as unmatched with a logged warning.
- What happens when `--embed-matches` is used on a file format that does not support `TXXX` tags (e.g., FLAC, AAC)? The tool falls back to an equivalent custom tag if supported by the format, or logs a warning and skips tag writing for that file.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a `deezer` CLI command group with five sub-commands: `import`, `sync`, `match`, `compare`, and `duplicates`.
- **FR-002**: The system MUST authenticate to Deezer using the ARL cookie stored in the `[deezer]` section of `~/.playlist_sync/config.ini`; no OAuth flow is required.
- **FR-003**: The `deezer import` command MUST accept one or more `.m3u` file paths and create a corresponding Deezer playlist for each, populated with matched tracks.
- **FR-004**: The `deezer sync` command MUST accept a local `.m3u` file path and a Deezer playlist identifier, then add tracks missing from Deezer and remove tracks absent from the local file.
- **FR-005**: The `deezer match` command MUST always write resolved Deezer track identifiers to local audio files as `TXXX:DEEZER` ID3 tags (embedding is unconditional for this command); it MUST NOT create or modify any Deezer playlist.
- **FR-006**: The `deezer compare` command MUST print a human-readable diff between a local `.m3u` playlist and a Deezer playlist, using `TXXX:DEEZER` to identify tracks.
- **FR-007**: The `deezer duplicates` command MUST report all tracks in a local `.m3u` file that share the same `TXXX:DEEZER` value.
- **FR-008**: Track matching MUST follow this resolution order: (1) if the local track has a `TXXX:DEEZER` tag containing a well-formed Deezer track URL (with or without `www.`, an optional locale segment, and/or an optional query string, e.g., `https://www.deezer.com/en/track/12345?utm_source=sharing`), extract the numeric track ID, normalise to the canonical form `https://www.deezer.com/track/<id>`, and use it directly, skipping all lookups; (2) if the tag value is `"SKIP"`, exclude the track; (3) if the tag is absent or malformed, attempt ISRC-based lookup if an ISRC is available in local metadata; (4) if ISRC lookup yields no result, fall back to fuzzy title/artist search.
- **FR-009**: A `TXXX:DEEZER` tag value of `"SKIP"` MUST cause the track to be excluded from Deezer playlist operations without error or prompt.
- **FR-010**: The `--autopilot` flag MUST auto-accept matches that meet or exceed a configurable confidence threshold, bypassing interactive prompts.
- **FR-011**: The `--embed-matches` flag, supported by `deezer import` and `deezer sync`, MUST write the resolved Deezer track identifier back to the local audio file's `TXXX:DEEZER` tag when a match is found. When the flag is absent on these commands, no local tags are written.
- **FR-012**: The `import` and `sync` commands MUST support `--from-path`/`--to-path` flags for path prefix remapping of local file references.
- **FR-013**: The `import` command MUST support a `--public` flag; playlists created without it MUST default to private.
- **FR-014**: The `sync` command MUST support a `--sort-tracks` flag that reorders the Deezer playlist to match the local `.m3u` track order after syncing.
- **FR-015**: Non-Latin track and artist names (Cyrillic, CJK, etc.) MUST be forwarded to Deezer search without silent truncation or transliteration; unresolved non-Latin tracks MUST be logged as warnings rather than silently skipped.
- **FR-016**: The system MUST report a clear, actionable error message when ARL authentication fails and MUST NOT modify any Deezer playlist or local tags in that case.
- **FR-017**: When a transient network error occurs while resolving an individual track or performing a single playlist mutation, the system MUST log a warning and continue processing the remaining tracks; it MUST NOT abort the entire command.
- **FR-018**: The ARL cookie value MUST NOT appear in any log output, error message, or terminal output under any circumstances; error messages relating to authentication MUST describe the failure without echoing the credential.
- **FR-019**: The `deezer import` command MUST always create a new Deezer playlist regardless of whether a playlist with the same name already exists; it MUST NOT modify or overwrite any existing Deezer playlist.

### Key Entities

- **DeezerTrack**: Represents a Deezer catalog track; key attributes include Deezer track ID, title, artist name, album name, ISRC, and the Deezer URL used as the persistent reference.
- **DeezerPlaylist**: Represents a Deezer playlist; key attributes include playlist ID, name, visibility (public/private), and an ordered list of `DeezerTrack` references.
- **DeezerMatcher**: Encapsulates the four-step track resolution strategy — existing `TXXX:DEEZER` tag → `SKIP` check → ISRC lookup → fuzzy search fallback — and returns a match result with a confidence score.
- **DeezerRef** (`TXXX:DEEZER` tag): A string stored in local audio file metadata. Valid values are a Deezer track URL matching `https://[www.]deezer.com[/<locale>]/track/<numeric-id>[?<query>]` (`www.`, locale, and query string all optional), the literal value `"SKIP"` (intentionally excluded), or absent (unmatched). All valid variants are normalised to the canonical form (`https://www.deezer.com/track/<id>`) — locale and query string stripped — when read or written. Any other value is treated as invalid and triggers re-resolution.
- **DeezerAPI**: A singleton client that wraps the `deezer-py` `GW` class, authenticated via ARL cookie, providing playlist CRUD and track search operations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can import a 100-track `.m3u` playlist to Deezer end-to-end in under 5 minutes on a typical broadband connection.
- **SC-002**: For tracks that have an ISRC tag present in both local metadata and the Deezer catalog, the match accuracy rate is 100% (exact match, no false positives).
- **SC-003**: For tracks matched via fuzzy search, the auto-accepted match accuracy rate is at or above the same threshold as the existing Spotify fuzzy matcher.
- **SC-004**: All five `deezer` CLI commands are reachable and produce help text via `--help` without requiring a valid ARL.
- **SC-005**: Running `deezer sync` on a playlist that is already up to date completes without modifying the Deezer playlist and exits with a success status.
- **SC-006**: A `TXXX:DEEZER` tag written by `deezer match`, `deezer import --embed-matches`, or `deezer sync --embed-matches` is correctly read back on any subsequent matching operation, causing the matcher to use the cached reference directly and avoiding any redundant network lookup.
- **SC-007**: Non-Latin (Cyrillic, CJK) track names do not cause the tool to crash or exit silently; they result in either a matched track or a logged warning.

## Assumptions

- The `deezer-py` v1.3.7 library's `GW` class is sufficient for all required Deezer operations (playlist create, playlist update, track search by ISRC, fuzzy search) and no alternative library is needed.
- The Deezer internal API (`gw-light.php`) exposed through `deezer-py` remains functional at the time of implementation; no stability guarantee is assumed.
- ARL cookies must be obtained manually by the user and are not generated or renewed by this tool.
- The ARL cookie does not expire during a single tool invocation; sessions lasting longer than one ARL lifetime are out of scope.
- Deezer playlist visibility options are limited to public and private; collaborative or secret playlist types are out of scope.
- Path remapping (`--from-path`/`--to-path`) follows the same one-directional semantics as the existing `PathMapper` used in the Spotify flow.
- The `TXXX:DEEZER` tag is independent of `TXXX:SPOTIFY_REF`; a track may have both, either, or neither without conflict. **Write**: always store the canonical form `https://www.deezer.com/track/<id>` (with `www.`, no locale, no query string). **Read**: accept any valid Deezer track URL variant (`www.` optional, locale optional, query string optional), extract the numeric ID, and normalise to canonical before use.
- Mobile-app-specific Deezer features (offline sync, HiFi quality selection) are out of scope.
- The initial implementation targets audio formats that already support `TXXX` tags (MP3); extended format support (FLAC, AAC, ALAC) is treated as a best-effort enhancement.
- The `deezer` CLI group is added to the existing `main.py` entry point alongside the `spotify` group, with no separate binary produced.
