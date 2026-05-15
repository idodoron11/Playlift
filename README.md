# Playlift

>  One tool to keep your music in sync everywhere: Spotify, Deezer, and your local library.

Playlift is a command-line tool that syncs music between your local library, Spotify, and Deezer. It matches tracks using fuzzy title/artist matching and ISRC lookup, then creates or syncs playlists on any supported platform. Matched references are optionally embedded directly into your audio file's ID3/FLAC/M4A tags so every subsequent sync is instant.

---

## Features

- **Import** a local `.m3u` playlist or a streaming service playlist to a new Spotify or Deezer playlist
- **Sync** a local or service playlist into an existing Spotify or Deezer playlist (full replace)
- **Cross-platform sync** — pass a Spotify URI/URL or Deezer URL as `--source`; the platform is auto-detected
- **Match** tracks in place — embed service references into your local files without creating a playlist
- **Compare** a local playlist with a Spotify or Deezer playlist and print the diff
- **Find duplicates** in a local playlist by service reference
- **Fuzzy matching** with configurable autopilot threshold; handles Cyrillic, CJK, and other non-Latin names
- **ISRC matching** for exact identification when metadata is available
- **Path remapping** (`--from-path` / `--to-path`) for cross-machine or cross-OS library paths
- **Embedded match cache** — references stored in `TXXX:SPOTIFY` / `TXXX:DEEZER` ID3 tags survive across syncs; set `SKIP` to permanently ignore a track

---

## Requirements

- Python ≥ 3.11
- [uv](https://github.com/astral-sh/uv) (dependency management)
- A Spotify Developer application ([create one here](https://developer.spotify.com/dashboard)) — for Spotify commands
- A Deezer ARL cookie — for Deezer commands (see [Configuration](#configuration))

---

## Installation

### As a tool (end-user)

Install Playlift as a globally available command using [uv](https://github.com/astral-sh/uv):

```bash
uv tool install git+https://github.com/idodoron11/playlist-sync.git
```

The `playlift` and `playlift-batch` commands are then available system-wide — no `uv run` prefix needed.

### For development

```bash
git clone https://github.com/idodoron11/playlist-sync.git
cd playlist-sync
uv sync
```

When running from the cloned directory, prefix all commands with `uv run` (e.g. `uv run playlift ...`).

---

## Configuration

Create `~/.playlift/config.ini` and fill in your credentials:

```bash
mkdir -p ~/.playlift
```

Then create `~/.playlift/config.ini` with the following content:

```ini
[SPOTIFY]
CLIENT_ID=<your_spotify_client_id>
CLIENT_SECRET=<your_spotify_client_secret>
REDIRECT_URL=http://127.0.0.1:3040

[DEEZER]
ARL=<your_deezer_arl_cookie>
```

**Spotify:** On first run you will be redirected to Spotify's OAuth page. The resulting token is cached locally for subsequent runs.

**Deezer:** The ARL is a long-lived session cookie from your Deezer browser session. Open Deezer in a browser, open DevTools → Application → Cookies → `arl`, and copy the value.

---

## Usage

Commands are grouped by service: `spotify` and `deezer`. Both groups expose the same five sub-commands: `import`, `sync`, `match`, `compare`, and `duplicates`.

> **Note:** Examples below use `uv run playlift` (development install). If you installed with `uv tool install`, drop the `uv run` prefix and call `playlift` directly.

### Spotify

##### Import a playlist to Spotify

Creates a new Spotify playlist from a local `.m3u` file, a local directory, or a streaming service playlist.

`--source` accepts any of:
- A local `.m3u` file path
- A local directory path (imports the whole library)
- A Spotify URI: `spotify:playlist:<id>`
- A Spotify URL: `https://open.spotify.com/playlist/<id>`
- A Deezer URL: `https://www.deezer.com/en/playlist/<id>`

```bash
# From a local file
uv run playlift spotify import \
  --source  "path/to/playlist.m3u" \
  --destination "My New Playlist"

# From a Deezer playlist
uv run playlift spotify import \
  --source  "https://www.deezer.com/en/playlist/1313621735" \
  --destination "My New Playlist"
```

| Flag | Description |
|------|-------------|
| `--autopilot` | Auto-select the best fuzzy match without prompting |
| `--embed-matches` | Write Spotify references back into local file tags (silently ignored for service sources) |
| `--public` | Create a public playlist (default: private) |
| `--from-path` / `--to-path` | Remap a path prefix — local sources only; incompatible with service sources |

Multiple `--source` / `--destination` pairs can be passed in one invocation to import several playlists at once. Each `--source` is paired with the `--destination` at the same position — the counts must match.

```bash
uv run playlift spotify import \
  --source "rock.m3u"    --destination "Rock Hits" \
  --source "jazz.m3u"    --destination "Jazz Classics" \
  --source "pop.m3u"     --destination "Pop Favourites"
```

#### Sync a playlist to an existing Spotify playlist

Replaces all tracks in an existing Spotify playlist. `--source` accepts the same formats as `import` (local `.m3u` or directory, Spotify URI/URL, or Deezer URL).

```bash
# From a local file
uv run playlift spotify sync \
  --source      "path/to/playlist.m3u" \
  --destination "spotify:playlist:<id>"

# From a Deezer playlist
uv run playlift spotify sync \
  --source      "https://www.deezer.com/en/playlist/1313621735" \
  --destination "spotify:playlist:<id>"
```

Supports the same flags as `import`, plus `--sort-tracks` (alphabetical sort before sync).

#### Match tracks without creating a playlist

Runs the matching pipeline and embeds references into local file tags — no Spotify playlist is created or modified.

```bash
uv run playlift spotify match \
  --source "path/to/playlist.m3u" \
  --autopilot
```

#### Compare a local playlist with a Spotify playlist

Prints tracks that exist only locally or only on Spotify.

```bash
uv run playlift spotify compare \
  --source      "path/to/playlist.m3u" \
  --destination "spotify:playlist:<id>"
```

#### Find duplicate tracks in a local playlist

Lists tracks that map to the same Spotify reference.

```bash
uv run playlift spotify duplicates \
  --source "path/to/playlist.m3u"
```

### Deezer

#### Import a playlist to Deezer

Creates a new Deezer playlist from a local `.m3u` file, a local directory, or a streaming service playlist. `--source` accepts the same formats as `spotify import` (local `.m3u` or directory, Spotify URI/URL, or Deezer URL).

```bash
# From a local file
uv run playlift deezer import \
  --source      "path/to/playlist.m3u" \
  --destination "My New Playlist"

# From a Spotify playlist
uv run playlift deezer import \
  --source      "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M" \
  --destination "My New Playlist"
```

Supports the same flags as `spotify import` (`--autopilot`, `--embed-matches`, `--public`, `--from-path` / `--to-path`).

#### Sync a playlist to an existing Deezer playlist

`--source` accepts the same formats as `spotify sync` (local `.m3u` or directory, Spotify URI/URL, or Deezer URL).

```bash
# From a local file
uv run playlift deezer sync \
  --source      "path/to/playlist.m3u" \
  --destination "<deezer_playlist_id>"

# From a Spotify playlist
uv run playlift deezer sync \
  --source      "spotify:playlist:37i9dQZF1DXcBWIGoYBM5M" \
  --destination "<deezer_playlist_id>"
```

Supports the same flags as `spotify sync` (including `--sort-tracks`).

#### Match tracks without creating a playlist

Embeds Deezer references into local file tags — no Deezer playlist is created or modified.

```bash
uv run playlift deezer match \
  --source "path/to/playlist.m3u" \
  --autopilot
```

#### Compare a local playlist with a Deezer playlist

Prints tracks that exist only locally or only on Deezer.

```bash
uv run playlift deezer compare \
  --source      "path/to/playlist.m3u" \
  --destination "<deezer_playlist_id>"
```

#### Find duplicate tracks in a local playlist

Lists tracks that map to the same Deezer reference.

```bash
uv run playlift deezer duplicates \
  --source "path/to/playlist.m3u"
```

### Batch import all playlists in a directory

```bash
uv run playlift-batch /path/to/playlists/
```

---

## Development

```bash
# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type-check
uv run mypy .

# Tests (unit only)
uv run pytest tests/ -m "not integration"
```

### Git hooks

The project uses [pre-commit](https://pre-commit.com/) to enforce formatting, linting, and type-checking before every commit. Hooks run `ruff-format`, `ruff --fix`, and `mypy` automatically.

Install the hooks once after cloning:

```bash
uv run pre-commit install
```

To run all hooks manually against every file:

```bash
uv run pre-commit run --all-files
```

---

## License

GPLv3
