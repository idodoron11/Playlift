# Research: Decouple Matcher from Concrete Track Implementation

All questions from the Technical Context are resolved from codebase analysis. No external research required.

---

## Decision 1 — Where to locate `ServiceTrack` and `EmbeddableTrack`

**Decision**: Both new ABCs go in `tracks/__init__.py` alongside `Track`.

**Rationale**: `Track` is already the single import surface for the tracks layer. Co-locating the two new ABCs means callers do `from tracks import Track, ServiceTrack, EmbeddableTrack` — consistent with existing import patterns. Splitting them into separate files would add import paths without adding clarity.

**Alternatives considered**:
- Separate files (`tracks/service_track.py`, `tracks/embeddable_track.py`) — rejected: over-engineering for two 5-line ABCs that are tightly coupled to `Track`.

---

## Decision 2 — `service_name` as abstract property vs. class variable on `ServiceTrack`

**Decision**: `service_name` is declared as an `@property @abstractmethod` on `ServiceTrack` (not a class variable). Same pattern applied to `Matcher.service_name`.

**Rationale**: Python ABCs enforce abstract property overrides at instantiation time. A plain class variable annotation (`service_name: str`) is not enforced — a subclass can omit it and `mypy` in strict mode will emit no error for the base class. An `@abstractmethod` property provides both runtime and static enforcement.

**Alternatives considered**:
- `ClassVar[str]` annotation — rejected: not enforced by `ABCMeta`; subclasses could forget to define it with no error.
- `__init_subclass__` check — rejected: adds runtime complexity with no benefit over ABC enforcement.

---

## Decision 3 — `embed_match(match: ServiceTrack)` parameter type

**Decision**: The parameter type is `ServiceTrack`, not `Track`.

**Rationale**: `embed_match` needs `match.service_name` and `match.permalink` — both of which only exist on `ServiceTrack`. Accepting `Track` would require a runtime `isinstance` check inside `embed_match`, reintroducing the very coupling this refactor removes. The tighter type also prevents callers from accidentally passing a `LocalTrack` or `TrackMock` as the match.

**Alternatives considered**:
- Accept `Track` and guard with `isinstance(match, ServiceTrack)` — rejected: propagates the type-check smell into the new method.

---

## Decision 4 — `_normalize_isrc` visibility after the refactor

**Decision**: `_normalize_isrc` remains a private module-level function in `tracks/local_track.py`. It is not promoted to `tracks/__init__.py` or made public.

**Rationale**: After this refactor `_normalize_isrc` is only called within `local_track.py` — inside the `isrc` getter, the `isrc` setter, and the new `embed_match`. No other module needs it. Making it public would widen the API surface without justification.

**Alternatives considered**:
- Move to `tracks/__init__.py` as public `normalize_isrc` — rejected: nothing outside `local_track.py` calls it after the refactor.

---

## Decision 5 — `Matcher.service_name` as abstract property

**Decision**: Add `@property @abstractmethod service_name(self) -> str` to the `Matcher` ABC. `SpotifyMatcher` overrides it with `return "SPOTIFY"`.

**Rationale**: The matcher needs to call `source_track.service_ref(self.service_name)` to check for already-matched tracks without hardcoding `"SPOTIFY"` as a string literal in `_find_spotify_match_in_source_track`. Making it abstract on the ABC enforces that every future matcher (Deezer, Apple Music) declares its own service identifier — self-documenting and compiler-checked.

**Alternatives considered**:
- Private class constant `_SERVICE_NAME: str = "SPOTIFY"` — rejected: not enforced by the ABC, so future matchers could forget to define it without a helpful error.

---

## Decision 6 — `isinstance(track, LocalTrack)` in `main.py` (cli_spotify_duplicates)

**Decision**: Leave `main.py:99` unchanged — this `isinstance(track, LocalTrack)` check is acceptable.

**Rationale**: Constitution §II-D states: "Dependencies MUST be injected, never instantiated inside business logic." The CLI layer (`main.py`) is an entry point boundary, not business logic. The `cli_spotify_duplicates` command explicitly works with `LocalTrack.spotify_ref` as a domain concept (grouping local files by their Spotify ref) — knowing the concrete type is appropriate here. Introducing `EmbeddableTrack` into the CLI check would misuse the interface.

**Alternatives considered**:
- Replace with `isinstance(track, EmbeddableTrack)` in `main.py` — rejected: `EmbeddableTrack` does not expose `spotify_ref`; it exposes `service_ref(name)`. Changing the CLI to use `service_ref("SPOTIFY")` is a scope creep that can be a separate refactor.

---

## Decision 7 — `SpotifyTrack.track_url` vs. `permalink`

**Decision**: `SpotifyTrack.permalink` returns `self.track_url`. `track_url` is kept as-is (not deprecated).

**Rationale**: `track_url` is used externally by `cleanup.py` and in existing tests via `match.track_url`. Renaming it would require updating callers throughout the codebase — out of scope. `permalink` is the abstraction-layer property; `track_url` remains the concrete Spotify-specific convenience accessor.

**Alternatives considered**:
- Remove `track_url` and replace with `permalink` everywhere — rejected: out of scope; breaking change to existing callers.
