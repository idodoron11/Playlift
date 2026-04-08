# Research: Remove SpotifyAPI Singleton — Constructor Injection Refactor

**Branch**: `004-remove-spotifyapi-di`  
**Date**: 2026-04-08  
**Status**: Complete — all NEEDS CLARIFICATION resolved

---

## R-001: `@functools.cache` and mypy strict-mode compatibility

**Question**: Does `@functools.cache` on a function annotated with `-> spotipy.Spotify` pass
mypy strict mode?

**Decision**: Use `@functools.cache`.

**Rationale**: `functools.cache` is `lru_cache(maxsize=None)` and preserves the decorated
function's signature via `ParamSpec`/`TypeVar` in its implementation (Python 3.11+ stdlib
ships typed stubs). The project already has `[[tool.mypy.overrides]] module = ["spotipy",
"spotipy.*"], ignore_missing_imports = true`, and `api/spotify.py` has
`disallow_any_unimported = false`. mypy treats `spotipy.Spotify` as `Any` for the return
annotation, which is permitted under these overrides. Empirically confirmed: the existing
`api/spotify.py` already uses `-> spotipy.Spotify` as the return type of `get_instance()`
and passes mypy today.

**Alternatives considered**: 
- `cachetools.cached` — rejected; adds an external dependency for no benefit over stdlib.
- Module-level `_client: spotipy.Spotify | None = None` with manual `if _client is None` —
  rejected; `@functools.cache` is more declarative, removes mutable module-level state, and
  provides `cache_clear()` for test resets.

---

## R-002: `SpotifyMatcher._search` static → instance method migration

**Question**: Are there any external callers of `SpotifyMatcher._search` that would break
when it becomes an instance method?

**Decision**: Convert `_search` to a plain instance method (`def _search(self, query: str)`).

**Rationale**: Grep confirms `_search` is called in exactly four places:
1. `matchers/spotify_matcher.py:93` — `SpotifyMatcher._search(...)` (internal, `_match_by_isrc`)
2. `matchers/spotify_matcher.py:114` — `SpotifyMatcher._search(...)` (internal, `_match_by_fuzzy_search`)
3. `matchers/spotify_matcher.py:150` — `SpotifyMatcher._search(...)` (internal, `suggest_match`)
4. `tests/matchers/test_spotify_matcher.py` — via `patch.object(SpotifyMatcher, "_search")`.

All are internal. `patch.object(SpotifyMatcher, "_search")` works identically on instance
methods, so the test patch pattern is unaffected. The three internal callers change from
`SpotifyMatcher._search(q)` to `self._search(q)`.

**Alternatives considered**: Keep as `@staticmethod` and pass `client` as an extra parameter
— rejected; awkward for a private helper that logically belongs to the instance.

---

## R-003: `Matcher.__init__` guard removal safety

**Question**: Is it safe to remove the `if Matcher.__instance is not None: raise TypeError`
guard from `Matcher.__init__`? Does anything rely on it?

**Decision**: Remove the guard. `get_instance()` is the sole singleton enforcer.

**Rationale**: The guard was added to prevent accidental double-construction in prod, but
it also prevented using the constructor in tests — forcing the `Matcher._Matcher__instance =
None` reset hack in `_MatcherTestBase`. After removal:
- `get_instance()` still protects singleton semantics in production (it checks
  `if cls.__instance is None` before constructing).
- Tests construct `SpotifyMatcher(client=mock_client)` directly without acquiring the
  singleton slot.
- The constitution explicitly states: "Singletons MUST only be used at boundary layers;
  domain logic MUST receive all dependencies via injection." Direct construction is the
  desired pattern.

**Alternatives considered**: Keep the guard and add a `_testing=True` bypass flag — rejected;
the instructions explicitly prohibit "production-code changes to ease testing" that are not
genuine design improvements. Removing the guard is the correct design improvement.

---

## R-004: `SpotifyPlaylist` classmethod client threading

**Question**: `create()` and `create_from_another_playlist()` both call the Spotify API
(create playlist, look up current user). How does the `client=` parameter thread through?

**Decision**: Add `client: spotipy.Spotify | None = None` to both classmethods. `create()`
resolves the client once (`resolved = client or get_spotify_client()`) and passes it to the
`cls(playlist_id, client=resolved)` constructor call. `create_from_another_playlist()` passes
`client=` to `cls.create(...)`.

**Rationale**: This makes the full construction chain injectable in tests — a `SpotifyPlaylist`
unit test can call `SpotifyPlaylist.create(name, client=mock_client)` without patching the
global function. The `track_matcher()` used in `create_from_another_playlist` is a separate
concern (it is the `SpotifyMatcher` singleton); injecting a matcher is out of scope for this
refactor and not needed for the `SpotifyPlaylist` unit tests (they can mock `track_matcher()`
via `patch.object` if needed, or test `create_from_another_playlist` through the Spotify
playlist's construction path only).

**Alternatives considered**: Require both `client=` and `matcher=` on the classmethod — out
of scope per FR-003 and the agreed spec scope.

---

## R-005: `SpotifyTrack` construction in `SpotifyPlaylist._load_data`

**Question**: `_load_data` creates `SpotifyTrack(id, data=...)` inline. Must the same client
be forwarded?

**Decision**: Yes — per FR-004, `_load_data` must pass `client=self._client` to every
`SpotifyTrack` it constructs. This ensures a unit test that injects a mock client into
`SpotifyPlaylist` sees that same mock propagated to all tracks returned by `.tracks`.

**Rationale**: Without propagation, a test that asserts on `track.isrc` (which triggers
`SpotifyTrack.data` → `self._client.track(...)`) would fall back to `get_spotify_client()`
and fail in a test environment with no config. Propagation is the correct DI pattern.

---

## R-006: Existing tests that use `patch.object(SpotifyMatcher, "_search")`

**Question**: After `_search` becomes an instance method, do `patch.object` calls in tests
break?

**Decision**: No change needed. `patch.object(SpotifyMatcher, "_search", ...)` works for both
static and instance methods — it patches the attribute on the class object in both cases.

**Rationale**: Confirmed by Python unittest.mock semantics. `patch.object` targets the class
namespace, not the instance namespace. The existing `@patch.object(SpotifyMatcher, "_search")`
decorators in `test_spotify_matcher.py` remain valid after the conversion.

---

## Summary Table

| ID | Question | Decision |
|----|----------|----------|
| R-001 | `@functools.cache` mypy compat | ✅ Use it — no mypy issues |
| R-002 | `_search` external callers | ✅ None; convert to instance method |
| R-003 | `Matcher.__init__` guard removal | ✅ Safe; `get_instance()` is sole enforcer |
| R-004 | Classmethod client threading | ✅ Pass `client=` through `create()` chain |
| R-005 | `SpotifyTrack` in `_load_data` | ✅ Forward `client=self._client` |
| R-006 | `patch.object` for `_search` | ✅ Still works; no test changes needed there |
