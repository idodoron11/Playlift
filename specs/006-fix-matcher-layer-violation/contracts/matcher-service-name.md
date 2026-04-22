# Contract: `Matcher.service_name` ~~SUPERSEDED~~

> **SUPERSEDED**: This contract was removed during design review. `SpotifyMatcher` reads `SpotifyTrack.service_name` directly — `"SPOTIFY"` has a single definition on the `SpotifyTrack` class. The `Matcher` ABC does **not** declare `service_name`. This file is retained for history only.

**File**: `matchers/__init__.py`  
**Kind**: Abstract property added to existing `Matcher` ABC

## Purpose

Allows the `Matcher` ABC to know which service it works with — without hardcoding a string literal in any method body. Used by concrete matchers to call `source_track.service_ref(self.service_name)` when checking whether a source track is already matched.

## Abstract Interface

```python
class Matcher(ABC):

    @property
    @abstractmethod
    def service_name(self) -> str:
        """The streaming service identifier this matcher works with.

        Must match the service_name of the ServiceTrack subclass this matcher
        produces (e.g. SpotifyMatcher returns 'SPOTIFY' because it produces
        SpotifyTrack results, and SpotifyTrack.service_name == 'SPOTIFY').

        Returns:
            A non-empty uppercased string (e.g. 'SPOTIFY', 'DEEZER').
        """
        ...
```

## Invariants

- `service_name` MUST return the same value as `ServiceTrack.service_name` for the track type this matcher produces
- The value MUST be uppercased, stable, and non-empty

## Known Implementations

| Class | `service_name` |
|-------|----------------|
| `SpotifyMatcher` | `"SPOTIFY"` |

## Extension Guide

A future `DeezerMatcher` implementing this contract:
```python
class DeezerMatcher(Matcher):
    @property
    def service_name(self) -> str:
        return "DEEZER"
```
The base `Matcher._find_spotify_match_in_source_track` equivalent will call
`source_track.service_ref("DEEZER")` automatically — no further changes needed.
