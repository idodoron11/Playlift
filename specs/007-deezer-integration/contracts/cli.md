# Contract: `deezer` CLI Command Group

**Feature**: `007-deezer-integration`  
**Date**: 2026-04-24  
**Type**: CLI command schema

---

## Command Group: `deezer`

Entry point: `uv run python main.py deezer`

All commands share the top-level `deezer` group. No flags on the group itself.

---

### `deezer import`

Create a new Deezer playlist from one or more local `.m3u` files.

```
deezer import
  --source / -s   TEXT  (required, multiple)  Path to local .m3u file
  --destination / -d  TEXT  (required, multiple)  Name for the new Deezer playlist
  --autopilot           FLAG  Auto-accept matches above confidence threshold
  --embed-matches       FLAG  Write TXXX:DEEZER tag back to local audio files
  --public              FLAG  Create playlist as public (default: private)
  --from-path   TEXT    Source path prefix for remapping (requires --to-path)
  --to-path     TEXT    Destination path prefix (requires --from-path)
```

**Constraints**:
- Number of `--source` and `--destination` values must be equal.
- `--from-path` and `--to-path` must both be present or both absent.
- Always creates a new Deezer playlist regardless of name collisions (FR-019).

---

### `deezer sync`

Sync a local `.m3u` playlist to an existing Deezer playlist (add missing, remove extra).

```
deezer sync
  --source / -s   TEXT  (required)  Path to local .m3u file
  --destination / -d  TEXT  (required)  Deezer playlist ID or URL
  --autopilot           FLAG  Auto-accept matches above confidence threshold
  --embed-matches       FLAG  Write TXXX:DEEZER tag back to local audio files
  --sort-tracks         FLAG  Reorder Deezer playlist to match local .m3u order
  --from-path   TEXT    Source path prefix for remapping (requires --to-path)
  --to-path     TEXT    Destination path prefix (requires --from-path)
```

---

### `deezer match`

Resolve Deezer matches and write TXXX:DEEZER tags to local files without touching any Deezer playlist.

```
deezer match
  --source / -s   TEXT  (required, multiple)  Path to local .m3u file
  --autopilot           FLAG  Auto-accept matches above confidence threshold
  --from-path   TEXT    Source path prefix for remapping (requires --to-path)
  --to-path     TEXT    Destination path prefix (requires --from-path)
```

**Note**: Embedding is unconditional for this command (FR-005). No `--embed-matches` flag is present; tags are always written.

---

### `deezer compare`

Print a diff between a local `.m3u` playlist and a Deezer playlist.

```
deezer compare
  --source / -s   TEXT  (required)  Path to local .m3u file
  --destination / -d  TEXT  (required)  Deezer playlist ID or URL
  --from-path   TEXT    Source path prefix for remapping (requires --to-path)
  --to-path     TEXT    Destination path prefix (requires --from-path)
```

**Output** (stdout):
```
Only in local playlist:
  - Artist — Title

Only in Deezer playlist:
  - Artist — Title

No differences.  # (when playlists are identical)
```

---

### `deezer duplicates`

Report tracks in a local `.m3u` whose TXXX:DEEZER tag values appear more than once.

```
deezer duplicates
  --source / -s   TEXT  (required)  Path to local .m3u file
```

**Output** (stdout):
```
Duplicate Deezer references found:
  https://www.deezer.com/track/12345
    - /path/to/track1.mp3
    - /path/to/track2.mp3
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | User error (bad arguments, missing config) |
| 2 | Authentication failure (invalid/expired ARL) |
| 3 | Unrecoverable runtime error |
