# Research: Deezer Integration via ARL

**Feature**: `007-deezer-integration`  
**Date**: 2026-04-24  
**Branch**: `007-deezer-integration`

---

## Decision 1: deezer-py v1.3.7 — Authentication via ARL

**Decision**: Use the `Deezer` facade class with `login_via_arl(arl: str) -> bool`.

**Rationale**: The `GW` class requires a pre-configured `requests.Session` with the ARL cookie already set. The `Deezer` facade handles all cookie/session setup internally. `login_via_arl` is the designed entry point for ARL-based auth and returns `True`/`False` — no exception on invalid ARL, so we must check the return value explicitly and raise `DeezerAuthenticationError` (never logging the ARL value).

```python
from deezer import Deezer

dz = Deezer()
if not dz.login_via_arl(arl):
    raise DeezerAuthenticationError("Deezer authentication failed — check your ARL in config.ini")
```

**Invalid/expired ARL behaviour**: `login_via_arl` calls `gw.get_user_data()`; if `USER_ID == 0`, returns `False`. No exception is raised. An expired ARL at runtime may raise `GWAPIError` on subsequent calls.

**Alternatives considered**:
- Passing the ARL cookie directly to `GW.__init__` via a manual `requests.Session` — rejected; bypasses the auth-check logic in `Deezer.login_via_arl`.

---

## Decision 2: ISRC Lookup via Public API (not GW)

**Decision**: Use `dz.api.get_track_by_ISRC(isrc)` for ISRC-based exact matching.

**Rationale**: The `GW` class has no ISRC endpoint. The public `API` class (`api.deezer.com`) is unauthenticated for track reads — ISRC lookup works without the ARL session. Response is the normalized public-API shape with lowercase keys (`id`, `title`, `isrc`, `link`, `artist.name`, `album.title`). We extract `id` from the response to construct the canonical permalink `https://www.deezer.com/track/{id}`.

```python
track_data = dz.api.get_track_by_ISRC(isrc)
track_id = str(track_data["id"])
# permalink = f"https://www.deezer.com/track/{track_id}"
```

**Error path**: Raises `APIError` or `DataException` if ISRC not found — catch and fall through to fuzzy search.

**Alternatives considered**:
- `dz.gw.get_track()` after resolving ID — requires a second round trip; unnecessary given the public API supports ISRC.

---

## Decision 3: Fuzzy Search via GW

**Decision**: Use `dz.gw.search(query, index=0, limit=10)` for fuzzy title/artist search.

**Rationale**: The GW search returns raw dict responses with all-caps keys (`SNG_ID`, `SNG_TITLE`, `ART_NAME`, `ALB_TITLE`, `DURATION`, `ISRC`). The `TRACK` sub-key holds the list: `results['TRACK']['data']`. The GW path is preferred over the public API for search because it uses the authenticated session and returns richer data in one call.

```python
results = dz.gw.search(f"{artist} {title}", index=0, limit=10)
tracks = results.get("TRACK", {}).get("data", [])
```

**Query strategy** (mirrors SpotifyMatcher): construct `"{artist}" "{title}"` for the primary attempt; fall back to title-only if no results. Non-Latin names are forwarded as-is.

**Alternatives considered**:
- `dz.api.advanced_search(artist=..., track=...)` — also viable but requires the ARL session for search quotas; selected GW as primary since we already have the authenticated session.

---

## Decision 4: Playlist CRUD via GW

**Decision**: All playlist mutations use `GW` methods. The `Deezer` facade exposes them as `dz.gw.*`.

| Operation | Method |
|-----------|--------|
| Create | `dz.gw.create_playlist(title, status, songs=[])` — returns `int` playlist ID |
| Read tracks | `dz.gw.get_playlist_tracks(playlist_id)` — returns list of raw GW track dicts |
| Add tracks | `dz.gw.add_songs_to_playlist(playlist_id, songs=[sng_id, ...])` |
| Remove tracks | `dz.gw.remove_songs_from_playlist(playlist_id, songs=[sng_id, ...])` |

**Visibility**: `status=0` for public, `status=1` for private (matches `PlaylistStatus.PUBLIC` / `PlaylistStatus.PRIVATE` enum if available, otherwise raw int).

**Permalink construction**: `https://www.deezer.com/track/{SNG_ID}` — built directly from the `SNG_ID` field of the raw GW dict.

---

## Decision 5: DeezerMatcher singleton pattern

**Decision**: Override `Matcher.get_instance()` in `DeezerMatcher` to inject `get_deezer_client()` instead of `get_spotify_client()`.

**Rationale**: `Matcher.get_instance()` is currently hardcoded to `get_spotify_client()` — a DI violation that is an existing known issue. Rather than modifying the base class (which would be a scope expansion), `DeezerMatcher` overrides `get_instance()` at the class level, following the same caching pattern via a class-level `__instance` attribute. This mirrors how `SpotifyMatcher` uses the base, without touching shared code.

```python
class DeezerMatcher(Matcher):
    __instance: "DeezerMatcher | None" = None

    @classmethod
    def get_instance(cls) -> "DeezerMatcher":
        if cls.__instance is None:
            cls.__instance = cls(deezer=get_deezer_client())
        return cls.__instance
```

**Alternatives considered**:
- Modifying `Matcher.get_instance()` to be generic — deferred; is a separate refactor (feature 004/005 scope).

---

## Decision 6: URL Validation — `_is_valid_deezer_url`

**Decision**: Define a module-level regex `DEEZER_TRACK_URL_PATTERN` in `deezer_matcher.py` and a helper `_is_valid_deezer_url(url: str) -> bool`.

**Acceptance regex** (read): `^https://(www\.)?deezer\.com(/[a-z]{2}(-[a-z]{2})?)?/track/(\d+)(\?.*)?$`

On **read**, accept any Deezer track URL variant — `www.` optional, locale segment optional (`/en`, `/fr`, `/en-gb`, …), query string optional (e.g., `?utm_campaign=...`). Extract the numeric track ID and reconstruct the canonical URL; discard locale and query string entirely.

On **write**, always emit the canonical form `https://www.deezer.com/track/<id>` — `www.` present, no locale, no query string. `DeezerTrack.permalink` always returns this form.

**Rationale**: FR-008 requires the matcher to distinguish a valid cached `TXXX:DEEZER` URL from a malformed value. Accepting locale variants prevents false-invalid results when a user manually copies a URL from the Deezer web player. Storing only the canonical form avoids locale ambiguity on read-back. The helper is defined once, used in `DeezerMatcher.match()` and in `DeezerTrack.__init__` for input validation.

---

## Decision 7: `compare.py` — new `deezer_compare.py`

**Decision**: Add `src/playlists/deezer_compare.py` as a parallel file to `compare.py`, rather than generalizing the existing Spotify compare logic.

**Rationale**: The existing `compare.py` imports Spotify-specific types (`SpotifyPlaylist`, `SpotifyTrack`) at module level. Generalizing it would require a wider refactor touching an in-use module. A parallel `deezer_compare.py` is narrowly scoped, immediately testable, and mirrors the existing pattern exactly.

**Alternatives considered**:
- Generalizing `compare.py` with a `platform: str` parameter — preferred long-term but out of scope for this feature.

---

## Decision 8: `Config` extension for ARL

**Decision**: Add a `deezer_arl` property to the `Config` class reading from `config.ini` `[DEEZER]` section.

```ini
[DEEZER]
ARL=
```

```python
@property
def deezer_arl(self) -> str:
    return self.config.get("DEEZER", "ARL")
```

The ARL is read at call time (not at module import), so the tool will fail fast with a clear `configparser.NoSectionError` or `NoOptionError` if the section is missing — the error message mentions the config file path but never echoes the ARL value itself.
