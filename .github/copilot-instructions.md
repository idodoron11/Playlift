# Playlist Sync — AI Agent Guidelines

Workspace conventions for playlist-sync, a Python tool that syncs local m3u playlists to Spotify via fuzzy track matching.

## Code Style

**Python**: ≥3.11, PEP 8. Linting and formatting via **ruff** (`ruff check .` / `ruff format .`). Type checking via **mypy** (`mypy .`).

**Naming**:
- Private attributes: `_attribute` (single underscore, not double)
- Properties for lazy-loaded or computed values (e.g., `@property def spotify_ref`)
- Test helpers: `Mock`, `Spy`, `Fake` suffixes (e.g., `SpotifyPlaylistSpy`, `FakeLocalTrack`)

**Imports**: Group by stdlib, third-party, local. Each group separated by blank line.

## Architecture

### Layered Structure
```
CLI (main.py, sync_exported_playlists.py)
  ↓
Playlist Layer (playlists/) — LocalPlaylist, SpotifyPlaylist, compare.py
  ↓              ↓
  |       Matching Layer (matchers/) — SpotifyMatcher with fuzzy distance logic
  ↓              ↓
Track Layer (tracks/) — LocalTrack (ID3 metadata), SpotifyTrack (lazy-loaded)
  ↓
API Layer (api/) — SpotifyAPI singleton wrapping spotipy
  ↓
Config (config/) — CONFIG singleton, loaded on import
```

_Playlist depends on both Track and Matching directly; Matching depends on Track and API._

**Key Design Decisions**:
- **Singletons**: `SpotifyAPI.get_instance()` authorizes once; `Matcher.get_instance()` caches matcher state; `CONFIG` (read on import) holds credentials
- **Metadata Persistence**: Track matches stored as ID3 tag `TXXX:SPOTIFY_REF` (URL string or "SKIP" to ignore)
- **Abstract Bases**: `Playlist` and `Track` define common interface; subclasses implement Spotify or local variants
- **PathMapper**: One-directional (local path → mapped path); non-existent paths pass through unchanged

### Entry Points

| File | Purpose |
|------|---------|
| [main.py](../main.py) | CLI: `spotify import`, `spotify sync`, `spotify duplicates` with `--autopilot` and `--embed-matches` flags |
| [sync_exported_playlists.py](../sync_exported_playlists.py) | Batch import: recursively import all `.m3u` files from a directory |
| [cleanup.py](../cleanup.py) | Manual verification of close non-matches |
| [playlists/compare.py](../playlists/compare.py) | Diff logic: compare playlists via spotify_ref |

## Build and Test

**Install**:
```bash
uv sync
```

**Lint / Format / Type-check**:
```bash
uv run ruff check .
uv run ruff format .
uv run mypy .
```

**Dependencies** (key ones):
- `spotipy==2.23.0` — Spotify API client
- `music-tag==0.4.3` — Read/write ID3 metadata
- `click==8.1.7` — CLI framework
- `tqdm==4.66.2` — Progress bars

**Run**:
```bash
uv run python main.py spotify import <path-to-m3u-file>
uv run python main.py spotify sync <spotify-playlist-uri>
```

**Test**:
```bash
uv run pytest tests/
```

**Test Structure**: Tests mirror source (`tests/matchers/`, `tests/playlists/`, `tests/tracks/`). Use unittest.TestCase or plain functions with fixtures. See [tests/playlists/test_compare.py](../tests/playlists/test_compare.py) for lightweight fakes; [tests/playlists/spotify_playlist_spy.py](../tests/playlists/spotify_playlist_spy.py) for spy pattern.

## Conventions & Gotchas

### Special Values
- `"SKIP"` in `LocalTrack.spotify_ref` → skip this track (won't sync to Spotify)
- `None` spotify_ref → unmatched yet
- `"spotify://track/..."` or `"https://open.spotify.com/..."` → matched track

### Critical Anti-Patterns

1. **Non-bidirectional PathMapper**: `PathMapper.from_path()` remaps file paths (e.g., drive letters); reverse mapping doesn't exist. If `to_path()` is called with an unmapped path, it passes through unchanged.

2. **Repeated `SpotifyPlaylist.tracks` calls load fresh data**: Cache the result via `_data` attribute if making multiple accesses in a loop.

3. **LocalTrack constructor parses metadata immediately**: Don't create `LocalTrack(invalid_path)` expecting lazy loading—will raise on invalid file paths.

4. **Non-Latin artist names**: SpotifyMatcher has special handling for Cyrillic/CJK characters, but fails silently with a log warning. Test non-Latin searches manually.

5. **Config must exist at initialization**: `config/config_template.ini` is the template; actual config loaded from `~/.playlist_sync/config.ini` (set in imports). Missing config causes immediate failure on module load.

### Match Embedding

- Use `--embed-matches` flag to write Spotify refs back to ID3 tags: `LocalTrack.spotify_ref = "spotify://track/..."` persists to file
- `--autopilot` auto-matches close fuzzy matches (configurable threshold in SpotifyMatcher)

### Testing Patterns

**Mocks** (inherit from abstract bases):
- `MatcherMock` — controllable match results
- `PlaylistMock` — fake playlist with preset tracks
- `TrackMock` — stub tracks with fixed metadata

**Test Doubles**:
- `FakeLocalTrack`, `FakeSpotifyTrack` — lightweight, no file I/O
- `SpotifyPlaylistSpy` — wraps real class, captures method calls

**Dependency Injection**: Tests use monkeypatch/fixtures to inject mocks at runtime (no separate DI container).

## Quick Links

- **CLI Usage**: Run `python main.py --help` for command details
- **Spotify Auth**: See `config/config_template.ini` for setup steps
- **Fuzzy Matching**: [matchers/spotify_matcher.py](../matchers/spotify_matcher.py) uses SequenceMatcher distance ratios
- **Track Metadata**: [tracks/local_track.py](../tracks/local_track.py) parses ID3; [tracks/spotify_track.py](../tracks/spotify_track.py) wraps Spotify API

---

**Guiding Principle**: Playlist Sync maps real-world music files to Spotify catalog. When uncertain, ask: *"Will this change affect track matching accuracy or metadata persistence?"* If yes, test thoroughly with both Latin and non-Latin artist names.
