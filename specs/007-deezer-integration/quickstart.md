# Quickstart: Deezer Integration via ARL

**Feature**: `007-deezer-integration`  
**Branch**: `007-deezer-integration`

---

## Prerequisites

1. `deezer-py==1.3.7` added to `pyproject.toml` and installed:
   ```bash
   uv add deezer-py==1.3.7
   uv sync
   ```

2. Obtain your Deezer ARL cookie:
   - Log in to [deezer.com](https://www.deezer.com) in your browser.
   - Open DevTools → Application → Cookies → `.deezer.com` → copy the `arl` value.

3. Add the ARL to `~/.playlist_sync/config.ini` (or the local `src/config/config.ini`):
   ```ini
   [DEEZER]
   ARL=<your-arl-value-here>
   ```

---

## Usage

### Import a local playlist to Deezer

```bash
uv run python main.py deezer import \
  --source "/music/playlists/favourites.m3u" \
  --destination "My Favourites" \
  --autopilot \
  --embed-matches
```

### Sync a local playlist to an existing Deezer playlist

```bash
uv run python main.py deezer sync \
  --source "/music/playlists/favourites.m3u" \
  --destination "1234567890" \
  --autopilot \
  --embed-matches
```

### Pre-populate TXXX:DEEZER tags without touching Deezer

```bash
uv run python main.py deezer match \
  --source "/music/playlists/favourites.m3u" \
  --autopilot
```

### Compare a local playlist against a Deezer playlist

```bash
uv run python main.py deezer compare \
  --source "/music/playlists/favourites.m3u" \
  --destination "1234567890"
```

### Find duplicate tracks in a local playlist

```bash
uv run python main.py deezer duplicates \
  --source "/music/playlists/favourites.m3u"
```

---

## Path Remapping (optional)

Use `--from-path` / `--to-path` when the `.m3u` file references paths under a different
mount point than the current machine:

```bash
uv run python main.py deezer import \
  --source "/music/playlists/rock.m3u" \
  --destination "Rock" \
  --from-path "D:/Music" \
  --to-path "/mnt/nas/music"
```

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `DeezerAuthenticationError: Deezer authentication failed` | ARL expired or wrong | Refresh ARL from browser cookies |
| `configparser.NoSectionError: No section: 'DEEZER'` | Missing `[DEEZER]` section in config | Add section to `config.ini` |
| Track left unmatched with warning | ISRC absent and fuzzy search found no results | Run `deezer match` without `--autopilot` and manually confirm |
| `TXXX:DEEZER` tag not written | File is read-only | Check file permissions |
