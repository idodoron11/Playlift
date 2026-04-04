# Quickstart: ISRC-Based Track Matching and Embedding

**Date**: 2026-04-04 | **Feature**: 001-isrc-track-matching

## What This Feature Does

Adds ISRC (International Standard Recording Code) as a first-pass matching method for local-to-Spotify track matching. If a local audio file already has an ISRC in its tags, the system looks it up directly in Spotify's catalog instead of doing a fuzzy text search. After matching, it writes the Spotify track's ISRC back into the local file so future runs can skip fuzzy search.

## Files Changed

| File | Change |
|------|--------|
| `tracks/local_track.py` | Add `isrc` property (read/write) with format-specific tag handling |
| `tracks/spotify_track.py` | Add `isrc` property (read-only, from `external_ids`) |
| `matchers/spotify_matcher.py` | Add ISRC validation + ISRC-first lookup in `match()` flow; add ISRC embedding in `_update_spotify_match_in_source_track()` |
| `tests/tracks/track_mock.py` | Add optional `isrc` field |
| `tests/matchers/test_spotify_matcher.py` | Add tests for ISRC matching, fallback, validation, embedding |
| `tests/tracks/test_spotify_track.py` | Add test for ISRC property |

## How to Test

```bash
# Run all tests
uv run pytest tests/

# Run only matcher tests (most coverage for this feature)
uv run pytest tests/matchers/test_spotify_matcher.py -v

# Run quality gates
uv run ruff check .
uv run ruff format --check .
uv run mypy .
```

## Key Design Decisions

1. **No new classes**: ISRC support is added as properties on existing `LocalTrack` and `SpotifyTrack`, and logic additions to `SpotifyMatcher`. The feature fits within existing responsibilities.

2. **Format-specific ISRC tag handling**: MP3 uses the standard `TSRC` ID3 frame (not `TXXX:ISRC`); FLAC uses standard Vorbis `isrc` comment; M4A uses iTunes freeform tag. This ensures compatibility with other music software.

3. **Validation before lookup**: ISRC is normalized (uppercase, strip hyphens) and validated against `^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$` before any API call is made.

4. **Embedding gated by `--embed-matches`**: ISRC is written alongside `SPOTIFY_REF` when embedding is active. The `match` command always embeds.
