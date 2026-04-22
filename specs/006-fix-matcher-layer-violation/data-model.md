# Data Model: Decouple Matcher from Concrete Track Implementation

## Class Hierarchy

```
ABC
├── Track (ABC)                         tracks/__init__.py
│   ├── ServiceTrack(Track, ABC)        tracks/__init__.py  [NEW]
│   │   └── SpotifyTrack(ServiceTrack)  tracks/spotify_track.py  [MODIFIED]
│   └── LocalTrack(Track, EmbeddableTrack)  tracks/local_track.py  [MODIFIED]
│
├── EmbeddableTrack (ABC)               tracks/__init__.py  [NEW]
│   └── LocalTrack (see above)
│
└── Matcher (ABC)                       matchers/__init__.py  [MODIFIED]
    └── SpotifyMatcher(Matcher)         matchers/spotify_matcher.py  [MODIFIED]
```

---

## `ServiceTrack(Track, ABC)` — NEW

Location: `tracks/__init__.py`

A streaming service track — a `Track` that is hosted on a remote service and has a canonical URL and service identifier.

| Member | Kind | Type | Description |
|--------|------|------|-------------|
| `permalink` | abstract property | `str` | Canonical URL for this track on its service (e.g. `https://open.spotify.com/track/…`) |
| `service_name` | abstract property | `str` | Uppercased key identifying the service; used as the ID3 custom tag name (e.g. `"SPOTIFY"`) |

**Invariants**:
- `permalink` MUST be a non-empty string
- `service_name` MUST be a non-empty, stable, uppercased string
- Only streaming service track types implement this contract; `LocalTrack` does NOT

---

## `EmbeddableTrack(ABC)` — NEW

Location: `tracks/__init__.py`

A track that can persist external match data (service references and ISRC) into durable storage. Orthogonal to the `Track` hierarchy — not all tracks are embeddable.

| Member | Kind | Type | Description |
|--------|------|------|-------------|
| `service_ref(service_name: str)` | abstract method | `str \| None` | Read the stored service reference for the given service name; returns `None` if absent |
| `embed_match(match: ServiceTrack)` | abstract method | `None` | Persist match data (service ref + ISRC) from `match` into this track's durable storage |

**Invariants**:
- `service_ref` MUST NOT raise on an absent key — return `None` instead
- `embed_match` MUST be idempotent: calling it twice with the same `match` results in one write (second call detects no change)
- `embed_match` MUST only write the service tag for `match.service_name`; other service tags MUST NOT be affected
- Only `LocalTrack` implements this contract; `SpotifyTrack` does NOT

---

## `SpotifyTrack(ServiceTrack)` — MODIFIED

Location: `tracks/spotify_track.py`

Additions only — no existing behavior changed.

| Member | Kind | Type | Description |
|--------|------|------|-------------|
| `permalink` | property | `str` | Returns `self.track_url` (e.g. `https://open.spotify.com/track/{id}`) |
| `service_name` | property | `str` | Returns `"SPOTIFY"` |

---

## `LocalTrack(Track, EmbeddableTrack)` — MODIFIED

Location: `tracks/local_track.py`

Additions only — no existing behavior changed. `spotify_ref` and `isrc` properties are unchanged.

| Member | Kind | Type | Description |
|--------|------|------|-------------|
| `service_ref(service_name: str)` | method | `str \| None` | Delegates to `self._get_custom_tag(service_name)`; returns `None` if absent |
| `embed_match(match: ServiceTrack)` | method | `None` | Writes `match.permalink` under `match.service_name` tag if changed; writes `match.isrc` (normalized) if changed |

**`embed_match` write rules**:
1. If `self.service_ref(match.service_name) != match.permalink` → write via `self._set_custom_tag(match.service_name, match.permalink)`
2. If `match.isrc is not None` and `self.isrc != _normalize_isrc(match.isrc)` → write via `self.isrc = _normalize_isrc(match.isrc)`
3. If neither condition holds → no write (idempotent)

---

## `Matcher(ABC)` — MODIFIED

Location: `matchers/__init__.py`

Addition only — no existing behavior changed.

| Member | Kind | Type | Description |
|--------|------|------|-------------|
| `service_name` | abstract property | `str` | The service identifier this matcher works with (e.g. `"SPOTIFY"`); used to look up stored refs on source tracks |

---

## `SpotifyMatcher(Matcher)` — MODIFIED

Location: `matchers/spotify_matcher.py`

| Change | Before | After |
|--------|--------|-------|
| Import | `from tracks.local_track import LocalTrack, _normalize_isrc` | `from tracks import EmbeddableTrack` |
| `service_name` | (absent) | `@property` returning `"SPOTIFY"` |
| `_find_spotify_match_in_source_track` | `isinstance(track, LocalTrack)` → `track.spotify_ref` | `isinstance(track, EmbeddableTrack)` → `track.service_ref(self.service_name)` |
| `_update_spotify_match_in_source_track` | Direct tag writes via `LocalTrack` attributes | `if isinstance(source_track, EmbeddableTrack): source_track.embed_match(match)` |

---

## Service Reference Storage

Service references are stored as audio file custom tags. The tag key is the uppercased `service_name`.

| Audio Format | Tag Mechanism | Example Key |
|---|---|---|
| MP3 | `TXXX` frame with `desc=SERVICE_NAME` | `TXXX:SPOTIFY` |
| FLAC | Vorbis comment | `SPOTIFY` |
| M4A | iTunes freeform tag | `----:com.apple.iTunes:SPOTIFY` |

Multiple service references coexist independently — each occupies its own distinct tag key.
ISRC is stored in a single universal tag (TSRC for MP3, `isrc` Vorbis comment for FLAC, iTunes freeform for M4A) regardless of how many service references are stored.
