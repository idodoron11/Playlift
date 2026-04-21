# Research: Decouple Playlist from SyncTarget

**Feature**: 005-decouple-playlist-synctarget  
**Date**: 2026-04-21

## Research Task 1: Python MRO with Multiple ABCs

**Question**: Does `class SpotifyPlaylist(Playlist, SyncTarget)` work correctly when both
`Playlist` and `SyncTarget` are ABCs with different abstract methods?

**Decision**: Yes — Python's C3 linearization handles this correctly.

**Rationale**: Verified empirically. A class inheriting from two ABCs must implement abstract
methods from both. A class inheriting from only one ABC must implement only that ABC's
abstract methods. MRO is: `[Concrete, Base1, Base2, ABC, object]`.

**Alternatives considered**: None — this is standard Python behavior since ABC was introduced
in Python 2.6. No workarounds or special handling required.

## Research Task 2: mypy Strict Mode + Multiple ABC Inheritance

**Question**: Does mypy in strict mode accept `@staticmethod @abstractmethod` on a standalone
ABC (not inheriting from `Playlist` or `TrackCollection`)?

**Decision**: Yes — mypy strict reports zero issues.

**Rationale**: Verified with `mypy --strict` on a minimal reproduction. The pattern
`class SyncTarget(ABC)` with `@staticmethod @abstractmethod def track_matcher() -> Matcher`
is fully type-safe and accepted without errors.

**Alternatives considered**: Using `typing.Protocol` instead of ABC — rejected because the
codebase consistently uses ABCs (`Playlist`, `TrackCollection`, `Matcher`) and Protocol
would introduce an inconsistent abstraction style.

## Research Task 3: `patch.object` Compatibility After Hierarchy Change

**Question**: Does `patch.object(SpotifyPlaylist, "track_matcher", ...)` continue to work
when `track_matcher` is inherited from `SyncTarget` rather than `Playlist`?

**Decision**: Yes — `patch.object` patches the attribute on the concrete class regardless
of which base class originally defined it.

**Rationale**: `unittest.mock.patch.object` uses `getattr`/`setattr` on the target object.
Method resolution order means `track_matcher` is found on `SpotifyPlaylist` via `SyncTarget`
in the MRO. Patching it replaces the attribute on the concrete class for the duration of
the context manager. This is standard mock behavior and does not depend on where in the
MRO the original method is defined.

**Alternatives considered**: None — this is the expected behavior of `patch.object`.
