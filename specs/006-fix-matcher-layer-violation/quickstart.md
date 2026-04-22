# Quickstart: Decouple Matcher from Concrete Track Implementation

## What changes

Two new ABCs are introduced in `tracks/__init__.py`. Existing classes adopt them:

| Class | Change |
|-------|--------|
| `ServiceTrack` | **New** — abstract base for streaming service tracks |
| `EmbeddableTrack` | **New** — single-method write contract for tracks that store match data |
| `Track` | Gains concrete `service_ref(service_name) -> str \| None` (returns `None` by default) |
| `SpotifyTrack` | Extends `ServiceTrack`; adds `permalink`, `service_name` |
| `LocalTrack` | Implements `EmbeddableTrack`; overrides `service_ref`; adds `embed_match` |
| `Matcher` | **(no change)** |
| `SpotifyMatcher` | Removes `LocalTrack` import; uses `track.service_ref(SpotifyTrack.service_name)` on read path; delegates write to `embed_match` |

---

## How to add a new streaming service (e.g. Deezer)

### Step 1 — Create the track type

```python
# tracks/deezer_track.py
from tracks import ServiceTrack

class DeezerTrack(ServiceTrack):
    def __init__(self, track_id: str, data: dict | None = None) -> None:
        self._id = track_id
        self._data = data

    @property
    def permalink(self) -> str:
        return f"https://www.deezer.com/track/{self._id}"

    @property
    def service_name(self) -> str:
        return "DEEZER"

    # ... implement remaining Track abstract properties (artists, title, etc.)
```

### Step 2 — Create the matcher

```python
# matchers/deezer_matcher.py
from matchers import Matcher
from tracks import Track
from tracks.deezer_track import DeezerTrack

class DeezerMatcher(Matcher):
    def match(self, track: Track) -> DeezerTrack | None:
        # ... matching logic
        pass

    # ... implement remaining Matcher abstract methods
```

### Step 3 — Nothing else changes

- `LocalTrack.embed_match` already handles any `ServiceTrack` — it reads `match.service_name` dynamically.
- A local audio file can now hold both `SPOTIFY` and `DEEZER` tags simultaneously.
- Reading them back: `local_track.service_ref("DEEZER")` and `local_track.service_ref("SPOTIFY")` are independent.

---

## How embed_match works end-to-end

```
SpotifyMatcher.match_list(source_tracks, embed_matches=True)
  │
  ├─ for each (source_track, spotify_match) in pairs_to_embed:
  │
  │   SpotifyMatcher._update_spotify_match_in_source_track(source_track, spotify_match)
  │     │
  │     └─ if isinstance(source_track, EmbeddableTrack):
  │            source_track.embed_match(spotify_match)
  │              │
  │              ├─ if service_ref("SPOTIFY") != spotify_match.permalink:
  │              │      _set_custom_tag("SPOTIFY", spotify_match.permalink)
  │              │
  │              └─ if spotify_match.isrc and self.isrc != normalize(spotify_match.isrc):
  │                     self.isrc = normalize(spotify_match.isrc)
  │
  └─ source tracks that are NOT EmbeddableTrack → silently skipped
```

---

## Checking whether a source track is already matched

```python
# Inside SpotifyMatcher._find_spotify_match_in_source_track:
return track.service_ref(SpotifyTrack.service_name)  # reads the "SPOTIFY" tag, or None
# Track.service_ref returns None by default — no isinstance guard needed
```

---

## Running the tests

```bash
uv run pytest tests/tracks/test_local_track.py -k "EmbedMatch"   # new embed_match tests
uv run pytest tests/matchers/test_spotify_matcher.py -k "Embed"  # updated delegation tests
uv run pytest tests/                                              # full suite
uv run mypy .
uv run ruff check .
```
