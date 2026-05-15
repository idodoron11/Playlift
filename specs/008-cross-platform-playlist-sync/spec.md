# Feature Specification: Cross-Platform Playlist Sync

**Feature Branch**: `008-cross-platform-playlist-sync`  
**Created**: 2026-05-15  
**Status**: Draft  
**Input**: User description: "Cross-platform playlist sync: sync any TrackCollection (local, Spotify, Deezer) into any SyncTarget (Spotify, Deezer) via a new PlaylistFactory class for source detection and construction"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Import a Service Playlist into Another Platform (Priority: P1)

A user has a playlist on one streaming platform (e.g. Spotify) and wants to recreate it on another (e.g. Deezer). They pass the source playlist URL or URI as the `--source` argument to an `import` command targeting the destination platform. The tool auto-detects the source platform from the URL format, fetches the tracks, matches them against the destination platform's catalog, and creates a new playlist.

**Why this priority**: This is the core value of the feature — enabling one-shot cross-platform playlist migration that was previously impossible with the tool.

**Independent Test**: Run `import` on a service playlist URL targeting the other platform; verify a new playlist is created on the destination containing matched tracks.

**Acceptance Scenarios**:

1. **Given** a valid Spotify playlist URI/URL, **When** the user runs `deezer import --source <spotify-url> --destination "My Playlist"`, **Then** a new Deezer playlist is created containing all matched tracks from the Spotify playlist.
2. **Given** a valid Deezer playlist URL, **When** the user runs `spotify import --source <deezer-url> --destination "My Playlist"`, **Then** a new Spotify playlist is created containing all matched tracks from the Deezer playlist.
3. **Given** a Spotify playlist URL and `--embed-matches` flag, **When** the user runs the import, **Then** the import completes successfully and the flag is silently ignored (no error, no embedding — source tracks are remote and cannot carry embedded metadata).

---

### User Story 2 - Sync an Existing Service Playlist from Another Platform (Priority: P2)

A user has an existing playlist on a destination platform and wants to keep it in sync with a source playlist on a different platform. They run a `sync` command specifying the source service playlist URL and the destination platform playlist ID. The tool clears the destination playlist and repopulates it with freshly matched tracks.

**Why this priority**: Recurring sync across platforms is a natural follow-on to one-time import and covers ongoing use cases (e.g. maintaining a Deezer mirror of a Spotify playlist).

**Independent Test**: Run `sync` targeting an existing destination playlist with a service playlist URL as source; verify the destination playlist's tracks are replaced with matched tracks from the source.

**Acceptance Scenarios**:

1. **Given** an existing Deezer playlist and a Spotify playlist URI, **When** the user runs `deezer sync --source <spotify-uri> --destination <deezer-id>`, **Then** the Deezer playlist is updated to reflect the current contents of the Spotify playlist.
2. **Given** an existing Spotify playlist and a Deezer playlist URL, **When** the user runs `spotify sync --source <deezer-url> --destination <spotify-id>`, **Then** the Spotify playlist is updated to reflect the current contents of the Deezer playlist.

---

### User Story 3 - Existing Local-to-Service Workflows Are Unchanged (Priority: P1)

A user who currently uses the tool to sync local `.m3u` files to Spotify or Deezer continues to do so exactly as before. No existing commands or flags are changed or broken.

**Why this priority**: Regression prevention is as critical as new capability. Any breakage of local workflows would make the feature unshippable.

**Independent Test**: Run existing `spotify import --source <m3u-file>` and `deezer sync --source <m3u-file>` commands; verify identical behavior to before this feature.

**Acceptance Scenarios**:

1. **Given** a local `.m3u` file as source, **When** the user runs any existing `import` or `sync` command, **Then** it behaves identically to before this feature was introduced.
2. **Given** a local `.m3u` file with `--from-path`/`--to-path` flags, **When** the user runs any existing command, **Then** path remapping continues to work correctly.

---

### Edge Cases

- **Source platform equals destination platform**: A user passes a Spotify playlist URL as the source of a `spotify import` command. This is a valid operation — the tool should treat it as any other source and copy the playlist.
- **`--embed-matches` with a service playlist source**: The flag is silently ignored. No error is raised, no warning is printed. The import or sync proceeds normally.
- **`--from-path`/`--to-path` combined with a service playlist source**: The tool immediately reports an error. Path remapping is only meaningful for local file sources and has no defined behavior for remote playlists.
- **Unrecognised source string**: A source string that is not a local file path, a local directory path, a Spotify URI/URL, or a Deezer URL produces a clear error before any network calls are made.
- **Source platform authentication failure**: If the source platform's credentials are missing or invalid, the tool reports an authentication error before attempting any matching.
- **Tracks on source platform not available on destination catalog**: Unmatched tracks are skipped (existing matcher behavior). The playlist is created/updated with only successfully matched tracks.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `import` and `sync` commands for both platforms MUST accept a streaming service playlist URL or URI as the `--source` argument, in addition to existing local file/directory paths.
- **FR-002**: The tool MUST auto-detect the source platform (Spotify, Deezer, or local) from the format of the `--source` argument, without requiring an explicit platform flag.
- **FR-003**: A Spotify playlist MUST be identifiable by either the `spotify:playlist:<id>` URI format or the `https://open.spotify.com/playlist/<id>` URL format.
- **FR-004**: A Deezer playlist MUST be identifiable by a `deezer.com/*/playlist/<id>` URL format. A raw numeric string MAY also be accepted as a Deezer playlist ID.
- **FR-005**: When `--from-path` or `--to-path` is provided alongside a service playlist source, the tool MUST reject the command with a clear error before any network calls are made.
- **FR-006**: When `--embed-matches` is provided alongside a service playlist source, the tool MUST silently ignore the flag and proceed normally — no error, no warning.
- **FR-007**: All six supported source-to-destination combinations MUST work: local→Spotify, local→Deezer, Spotify→Spotify, Spotify→Deezer, Deezer→Spotify, Deezer→Deezer.
- **FR-008**: Syncing to a local playlist from any service (e.g. Spotify→local) is NOT supported and is out of scope.
- **FR-009**: The `compare` and `match` commands are NOT required to support service playlist sources and remain local-only.
- **FR-010**: All existing local-to-service workflows MUST continue to work without any change to user-facing behavior.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can complete a cross-platform playlist import (service→service) in no more steps than a local-to-service import — only the `--source` value changes.
- **SC-002**: 100% of the six supported source/destination combinations complete without error when both platform accounts are authenticated and tracks exist in both catalogs.
- **SC-003**: All existing passing tests continue to pass after the feature is introduced (zero regressions).
- **SC-004**: Providing `--from-path`/`--to-path` with a service source produces a user-readable error message in 100% of invocations, with no partial side effects (no playlist created, no API calls made).
- **SC-005**: Source platform detection requires no user-supplied flags beyond the existing `--source` argument.

## Assumptions

- Both source and destination platform accounts are authenticated before the command runs; credential setup is out of scope for this feature.
- The track-matching quality for service→service flows is the same as for local→service flows, since the same matcher logic is reused. No special cross-platform match tuning is in scope.
- Tracks present on the source platform but absent from the destination platform's catalog are silently skipped — this is the existing matcher behavior and is not changed by this feature.
- The `--autopilot` flag behaves identically for service sources as it does for local sources.
- Same-platform sync (e.g. Spotify→Spotify) is valid but offers limited practical value; it is supported as a natural consequence of the general design, not as a primary use case.
