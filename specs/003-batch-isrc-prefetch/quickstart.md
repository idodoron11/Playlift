# Quickstart: Batch ISRC Prefetch

**Feature**: `003-batch-isrc-prefetch`  
**Date**: 2026-04-07  
**Audience**: Developer implementing or reviewing this feature

---

## What Changes

One file changes: `matchers/spotify_matcher.py`.

The public interface of `SpotifyMatcher` is **unchanged** — no CLI flags, no new arguments,
no configuration changes. The optimisation is entirely internal.

---

## New Constant

Add at module scope (above the class definition):

```python
SPOTIFY_BATCH_SIZE: int = 50
```

---

## New Private Method — `_prefetch_isrc_data`

Add to `SpotifyMatcher`:

```python
def _prefetch_isrc_data(self, matches: list[SpotifyTrack]) -> None:
    """Batch-fetch full track data for SpotifyTrack objects that lack ISRC.

    Mutates _data in-place on each match so subsequent .isrc reads are
    served from memory. Called before the embed loop in match_list.
    Tracks whose _data already contains external_ids.isrc are skipped.
    """
    needs_fetch = [
        m for m in matches
        if not (m._data and m._data.get("external_ids", {}).get("isrc"))
    ]
    if not needs_fetch:
        return

    # De-duplicate: multiple SpotifyTrack objects may share the same ID
    id_to_tracks: dict[str, list[SpotifyTrack]] = {}
    for m in needs_fetch:
        id_to_tracks.setdefault(m.track_id, []).append(m)

    track_ids = list(id_to_tracks)
    for i in range(0, len(track_ids), SPOTIFY_BATCH_SIZE):
        batch = track_ids[i : i + SPOTIFY_BATCH_SIZE]
        try:
            response = SpotifyAPI.get_instance().tracks(batch)
        except Exception:
            logger.warning(
                "Batch ISRC prefetch failed for %d track(s); ISRC will not be embedded for this batch",
                len(batch),
            )
            continue

        for track_id, item in zip(batch, response.get("tracks", [])):
            if item is None:
                logger.debug(
                    "Batch ISRC prefetch: track %s not available on Spotify, skipping ISRC",
                    track_id,
                )
                continue
            for sp_track in id_to_tracks[track_id]:
                sp_track._data = item
```

---

## Changed Method — `match_list`

Restructure to separate the user review pass from the embed pass:

```python
def match_list(
    self,
    tracks: Iterable[Track],
    autopilot: bool = False,
    embed_matches: bool = False,
) -> list[Track]:
    suggestions_list = self._match_list(tracks)
    processed: list[list[SpotifyTrack]] = list(map(list, suggestions_list))
    sp_tracks: list[Track] = []
    pairs_to_embed: list[tuple[Track, SpotifyTrack]] = []

    print("Reviewing matches")
    for _index, (track, suggestions) in tqdm(
        list(enumerate(zip(tracks, processed, strict=True)))
    ):
        if not suggestions:
            continue
        choice = 0
        if len(suggestions) > 1 and not autopilot:
            choice = Matcher.choose_suggestion(track, suggestions)
        if choice >= 0:
            sp_tracks.append(suggestions[choice])
            if embed_matches:
                pairs_to_embed.append((track, suggestions[choice]))

    if pairs_to_embed:
        chosen_matches = [match for _, match in pairs_to_embed]
        self._prefetch_isrc_data(chosen_matches)
        for source_track, match in pairs_to_embed:
            self._update_spotify_match_in_source_track(source_track, match)

    return sp_tracks
```

---

## Test Coverage Required

Add to `tests/matchers/test_spotify_matcher.py`:

| Test name | Scenario |
|-----------|----------|
| `test_prefetch_isrc_data_fetches_tracks_missing_isrc` | Tracks with no `_data` → batch call made, `_data` updated |
| `test_prefetch_isrc_data_skips_tracks_with_isrc_in_data` | Tracks with `external_ids.isrc` already set → no API call |
| `test_prefetch_isrc_data_mixed_requires_and_skips` | Mix of loaded/unloaded → partial batch |
| `test_prefetch_isrc_data_handles_more_than_50_tracks` | 51 tracks → two batch calls |
| `test_prefetch_isrc_data_logs_warning_on_batch_failure` | Exception raised → WARNING logged, no crash |
| `test_prefetch_isrc_data_skips_null_items_with_debug_log` | `None` in response → DEBUG logged, other tracks updated |
| `test_match_list_does_not_call_prefetch_when_not_embedding` | `embed_matches=False` → `tracks()` never called |
| `test_match_list_embeds_all_tracks_after_prefetch` | `embed_matches=True` → all ISRCs written correctly |

---

## Verify

```bash
uv run ruff check .
uv run ruff format .
uv run mypy .
uv run pytest tests/
```
