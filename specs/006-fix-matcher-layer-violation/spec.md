# Feature Specification: Decouple Matcher from Concrete Track Implementation

**Feature Branch**: `006-fix-matcher-layer-violation`  
**Created**: 2026-04-22  
**Status**: Draft  
**Input**: Fix DIP and SRC violation in SpotifyMatcher: introduce ServiceTrack and EmbeddableTrack abstractions

## Clarifications

### Session 2026-04-22

- Q: Where should the service identifier key live so the matcher can call `service_ref(key)` without hardcoding strings in method bodies? → A: The `Matcher` ABC declares an abstract `service_name` property; each concrete matcher overrides it (e.g. `SpotifyMatcher.service_name = "SPOTIFY"`).
- Q: When the local track already has a different ISRC from the matched streaming track, should the stored ISRC be overwritten? → A: Always overwrite when different — the matched track's ISRC is considered authoritative.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Matcher delegates match persistence without knowing the source track type (Priority: P1)

A developer runs a sync operation. The matcher finds a streaming service match for a source track. When `embed_matches` is enabled, the match's service reference and ISRC are written back into the source track's audio file — without the matcher ever needing to know the concrete type of the source track or the concrete type of the matched track.

**Why this priority**: This is the core DIP fix. Without it the matcher is tightly coupled to a concrete track class, preventing future extension.

**Independent Test**: Given a source track that supports ref storage and a matched streaming service track, calling the matcher's embed step results in the source track recording the service reference and ISRC — verifiable by reading the audio file tags.

**Acceptance Scenarios**:

1. **Given** a source track that supports ref storage and has no existing service ref, **When** a streaming service match is embedded, **Then** the source track persists the service URL under a key named after that service, and the ISRC is also written if the matched track carries one.
2. **Given** a source track that does not support ref storage (e.g. a read-only or remote track), **When** a streaming service match is embedded, **Then** the embed step is silently skipped with no error.
3. **Given** a source track that already has the exact same service ref and ISRC as the matched track, **When** embed is called, **Then** no write operations occur.

---

### User Story 2 — A new streaming service can be added without changing any existing class (Priority: P2)

A developer adds support for a new streaming service (e.g. Deezer). The new service's track type declares its own service identifier and canonical URL. Local audio files can now store Deezer references alongside existing Spotify references, and a Deezer matcher can embed matches using the same embedding mechanism — without modifying the matcher base, the local track class, or any other existing class.

**Why this priority**: Validates that the abstraction is truly open for extension; directly exercises the multi-service coexistence requirement.

**Independent Test**: A local audio file that already has a Spotify reference can receive a Deezer match embed. Afterwards, both the Spotify and Deezer references are present in the file simultaneously, and reading each one independently returns the correct value.

**Acceptance Scenarios**:

1. **Given** a local audio file with an existing Spotify service reference, **When** a Deezer match is embedded, **Then** the Deezer reference is written under the Deezer service key and the Spotify reference is unchanged.
2. **Given** a new streaming service track type that declares its own service identifier and permalink, **When** an embed operation is performed, **Then** the service reference is stored under the new service's identifier without any modification to existing classes.

---

### User Story 3 — Streaming service tracks expose a canonical URL and service identifier (Priority: P3)

Streaming service tracks (e.g. Spotify, Deezer) expose two queryable properties: a canonical URL that identifies the track on that service, and a service identifier string used as the storage key. Local tracks do not implement these properties because the concepts are not applicable to them.

**Why this priority**: Foundational contract that makes Story 2 possible; can be verified in isolation before the full embed pipeline is wired.

**Independent Test**: A streaming service track object can be queried for its canonical URL and service identifier and returns correct non-null values. A local track object does not implement this contract.

**Acceptance Scenarios**:

1. **Given** a streaming service track, **When** its canonical URL is read, **Then** a non-null URL identifying that track on its service is returned.
2. **Given** a streaming service track, **When** its service identifier is read, **Then** a non-null string key (e.g. `"SPOTIFY"`) is returned.
3. **Given** a local audio track, **When** checked whether it conforms to the streaming service track contract, **Then** it does not — local tracks are not streaming service tracks.

---

### Edge Cases

- What happens when the matched streaming track has no ISRC? → Only the service reference is written; the ISRC tag is left unchanged.
- What happens when the source track already has a different ISRC from the matched track? → The matched track's ISRC always overwrites the stored one — it is considered authoritative. ISRC is a universal, service-agnostic identifier so a single value applies regardless of which service provided it.
- What happens when the canonical URL for a match is identical to what is already stored? → No write occurs; the embed operation is idempotent.
- What happens when two different streaming service tracks return different ISRCs for the same song? → The ISRC from the most recently embedded match wins; no conflict resolution is applied.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a streaming service track contract that exposes a canonical URL and a service identifier; only streaming service track types implement this contract.
- **FR-002**: The system MUST provide an embeddable track contract, orthogonal to the streaming service contract, that defines how a track stores external match data; only local audio tracks implement this contract.
- **FR-003**: The matcher MUST request match persistence through the embeddable track contract only — it MUST NOT reference any concrete track type or any private symbol from the tracks layer.
- **FR-004**: When embedding a match, the embeddable track MUST write the service reference under a key derived from the matched track's service identifier.
- **FR-005**: When embedding a match, the embeddable track MUST write the ISRC from the matched track if the matched track carries an ISRC that differs from the value already stored; the matched track's ISRC is always considered authoritative and MUST overwrite any previously stored value.
- **FR-006**: Multiple service references for different streaming services MUST coexist independently in the same audio file; embedding one service's match MUST NOT affect any other service's stored reference.
- **FR-007**: If a source track does not implement the embeddable track contract, the matcher MUST skip the embed step silently.
- **FR-008**: Reading a stored service reference by service identifier MUST be supported on any embeddable track; an absent reference MUST return a null/absent value rather than an error.
- **FR-009**: The matcher MUST use the stored service reference (read via the embeddable contract) to detect already-matched tracks, replacing the current concrete type check.
- **FR-010**: The `Matcher` ABC MUST declare an abstract `service_name` property returning the service identifier string; each concrete matcher MUST provide its own value (e.g. `SpotifyMatcher` returns `"SPOTIFY"`).

### Key Entities

- **Track**: The base contract for any playable track — local or remote. Carries metadata (title, artists, album, duration, ISRC, track number). Neither permalink nor service identity belong here.
- **Streaming Service Track**: A specialisation of Track for tracks sourced from a streaming service. Adds a canonical URL and a service identifier. Implemented by each streaming service's track type.
- **Embeddable Track**: An orthogonal contract for tracks that can persist external match data (service references and ISRC) into durable storage. Implemented only by local audio tracks.
- **Service Reference**: A stored association between a local audio file and a specific streaming service track, identified by service name and value (the canonical URL).
- **Matcher service_name**: An abstract property on the `Matcher` ABC that each concrete matcher overrides to declare its own service identifier. Used by the matcher to read the correct stored service reference when checking for already-matched tracks.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero references to any concrete track implementation exist in the matcher layer after the change — verified by static search.
- **SC-002**: Zero references to private symbols from the track layer exist in the matcher layer after the change — verified by static search.
- **SC-003**: All existing tests pass without modification to their assertions (only test setup may change where tests previously constructed concrete mocks).
- **SC-004**: A new streaming service track type can be made embeddable by implementing two contracts only, with zero changes to the matcher or local track classes — demonstrated by the design permitting this without modification.
- **SC-005**: All modified and new code passes static type checking with no new type errors.
- **SC-006**: All modified and new code passes the project linter with no new warnings.

## Assumptions

- Embedding match data is only meaningful for local audio files; streaming service tracks never need to store references back into themselves.
- The service identifier used as the storage key is a stable, uppercased string (e.g. `"SPOTIFY"`, `"DEEZER"`); it is defined by the streaming service track type, not the matcher.
- ISRC is a universal, service-agnostic identifier; a single ISRC tag per audio file is sufficient regardless of how many service references are stored.
- The existing `spotify_ref` property on local tracks is preserved as a convenience accessor for callers that already use it directly (e.g. `cleanup.py`); it reads the same underlying tag as reading the service reference for Spotify.
- Behavior of the embed pipeline (when to embed, autopilot mode, ISRC prefetch batching) is out of scope and unchanged by this refactor.
