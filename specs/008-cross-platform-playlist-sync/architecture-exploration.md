# Playlist Sync Architecture Exploration

## Completed Tasks
- [x] Explored src/playlists/__init__.py - base classes
- [x] Explored src/tracks/__init__.py - Track hierarchy
- [x] Explored src/matchers/__init__.py - Matcher base class
- [x] Explored main.py - CLI wiring
- [x] Explored playlist implementations (Local, Spotify, Deezer)
- [x] Explored matcher implementations (Spotify, Deezer)
- [x] Explored track implementations (Local, Spotify, Deezer)
- [x] Explored singleton.py - singleton pattern
- [x] Explored compare modules

## Key Findings

### Abstract Base Classes (src/playlists/__init__.py)

1. **TrackCollection** (ABC)
   - Single abstract property: `tracks: Iterable[Track]`

2. **SyncTarget** (ABC)
   - Static method: `track_matcher() -> Matcher` (returns platform-specific matcher)

3. **Playlist** (ABC, extends TrackCollection)
   - Abstract methods:
     - `remove_track(tracks: list[Track])`
     - `add_tracks(track: Track)`

4. **CompareResult** (Generic dataclass)
   - `source_only: list[_S]` - tracks in first playlist only
   - `target_only: list[_T]` - tracks in second playlist only

### Track Hierarchy (src/tracks/__init__.py)

1. **Track** (ABC) - Base for all tracks
   - Properties: `artists`, `title`, `album`, `duration`, `track_id`, `track_number`, `isrc`
   - Methods: `service_ref(service_name)`, `__eq__`, `__hash__`, `__repr__`

2. **ServiceTrack** (ABC, extends Track)
   - For streaming service tracks only
   - Properties: `permalink` (canonical URL), `service_name` (uppercased identifier)

3. **EmbeddableTrack** (ABC)
   - For tracks that persist match data (LocalTrack only)
   - Method: `embed_match(match: ServiceTrack)`

### Track Implementations

1. **LocalTrack** (extends Track, EmbeddableTrack)
   - Reads/writes ID3 metadata from audio files (.mp3, .flac, .m4a)
   - Properties: `file_path`, `spotify_ref`, `spotify_id`
   - Methods: `service_ref()`, `embed_match()`, `isrc` (getter/setter)

2. **SpotifyTrack** (extends ServiceTrack)
   - service_name = "SPOTIFY"
   - Lazy-loads track data from Spotify API
   - Properties: `track_url`, `permalink`

3. **DeezerTrack** (extends ServiceTrack)
   - service_name = "DEEZER"
   - Accepts GW response dict or public API dict on construction
   - Normalizes various key formats (SNG_ID/id, SNG_TITLE/title, etc.)

### Playlist Implementations

1. **LocalPlaylist** (extends Playlist)
   - Reads .m3u files, loads LocalTrack instances
   - Optional PathMapper for path remapping
   - Methods: `remove_track()`, `add_tracks()`, `save_playlist()`

2. **LocalLibrary** (extends TrackCollection)
   - Recursively scans directory for audio files (.mp3, .flac, .m4a)
   - Returns list of LocalTrack instances

3. **SpotifyPlaylist** (extends Playlist, SyncTarget)
   - Class methods: `create()`, `create_from_another_playlist()`
   - Methods: `import_tracks()`, `clear()`, `remove_track()`, `add_tracks()`
   - Lazy-loads playlist data from Spotify API
   - Batches add/remove operations (100 tracks per API call)

4. **DeezerPlaylist** (extends Playlist, SyncTarget)
   - Class methods: `create()`, `create_from_another_playlist()`
   - Methods: `import_tracks()`, `sync_tracks()`, `remove_track()`, `add_tracks()`
   - Caches tracks internally; invalidates cache on mutations
   - De-duplicates when adding tracks (tracks not already in playlist)

### Matcher Implementations

**Base Matcher** (src/matchers/__init__.py, ABC)
- Methods:
  - `match(track) -> Track | None` - resolve a single track
  - `suggest_match(track) -> Iterable[Track]` - return candidates
  - `match_list(tracks, autopilot, embed_matches) -> list[Track]` - batch resolution
  - Static: `track_distance(track1, track2) -> tuple[float, float, float, float]` - distance metrics
  - Static: `choose_suggestion(track, suggestions) -> int` - interactive selection
  - Instance: `_match_constraints(source_track, suggestion) -> bool` - validation

- Singleton: `get_instance() -> Matcher` class method
- Special handling: Non-Latin artist names bypass artist similarity check

**SpotifyMatcher**
- 4-step resolution strategy:
  1. Check `TXXX:SPOTIFY` tag in LocalTrack (raise SkipTrackError if "SKIP")
  2. ISRC lookup via Spotify /search endpoint
  3. Fuzzy search (artist/album/title components)
  4. Return best match or None
- Special: `_prefetch_isrc_data()` batch-fetches ISRC for matches (up to 50 per request)

**DeezerMatcher**
- 4-step resolution strategy:
  1. Check `TXXX:DEEZER` tag (raise SkipTrackError if "SKIP")
  2. ISRC lookup via Deezer API
  3. Fuzzy search via GW endpoint
  4. Return best match or None
- Handles URL normalization/extraction for cached Deezer refs

### Singleton Pattern (src/singleton.py)

Uses metaclass-based singleton:
```python
class Singleton(type):
    _instances: ClassVar[dict[type, Any]] = {}
    def __call__(cls, ...):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(...)
        return cls._instances[cls]
```

Matchers use `get_instance()` class method for controlled singleton access.

### CLI Wiring (main.py)

**Spotify Commands:**
- `spotify import` - create new Spotify playlist from local file(s)
- `spotify sync` - sync existing Spotify playlist with local file
- `spotify match` - match local tracks without creating playlist
- `spotify compare` - compare local m3u with Spotify playlist
- `spotify duplicates` - find duplicate Spotify refs in local file

**Deezer Commands:**
- `deezer import` - create new Deezer playlist from local file(s)
- `deezer sync` - sync existing Deezer playlist with local file
- `deezer match` - match local tracks
- `deezer compare` - compare local m3u with Deezer playlist
- `deezer duplicates` - find duplicate Deezer refs

All commands support:
- `--autopilot` - auto-select first match when multiple candidates exist
- `--embed-matches` - write service refs back to ID3 tags
- `--from-path`/`--to-path` - path prefix remapping

### Playlist Comparison (compare.py, deezer_compare.py)

**compare_playlists()** (Spotify)
- Loads LocalPlaylist and SpotifyPlaylist
- Identifies local tracks by `spotify_id` property
- Returns CompareResult[LocalTrack, SpotifyTrack]

**compare_deezer_playlists()** (Deezer)
- Loads source (LocalPlaylist/LocalLibrary) and DeezerPlaylist
- Matches via `service_ref("DEEZER")` normalized URLs
- Returns CompareResult[Track, DeezerTrack]

### PathMapper (path_mapper.py)

- Maps file paths from one prefix to another using pathlib
- Pass-through for non-matching paths
- Raises InvalidPathMappingError if from_path is empty
