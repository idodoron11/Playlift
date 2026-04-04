---
description: "Clean code, SOLID, and maintainability guidelines for GitHub Copilot"
applyTo: "**/*.py"
---

# Clean Code Instructions

Guidelines for writing clean, maintainable, testable, and scalable Python code.
These complement the Python style instructions — apply both together.

---

## Naming

Names are the most-read part of code. Optimize for the reader, not the writer.

- **Be precise**: `user_email` over `data`; `retry_count` over `n`; `is_authenticated` over `flag`
- **Reveal intent**: the name should answer *why it exists* and *what it does*
- **Avoid noise words**: `user_info`, `track_data`, `manager`, `helper`, `utils` are red flags — be specific
- **Boolean names**: use `is_`, `has_`, `can_`, `should_` prefixes (`is_empty`, `has_metadata`, `can_retry`)
- **Collections**: use plural nouns (`tracks`, `playlist_ids`); use singular for single items
- **Functions & methods**: start with a verb that describes the action (`fetch_`, `build_`, `calculate_`, `find_`, `validate_`)
- **Constants**: `UPPER_SNAKE_CASE`; define them at module level, never as magic literals inline

```python
# ❌ Bad
def process(d, f=False):
    data2 = []
    for x in d:
        if x[1] > 0:
            data2.append(x)
    return data2

# ✅ Good
def filter_matched_tracks(tracks: list[Track], include_skipped: bool = False) -> list[Track]:
    return [t for t in tracks if t.spotify_ref is not None or (include_skipped and t.spotify_ref == "SKIP")]
```

---

## Functions

- **Do one thing**: a function that does two things should be two functions
- **Keep them short**: aim for < 20 lines; if it needs scrolling, split it
- **Limit parameters**: > 3 parameters is a signal to introduce a dataclass or config object
- **No flag arguments**: a boolean parameter that changes behavior is two functions in disguise
- **Return early** (guard clauses): handle invalid/edge cases at the top, keep the happy path unindented

```python
# ❌ Bad: flag argument + deeply nested happy path
def sync_track(track, force=False):
    if track:
        if force or not track.spotify_ref:
            result = matcher.match(track)
            if result:
                track.spotify_ref = result
                return True
    return False

# ✅ Good: guard clauses + split by intent
def sync_track(track: LocalTrack) -> bool:
    if not track:
        return False
    if track.spotify_ref and not _should_force_sync(track):
        return False
    result = matcher.match(track)
    if not result:
        return False
    track.spotify_ref = result
    return True
```

---

## SOLID Principles

### S — Single Responsibility
Each class/module has exactly one reason to change.

```python
# ❌ Bad: one class does matching AND persistence
class TrackMatcher:
    def match(self, track): ...
    def save_to_file(self, track): ...

# ✅ Good: separate concerns
class TrackMatcher:
    def match(self, track: LocalTrack) -> str | None: ...

class TrackRepository:
    def save(self, track: LocalTrack) -> None: ...
```

### O — Open/Closed
Classes should be open for extension, closed for modification.
Prefer composition and polymorphism over `if/elif` chains keyed on type.

```python
# ❌ Bad: must modify this function to support a new source
def get_track_title(track):
    if track.source == "local":
        return track.id3_title
    elif track.source == "spotify":
        return track.api_name

# ✅ Good: each track type owns its behavior
class Track(ABC):
    @property
    @abstractmethod
    def title(self) -> str: ...

class LocalTrack(Track):
    @property
    def title(self) -> str:
        return self._tag.title

class SpotifyTrack(Track):
    @property
    def title(self) -> str:
        return self._data["name"]
```

### L — Liskov Substitution
Subclasses must be usable wherever the base class is expected — no surprises.

- Never narrow preconditions or widen postconditions in overrides
- If a subclass must raise `NotImplementedError` for part of the interface, the abstraction is wrong — split it

### I — Interface Segregation
Keep abstract bases small and focused. Clients should not depend on methods they don't use.

```python
# ❌ Bad: forces every track to implement Spotify-specific methods
class Track(ABC):
    def title(self) -> str: ...
    def fetch_audio_features(self) -> dict: ...  # only meaningful for Spotify

# ✅ Good: split the interface
class Track(ABC):
    def title(self) -> str: ...

class RemoteTrack(Track, ABC):
    def fetch_audio_features(self) -> dict: ...
```

### D — Dependency Inversion
High-level modules depend on abstractions, not concrete implementations.
Pass dependencies in; don't create them inside a function.

```python
# ❌ Bad: hard-coded dependency
class PlaylistSyncer:
    def __init__(self):
        self._matcher = SpotifyMatcher()  # impossible to test or swap

# ✅ Good: inject the dependency
class PlaylistSyncer:
    def __init__(self, matcher: Matcher) -> None:
        self._matcher = matcher
```

---

## DRY — Don't Repeat Yourself

Every piece of knowledge should have a single, authoritative representation.

- Extract duplicated logic into a named function — even if called only twice, if both usages encode the same concept
- Deduplicate configuration into constants or dataclasses
- Prefer data-driven structure over copy-pasted `if/elif` blocks
- **Rule of three**: tolerate duplication once; refactor on the third occurrence

```python
# ❌ Bad: same normalization logic in two places
def match_by_title(query: str) -> ...:
    q = query.lower().strip().replace("-", " ")
    ...

def search_library(query: str) -> ...:
    q = query.lower().strip().replace("-", " ")
    ...

# ✅ Good: extracted once, named clearly
def normalize_query(query: str) -> str:
    return query.lower().strip().replace("-", " ")
```

---

## Abstraction Levels

Each function should operate at a single level of abstraction.
Mix high-level orchestration with low-level detail is hard to read and test.

```python
# ❌ Bad: mixes orchestration with raw string parsing
def import_playlist(path: str) -> None:
    with open(path) as f:
        lines = [l.strip() for l in f if not l.startswith("#") and l.strip()]
    tracks = [LocalTrack(p) for p in lines]
    playlist = SpotifyPlaylist.create(tracks[0].title)
    ...

# ✅ Good: each level reads as a summary of the one below
def import_playlist(path: str) -> None:
    tracks = _load_tracks_from_m3u(path)
    playlist = _create_spotify_playlist(tracks)
    _sync_tracks_to_playlist(playlist, tracks)
```

---

## Testability

Write code that is easy to test in isolation.

- **Inject dependencies** — never instantiate collaborators inside business logic
- **Avoid global state** — singletons are acceptable at the boundary, not deep in domain logic
- **Pure functions first** — prefer functions with no side effects; isolate I/O at the edges
- **Small units** — a function that does one thing is trivially testable
- **Avoid hidden coupling to filesystem, time, or network** — pass these as parameters or behind interfaces
- **Design for fakes** — if a class is hard to fake, its interface is probably too large

```python
# ❌ Hard to test: couples business logic to system time
def is_token_expired() -> bool:
    return datetime.now() > self._expiry

# ✅ Easy to test: time is injected
def is_token_expired(now: datetime | None = None) -> bool:
    return (now or datetime.now()) > self._expiry
```

---

## Error Handling

- **Be explicit**: catch specific exception types, never bare `except:`
- **Fail fast**: validate inputs at function entry, before doing any work
- **Define domain exceptions**: use custom exception classes for expected failure modes
- **Don't swallow errors**: if you catch, either handle or re-raise with context
- **Propagate context**: use `raise X from e` to preserve the original traceback

```python
# ❌ Bad
def load_track(path):
    try:
        return LocalTrack(path)
    except:
        return None  # caller has no idea what went wrong

# ✅ Good
class TrackLoadError(Exception): ...

def load_track(path: str) -> LocalTrack:
    if not Path(path).exists():
        raise FileNotFoundError(f"Track file not found: {path}")
    try:
        return LocalTrack(path)
    except Exception as e:
        raise TrackLoadError(f"Failed to load track at {path}") from e
```

---

## Complexity & Readability

- **Cyclomatic complexity**: aim for ≤ 5 per function; refactor when it grows
- **Nesting depth**: max 2–3 levels; use guard clauses, extracted helpers, or comprehensions to flatten
- **Comprehensions**: use for simple transformations; switch to a loop when logic needs explanation
- **Comments explain *why*, not *what***: the code describes what happens; a comment explains a non-obvious constraint, trade-off, or domain rule
- **Dead code**: delete it; version control is the history

```python
# ❌ Bad comment (restates the code)
# increment counter by 1
retry_count += 1

# ✅ Good comment (explains the non-obvious rule)
# Spotify rate-limits to 1 req/s; back off exponentially after the first failure
```

---

## Scalability & Maintainability

- **Prefer immutability**: use `dataclasses(frozen=True)` or `NamedTuple` for value objects
- **Encapsulate change**: identify the parts most likely to change and hide them behind an interface
- **Avoid premature optimization**: write clear code first; optimize only when profiling shows a bottleneck
- **Configuration over hardcoding**: thresholds, limits, external URLs belong in config, not in logic
- **Consistent patterns**: pick one approach per problem domain and apply it throughout; inconsistency is its own form of complexity

---

## Module & Package Design

- **Single purpose per module**: a module named `utils.py` is always a sign of unclear ownership
- **Explicit public API**: use `__all__` in modules that are imported by external code
- **Avoid circular imports**: if two modules need each other, extract the shared concept into a third
- **Flat is better than nested**: don't add sub-packages until the namespace genuinely needs it
