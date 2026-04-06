# Quickstart: Fix Three M4A ISRC Tag Bugs

**Branch**: `002-fix-isrc-mp4-bugs` | **Date**: 2026-04-06

## Overview

Three targeted edits across two source files and one test file. Each bug is independent; they can be implemented and tested in any order though the recommended order is Bug 1 → Bug 2 → Bug 3.

---

## Bug 1 — Case-insensitive freeform key lookup (`tracks/local_track.py`)

**What to change**: `_get_custom_tag` currently does an exact-case dict lookup. Add a case-insensitive fallback for MP4 files.

**Step 1**: Extract the iTunes freeform prefix to a module-level constant:
```python
_ITUNES_FREEFORM_PREFIX = "----:com.apple.iTunes:"
```

**Step 2**: Replace `tag_name = f"----:com.apple.iTunes:{tag_name}"` with `tag_name = f"{_ITUNES_FREEFORM_PREFIX}{tag_name}"` in both `_get_custom_tag` and `_set_custom_tag`.

**Step 3**: In `_get_custom_tag`, after the `if tag_name not in self._mutagen_file.tags` check, add a fallback:
```python
if isinstance(self._mutagen_file, MP4) and tag_name not in self._mutagen_file.tags:
    tag_name = next(
        (k for k in self._mutagen_file.tags.keys() if k.lower() == tag_name.lower()),
        tag_name,  # keep original if still not found (will return None below)
    )
```

**Before/After**:
```python
# BEFORE
if tag_name not in self._mutagen_file.tags:
    return None

# AFTER (MP4 path only — fallback, then check again)
if isinstance(self._mutagen_file, MP4) and tag_name not in self._mutagen_file.tags:
    tag_name = next(
        (k for k in self._mutagen_file.tags.keys() if k.lower() == tag_name.lower()),
        tag_name,
    )
if self._mutagen_file.tags is None or tag_name not in self._mutagen_file.tags:
    return None
```

---

## Bug 2 — Correct `MP4FreeForm` write type (`tracks/local_track.py`)

**What to change**: In `_set_custom_tag`, the write for MP4 files must use `[MP4FreeForm(value.encode("utf-8"))]`, not `value.encode("utf-8")`.

**Add import**:
```python
from mutagen.mp4 import MP4, MP4FreeForm
```

**Before/After**:
```python
# BEFORE
self._mutagen_file.tags[tag_name] = value.encode("utf-8")

# AFTER
from mutagen.mp4 import MP4FreeForm  # already imported at top of file
self._mutagen_file.tags[tag_name] = [MP4FreeForm(value.encode("utf-8"))]
```

---

## Bug 3 — Normalize ISRC before comparison (`matchers/spotify_matcher.py`)

**What to change**: In `_update_spotify_match_in_source_track`, normalize `match.isrc` before comparing with `source_track.isrc` (which is already normalized by the getter).

**Add import**:
```python
from tracks.local_track import LocalTrack, _normalize_isrc
```

**Before/After**:
```python
# BEFORE
if match.isrc is not None and source_track.isrc != match.isrc:
    source_track.isrc = match.isrc

# AFTER
if match.isrc is not None and source_track.isrc != _normalize_isrc(match.isrc):
    source_track.isrc = match.isrc
```

---

## Regression Tests (`tests/tracks/test_local_track.py`)

Constitution requires failing tests written **before** the fix. Add to `TestLocalTrackIsrcGetterM4a`:

### Test 1 — ISRC getter reads lowercase-keyed atom (Bug 1 regression)
```python
def test_isrc_returns_value_from_lowercase_itunes_key(self) -> None:
    from mutagen.mp4 import MP4, MP4FreeForm
    mock_mp4 = MagicMock(spec=MP4)
    mock_mp4.__class__ = MP4
    # Key is lowercase, as written by Apple Music / some encoders
    tags_dict = {"----:com.apple.iTunes:isrc": [MP4FreeForm(b"USSM19604431")]}
    mock_mp4.tags = tags_dict
    mock_mp4.__getitem__ = Mock(side_effect=lambda key: tags_dict[key])
    mock_mp4.__contains__ = Mock(side_effect=lambda key: key in tags_dict)
    track = self._make_local_track(mock_mp4)
    assert track.isrc == "USSM19604431"  # Must not return None
```

### Test 2 — ISRC setter does not write when lowercase key already exists (Bug 1 regression)
```python
def test_isrc_setter_skips_write_when_lowercase_key_exists(self) -> None:
    from mutagen.mp4 import MP4, MP4FreeForm
    mock_mp4 = MagicMock(spec=MP4)
    mock_mp4.__class__ = MP4
    tags_dict = {"----:com.apple.iTunes:isrc": [MP4FreeForm(b"USSM19604431")]}
    mock_mp4.tags = tags_dict
    mock_mp4.__getitem__ = Mock(side_effect=lambda key: tags_dict[key])
    mock_mp4.__contains__ = Mock(side_effect=lambda key: key in tags_dict)
    track = self._make_local_track(mock_mp4)
    track.isrc = "USSM19604431"  # Must not write a new atom
    mock_mp4.save.assert_not_called()
```

### Test 3 — `_set_custom_tag` writes `MP4FreeForm` not raw bytes (Bug 2 regression)
Add to `TestLocalTrackIsrcSetterM4a`:
```python
def test_isrc_setter_writes_mp4freeform_not_raw_bytes(self) -> None:
    from mutagen.mp4 import MP4, MP4FreeForm
    mock_mp4 = MagicMock(spec=MP4)
    mock_mp4.__class__ = MP4
    written: dict = {}
    mock_mp4.tags = MagicMock()
    mock_mp4.tags.__contains__ = Mock(return_value=False)
    mock_mp4.tags.__setitem__ = Mock(side_effect=lambda k, v: written.update({k: v}))
    mock_audio = MagicMock()
    track = self._make_local_track(mock_mp4, audio_file=mock_audio)
    with self._isrc_setter_patch():
        track.isrc = "USSM19604431"
    value = written.get("----:com.apple.iTunes:ISRC")
    assert isinstance(value, list)
    assert all(isinstance(v, MP4FreeForm) for v in value)
```

### Test 4 — Normalized ISRC comparison skips write (Bug 3 regression)
Add a unit test to `tests/matchers/test_spotify_matcher.py` (or inline in `test_local_track.py`):
```python
# In _update_spotify_match_in_source_track: hyphenated Spotify ISRC must not
# trigger a write when the local ISRC is the same value without hyphens.
```
This is covered by asserting that `source_track.isrc` setter is never invoked when local isrc == normalized(match.isrc).

---

## Verification

```bash
uv run pytest tests/tracks/test_local_track.py -v
uv run ruff check .
uv run ruff format .
uv run mypy .
uv run pytest tests/
```
