# Feature Specification: Fix Three M4A ISRC Tag Bugs

**Feature Branch**: `002-fix-isrc-mp4-bugs`  
**Created**: 2026-04-06  
**Status**: Draft  
**Input**: User description: "Fix three M4A ISRC bugs: case-sensitive freeform key lookup, wrong MP4FreeForm type, and un-normalized ISRC comparison"

## Clarifications

### Session 2026-04-06

- Q: Should the case-insensitive freeform key lookup fix live in `_get_custom_tag` (affecting all freeform tags) or only in the `isrc` getter? → A: Fix inside `_get_custom_tag` — case-insensitive fallback applies to all freeform tags.
- Q: What test approach for the regression test — mock-only or real temp file? → A: Mock-only, extending existing `TestLocalTrackIsrcGetterM4a` with a lowercase-keyed tags dict.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - M4A file with existing lowercase ISRC is not duplicated (Priority: P1)

A user runs `spotify match` against a directory containing an M4A file that already has an ISRC stored under a lowercase freeform atom key (e.g. written by Apple Music or third-party encoders). After the command completes, the file must still have exactly one ISRC atom — not two.

**Why this priority**: This is the root-cause bug confirmed by live reproduction. Files with a pre-existing lowercase ISRC silently receive a second, uppercase duplicate atom every time `spotify match` is run, corrupting the file's metadata.

**Independent Test**: Point `spotify match` at a single M4A file whose ISRC atom key is `----:com.apple.iTunes:isrc` (lowercase) and verify the file still contains exactly one ISRC atom afterwards.

**Acceptance Scenarios**:

1. **Given** an M4A file with one ISRC tag stored as `----:com.apple.iTunes:isrc` (lowercase), **When** `spotify match` is run against it, **Then** the file still contains exactly one ISRC atom with the original value.
2. **Given** an M4A file with one ISRC tag stored as `----:com.apple.iTunes:ISRC` (uppercase), **When** `spotify match` is run against it, **Then** the file still contains exactly one ISRC atom.
3. **Given** an M4A file with no ISRC tag, **When** `spotify match` is run and a match with an ISRC is found, **Then** the file gains exactly one ISRC atom stored as `----:com.apple.iTunes:ISRC`.

---

### User Story 2 - ISRC comparison normalizes before comparing (Priority: P2)

A user's local file (M4A, MP3, or FLAC) has an ISRC. When `spotify match` embeds a result, the system normalizes both the local and Spotify ISRCs before comparing. If they are semantically the same value (ignoring hyphens and casing), the tag is not rewritten. If they are genuinely different, the local ISRC is updated with the normalized Spotify value.

**Why this priority**: Without normalization before comparison, the setter fires and overwrites the local ISRC with the un-normalized Spotify value on every format — not just M4A. Conversely, a track whose local ISRC is stale or wrong should be corrected by a fresh Spotify match.

**Independent Test**: Confirm that a local track whose ISRC matches the Spotify track's ISRC modulo hyphens and casing does not have its tag rewritten. Confirm that a track with a genuinely different local ISRC is updated to the Spotify value.

**Acceptance Scenarios**:

1. **Given** an M4A/MP3/FLAC file with ISRC `"USSM19604431"` and a Spotify match returning `"USSM1-9604431"`, **When** match embedding runs, **Then** the file's ISRC tag is not modified (values are semantically identical).
2. **Given** an M4A/MP3/FLAC file with ISRC `"ussm19604431"` (lowercase) and a Spotify match returning `"USSM19604431"`, **When** match embedding runs, **Then** the file's ISRC tag is not modified.
3. **Given** an M4A/MP3/FLAC file with ISRC `"GBAYE0100538"` and a Spotify match returning `"USRC17607839"` (genuinely different), **When** match embedding runs, **Then** the file's ISRC tag is updated to `"USRC17607839"`.

---

### User Story 3 - MP4 freeform tags are written as valid iTunes freeform values (Priority: P3)

When a new custom tag (ISRC, SPOTIFY ref, or any other freeform tag) is written to an M4A file, the stored value must be a proper iTunes freeform atom, readable by standard tag editors and playback software.

**Why this priority**: Writing raw bytes instead of a proper `MP4FreeForm` object is a latent correctness bug. It works today only due to silent fallback behaviour in the library and may break on future library upgrades or with certain readers.

**Independent Test**: Write any custom tag to an M4A file and confirm the value is stored as an `MP4FreeForm` atom with `AtomDataType.UTF8` when read back via mutagen.

**Acceptance Scenarios**:

1. **Given** an M4A file, **When** a custom ISRC tag is written, **Then** reading the tag back with mutagen yields an `MP4FreeForm` object, not a raw `bytes` object.
2. **Given** an M4A file, **When** the Spotify reference tag is written, **Then** reading the tag back yields an `MP4FreeForm` object with UTF-8 encoding.

---

### Edge Cases

- What happens when an M4A file has two existing ISRC atoms (already corrupt)? The getter reads `tag[0]` (first entry), so it returns a value and the setter guard blocks any further write — no third atom is added.
- What happens when the ISRC freeform atom key uses mixed case (e.g. `----:com.apple.iTunes:Isrc`)? The case-insensitive lookup must find it.
- What happens when `match.isrc` from Spotify is `None`? The setter is never called — the existing guard in `_update_spotify_match_in_source_track` (`if match.isrc is not None`) handles this.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `_get_custom_tag` helper MUST resolve a freeform iTunes atom using a case-insensitive match on the key suffix when an exact-case match is not found — this applies to all freeform tags (ISRC, SPOTIFY ref, and any future custom tag).
- **FR-002**: The system MUST NOT write a new ISRC atom to an M4A file when a valid ISRC already exists under any casing of the freeform key.
- **FR-003**: When writing a new freeform atom to an M4A file, the value MUST be stored as a proper MP4 freeform value with UTF-8 data type, compatible with the iTunes metadata specification.
- **FR-004**: Before writing an ISRC from a Spotify match result, the system MUST normalize the Spotify ISRC (uppercase, hyphens stripped) and compare it with the local ISRC value. If the normalized values are equal, no write is performed. If they differ, the local ISRC is updated with the normalized Spotify value. This applies on **all formats** (M4A, MP3, FLAC).
- **FR-005**: MP3 and FLAC ISRC read paths MUST remain unchanged. Only the comparison in `_update_spotify_match_in_source_track` is modified for these formats.
- **FR-006**: All existing behaviour for reading and writing the Spotify reference freeform tag (`----:com.apple.iTunes:SPOTIFY`) MUST remain unchanged.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An M4A file with a pre-existing lowercase-keyed ISRC atom has exactly one ISRC atom after `spotify match` is run — zero duplicates introduced.
- **SC-002**: An M4A file with a pre-existing uppercase-keyed ISRC atom has exactly one ISRC atom after `spotify match` is run.
- **SC-003**: An M4A file written by the tool contains freeform atoms that are readable as UTF-8 text by any conformant MP4/iTunes metadata reader.
- **SC-004**: All existing unit tests continue to pass without modification.
- **SC-005**: New unit tests covering the case-insensitive lookup, the MP4FreeForm write type, and the normalized comparison all pass.
- **SC-006**: Regression tests use mock mutagen objects (no real files on disk), consistent with the existing test style in `tests/tracks/test_local_track.py`.

## Assumptions

- **Bug 1 is M4A/MP4-only** because:
  - MP3 files: `isrc` getter reads the ID3 `TSRC` frame directly (`self._mutagen_file.tags["TSRC"]`). `_get_custom_tag` is never called for ISRC on MP3. ID3 frame names are fixed uppercase by spec — casing cannot vary.
  - FLAC files: `isrc` getter calls `self._get_tag("isrc")` via `music_tag`, which uses the Vorbis comment spec. Vorbis comment key lookup is case-insensitive by standard and handled internally by `music_tag` — `_get_custom_tag` is never called.
  - M4A files: `isrc` getter falls into the `else:` branch and calls `_get_custom_tag("ISRC")`, which performs a case-sensitive exact lookup. This is where the casing mismatch occurs.
- **Bug 2 is M4A/MP4-only**: the raw bytes write is in the MP4 branch of `_set_custom_tag`. MP3 uses `tags.add(TXXX(...))` and FLAC uses a plain string assignment — both are correct.
- **Bug 3 affects all formats** (M4A, MP3, FLAC): since the setter no longer has an early-exit guard, an un-normalized Spotify ISRC (`"USSM1-9604431"`) that differs only by formatting from the local ISRC (`"USSM19604431"`) will overwrite the local tag on every format. The fix — normalizing `match.isrc` before comparison — prevents this for all formats.
- The case-insensitive key lookup applies only to the freeform iTunes namespace prefix (`----:com.apple.iTunes:`); other MP4 atom keys are not affected.
- Existing files with two ISRC atoms (already corrupted by this bug) are not automatically repaired — a separate cleanup command is out of scope for this fix.
- The normalization logic (`_normalize_isrc`: uppercase + strip hyphens) is already correct and is reused; no changes to normalization behaviour are needed.
