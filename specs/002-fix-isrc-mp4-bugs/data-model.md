# Data Model: Fix Three M4A ISRC Tag Bugs

**Branch**: `002-fix-isrc-mp4-bugs` | **Date**: 2026-04-06

## Scope

No new entities, tables, or data structures are introduced by this feature.

The fix operates entirely within the existing data model:

| Existing entity | Change |
|---|---|
| `LocalTrack._mutagen_file` (MP4 in-memory tags dict) | Read path gains case-insensitive key fallback; write path uses `[MP4FreeForm(...)]` |
| `LocalTrack._file_path` (on-disk M4A file) | No structural change; iTunes freeform atoms remain the storage format |

## One New Constant

```python
# tracks/local_track.py — module level
_ITUNES_FREEFORM_PREFIX = "----:com.apple.iTunes:"
```

This is a named constant extracted from the repeated literal in `_get_custom_tag` and `_set_custom_tag`. Not a new entity — just an authoritative home for an existing value.

## No contracts/ directory needed

The CLI has no external API surface (no HTTP endpoints, no published library interface, no command schema changes). Contracts are N/A for this bugfix.
