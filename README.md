# Playlift

>  One tool to keep your music in sync everywhere: Spotify, Deezer, and your local library.

Playlift is a command-line tool that matches local audio files to streaming service tracks using fuzzy title/artist matching and ISRC lookup, then creates or syncs playlists on the target platform. Matched references are optionally embedded directly into your audio file's ID3/FLAC/M4A tags so every subsequent sync is instant.

---

## Features

- **Import** a local `.m3u` playlist to a new Spotify playlist
- **Sync** a local playlist to an existing Spotify playlist (full replace)
- **Match** tracks in place — embed Spotify references into your local files without creating a playlist
- **Compare** a local playlist with a Spotify playlist and print the diff
- **Find duplicates** in a local playlist by Spotify reference
- **Fuzzy matching** with configurable autopilot threshold; handles Cyrillic, CJK, and other non-Latin names
- **ISRC matching** for exact identification when metadata is available
- **Path remapping** (`--from-path` / `--to-path`) for cross-machine or cross-OS library paths
- **Embedded match cache** — Spotify references stored in `TXXX:SPOTIFY` ID3 tags survive across syncs; set `SKIP` to permanently ignore a track

---

## Requirements

- Python ≥ 3.11
- [uv](https://github.com/astral-sh/uv) (dependency management)
- A Spotify Developer application ([create one here](https://developer.spotify.com/dashboard))

---

## Installation

```bash
git clone https://github.com/idodoron11/playlist-sync.git
cd playlist-sync
uv sync
```

---

## Configuration

Copy the template and fill in your Spotify credentials:

```bash
mkdir -p ~/.playlist_sync
cp config/config_template.ini ~/.playlist_sync/config.ini
```

Edit `~/.playlist_sync/config.ini`:

```ini
[SPOTIFY]
CLIENT_ID=<your_client_id>
CLIENT_SECRET=<your_client_secret>
REDIRECT_URL=http://localhost:8888/callback
```

On first run you will be redirected to Spotify's OAuth page. The resulting token is cached locally for subsequent runs.

---

## Usage

All commands live under the `spotify` subcommand group.

### Import a local playlist to Spotify

Creates a new Spotify playlist from a local `.m3u` file.

```bash
uv run python main.py spotify import \
  --source  "path/to/playlist.m3u" \
  --destination "My New Playlist"
```

| Flag | Description |
|------|-------------|
| `--autopilot` | Auto-select the best fuzzy match without prompting |
| `--embed-matches` | Write Spotify references back into local file tags |
| `--public` | Create a public playlist (default: private) |
| `--from-path` / `--to-path` | Remap a path prefix (e.g. different drive letter on another machine) |

Multiple `--source` / `--destination` pairs can be passed in one invocation.

### Sync a local playlist to an existing Spotify playlist

Replaces all tracks in an existing Spotify playlist.

```bash
uv run python main.py spotify sync \
  --source      "path/to/playlist.m3u" \
  --destination "spotify:playlist:<id>"
```

Supports the same flags as `import`, plus `--sort-tracks` (alphabetical sort before sync).

### Match tracks without creating a playlist

Runs the matching pipeline and embeds references into local file tags — no Spotify playlist is created or modified.

```bash
uv run python main.py spotify match \
  --source "path/to/playlist.m3u" \
  --autopilot
```

### Compare a local playlist with a Spotify playlist

Prints tracks that exist only locally or only on Spotify.

```bash
uv run python main.py spotify compare \
  --source      "path/to/playlist.m3u" \
  --destination "spotify:playlist:<id>"
```

### Find duplicate tracks in a local playlist

Lists tracks that map to the same Spotify reference.

```bash
uv run python main.py spotify duplicates \
  --source "path/to/playlist.m3u"
```

### Batch import all playlists in a directory

```bash
uv run python sync_exported_playlists.py /path/to/playlists/
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

MIT
