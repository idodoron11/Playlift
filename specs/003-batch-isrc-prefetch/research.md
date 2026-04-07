# Research: Batch ISRC Prefetch in match_list

**Feature**: `003-batch-isrc-prefetch`  
**Date**: 2026-04-07  
**Status**: Complete — no NEEDS CLARIFICATION remaining

---

## Research 1: spotipy `tracks()` API contract

**Decision**: Use `SpotifyAPI.get_instance().tracks(track_ids)` where `track_ids` is a
`list[str]` of Spotify track IDs (not full URLs). Returns `{"tracks": [<track_object> | None, ...]}`.

**Rationale**: spotipy's `tracks()` method wraps the Spotify Web API `GET /tracks` endpoint.
It accepts up to 50 IDs per call and returns the full `TrackObject` — **the same schema** as
a single `GET /tracks/{id}` call. The official Spotify Web API reference explicitly documents
`external_ids.isrc` as a field on `TrackObject` (verified: developer.spotify.com/documentation/
web-api/reference/get-several-tracks and get-track). Items are returned in input order, with
`None` for any unknown/unavailable track IDs.

**Additional finding — search results**: The `GET /search` endpoint also returns full
`TrackObject` items for track search results (not `SimplifiedTrackObject`), so `external_ids.isrc`
is already present in `_data` for tracks matched via fuzzy search. The defensive skip guard
(`_data.get("external_ids", {}).get("isrc")`) still protects against any edge-case omission,
but the primary beneficiaries of the batch prefetch are tracks built from a cached `spotify_ref`
string where `_data` is `None`.

**Alternatives considered**:
- Calling `track(id)` per track individually — current behaviour, produces N API calls.
  Rejected: this is the problem being solved.
- Using the Spotify playlist endpoint to fetch all tracks at once — only applicable when
  loading a playlist from Spotify, not when embedding local-to-Spotify matches.

---

## Research 2: Skip condition for tracks already carrying ISRC data

**Decision**: A `SpotifyTrack` is excluded from the batch if and only if `_data is not None`
**and** `_data.get("external_ids", {}).get("isrc")` is a non-empty string.

**Rationale**: Tracks matched via the fuzzy search path are created with `data=track` from
the search response, and since `GET /search` returns full `TrackObject` items, `external_ids.isrc`
will typically already be present in `_data`. These tracks benefit from the skip guard at no
cost. Tracks constructed from a cached `spotify_ref` string (`SpotifyTrack(url)` with no `data`)
have `_data = None` and always require a fetch — this is the dominant case the batch prefetch
addresses. The defensive ISRC check (rather than checking `_data is not None` alone) protects
against any future scenario where `_data` is populated without `external_ids` (e.g., a partial
object injected in tests or a future code path change).

**Alternatives considered**:
- Check `_data is not None` only — sufficient for the current codebase but fragile against
  future changes. Rejected: the slightly more expensive check is worth the safety.
- Always fetch all tracks regardless of cached state — safe but wastes quota for search-matched
  tracks that already carry ISRC data. Rejected: unnecessary API calls.

---

## Research 3: Correlating batch response items to SpotifyTrack objects

**Decision**: Correlate by position: iterate `zip(batch_ids, response["tracks"])` so each
item aligns with its request ID. This is required when the response contains `None` items,
since a `None` carries no ID field of its own.

**Rationale**: The Spotify `/tracks` endpoint guarantees order preservation. spotipy does
not reorder items. Position-based correlation is the simplest and most reliable approach.

**Alternatives considered**:
- Correlate by `item["id"]` — works for non-null items, but fails for `None` values since
  they have no `id` field. Rejected: incomplete.

---

## Research 4: Handling duplicate track IDs in the chosen matches list

**Decision**: Build `id_to_tracks: dict[str, list[SpotifyTrack]]` mapping track ID →
list of `SpotifyTrack` instances that share that ID. On batch response, update `_data`
on all instances for a given ID.

**Rationale**: A playlist could theoretically contain the same Spotify track matched more
than once (e.g. two local files matched to the same release). Both `SpotifyTrack` objects
carry the same ID. De-duplicating the batch request avoids sending duplicate IDs to the
API (which spotipy/Spotify handles, but is wasteful).

**Alternatives considered**:
- Send duplicate IDs — Spotify handles it but wastes one of the 50-per-batch slots.
  Rejected: minor waste with no benefit.

---

## Research 5: Structuring `match_list` for a two-pass approach

**Decision**: Restructure `match_list` to a two-pass loop:
1. **Pass 1** (existing review loop): collect `(source_track, chosen_match)` pairs into
   `pairs_to_embed: list[tuple[Track, SpotifyTrack]]`.
2. **Prefetch** (new, gated on `embed_matches`): call `_prefetch_isrc_data` once on all
   chosen matches.
3. **Pass 2** (new, gated on `embed_matches`): embed chosen matches via
   `_update_spotify_match_in_source_track`.

**Rationale**: The current loop mixes user-interactive review (`Matcher.choose_suggestion`)
with embedding. Separating collection from embedding allows the batch prefetch to happen
after all user choices are made but before any file writes — a clean, linear flow that
preserves the interactive review experience unchanged.

**Alternatives considered**:
- Prefetch during `_match_list` before user review — too early; some suggestions will be
  rejected by the user. Wastes API calls for tracks whose suggestion is overridden.
  Rejected: over-fetches by potentially O(suggestions_per_track) factor.
- Inline prefetch inside `_update_spotify_match_in_source_track` with a lazy batch — adds
  hidden state and coupling. Rejected: violates single-responsibility and readability.

---

## Resolved Unknowns

| Unknown | Resolution |
|---------|------------|
| Does `tracks()` include ISRC in response? | Yes — `external_ids.isrc` present in full track objects |
| Max batch size | 50 IDs per call (Spotify Web API hard limit) |
| Response order preservation | Guaranteed — correlate by position |
| Skip condition for pre-loaded tracks | `_data is not None and _data.get("external_ids", {}).get("isrc")` is truthy |
| Handling duplicate IDs | De-duplicate via `id_to_tracks` dict |
| Restructuring `match_list` | Two-pass: collect → prefetch → embed |
