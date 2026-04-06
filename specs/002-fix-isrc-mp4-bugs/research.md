# Research: Fix Three M4A ISRC Tag Bugs

**Branch**: `002-fix-isrc-mp4-bugs` | **Date**: 2026-04-06

## Findings

### 1. mutagen MP4Tags — `bytes` vs. `[MP4FreeForm(...)]` during save

**Decision**: Write `[MP4FreeForm(value.encode("utf-8"))]` (list of MP4FreeForm) in `_set_custom_tag`.

**Rationale**: `MP4Tags.__setitem__` immediately calls `_render(key, value)` → `__render_freeform`. That function has a fallback `if isinstance(value, bytes): value = [value]`, which is why raw bytes work today. However, the correct API contract (per mutagen docs and source) is a `list[MP4FreeForm]`. Relying on the fallback is fragile — it uses the default `AtomDataType.UTF8` flag without the caller having any control. Using `MP4FreeForm` explicitly:
- Makes the data type intent clear (`AtomDataType.UTF8`)
- Matches the representation returned during a read (verified: `MP4FreeForm(b'...', <AtomDataType.UTF8: 1>)`)
- Is the pattern used by `music_tag.mp4` internally (`freeform_set` wraps in `[MP4FreeForm(...)]`)

**Alternatives considered**: Keep raw bytes. Rejected: fragile against library version changes and misrepresents the stored type when read back.

---

### 2. Case-insensitive fallback in `_get_custom_tag` — safety of `next()` over `tags.keys()`

**Decision**: Use `next((k for k in tags.keys() if k.lower() == tag_name.lower()), None)` as a fallback when the exact-case key is not found.

**Rationale**: `MP4Tags.keys()` (via `DictProxy`) returns a standard dict `KeysView`. Filtering with a generator and `next(..., None)` is safe and predictable. The expected number of freeform `----` atoms in a real music file is small (< 20 in the test file), so an O(n) scan is insignificant.

The prefix `"----:com.apple.iTunes:"` must be extracted to a module-level constant `_ITUNES_FREEFORM_PREFIX` to:
- Avoid repeating the literal across `_get_custom_tag`, `_set_custom_tag`, and the new fallback
- Satisfy Principle III (DRY) of the constitution

**Alternatives considered**: Lower-case all keys at load time. Rejected: would mutate the in-memory tag dict, changing the behavior of `save()` (keys are used verbatim when rendering atoms).

---

### 3. Importing `_normalize_isrc` from `tracks.local_track` into `matchers.spotify_matcher`

**Decision**: Import `_normalize_isrc` from `tracks.local_track` in `spotify_matcher.py`.

**Rationale**: The Matching layer already depends on the Track layer (imports `LocalTrack`, `SpotifyTrack`). `_normalize_isrc` is a pure, stateless string-transformation function with no side-effects. Placing it in `tracks.local_track` is correct — it is a track-level domain utility. Cross-module import within the correct dependency direction does not violate SOLID or the layered architecture.

**Alternatives considered**: Duplicate the normalization logic in `spotify_matcher.py`. Rejected: violates DRY; two copies of the same normalization would diverge.

---

### 4. `_set_custom_tag` — value must be a list, not a bare `MP4FreeForm`

**Decision**: Assign `self._mutagen_file.tags[tag_name] = [MP4FreeForm(value.encode("utf-8"))]` (a list).

**Rationale**: `__render_freeform` iterates over `value` with `for v in value`. A bare `MP4FreeForm` is a `bytes` subclass; iterating over it would yield individual bytes, not the intended single-value list. The tag must be a `list[MP4FreeForm]` as per the mutagen contract. This also matches how the tag is stored on disk and returned during a read (always a list of one or more `MP4FreeForm` objects).

## Summary: No Unresolved Items

All four open questions are resolved. No NEEDS CLARIFICATION items remain. Proceed to Phase 1.
