# Tasks: Deezer Integration via ARL

**Input**: Design documents from `/specs/007-deezer-integration/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/cli.md ✅, quickstart.md ✅

**Tests**: Included per Constitution Principle V — every concrete class has unit tests covering core logic, edge cases, and error paths.  
**Organization**: Tasks grouped by user story to enable independent implementation, testing, and delivery of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on an in-progress task in the same phase)
- **[Story]**: User story label ([US1]–[US8])
- Exact file paths are included in every task description

---

## Phase 1: Setup

**Purpose**: Add the new dependency and scaffold configuration — no user-facing behaviour yet.

- [ ] T001 Add `deezer-py==1.3.7` to `pyproject.toml` dependencies and run `uv sync`
- [ ] T002 [P] Add `[DEEZER]\nARL=` section to `src/config/config_template.ini`
- [ ] T003 [P] Add `deezer_arl: str` property (reads `[DEEZER] ARL`) to `Config` in `src/config/__init__.py`
- [ ] T032 [P] Move `_match_constraints(source: Track, suggestion: Track) -> bool` static method from `SpotifyMatcher` to `Matcher` base class in `src/matchers/__init__.py`; update `src/matchers/spotify_matcher.py` to remove the local definition and update all internal references to `Matcher._match_constraints()`; confirm existing `SpotifyMatcher` tests still pass
- [ ] T033 [P] Define `CompareResult` dataclass (`source_only: list[Track]`, `target_only: list[Track]`) in `src/playlists/__init__.py`; refactor `compare_playlists()` in `src/playlists/compare.py` to return `CompareResult` instead of the bare tuple; confirm existing `tests/playlists/test_compare.py` still passes

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: `DeezerAuthenticationError`, `get_deezer_client()` singleton, and `DeezerTrack` entity. All user stories depend on these two modules.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Implement `DeezerAuthenticationError` and `get_deezer_client()` `@functools.cache` singleton — raises `DeezerAuthenticationError` when `login_via_arl()` returns `False`; ARL value never appears in error message — in `src/api/deezer.py`
- [ ] T031 [P] Write unit tests for `get_deezer_client()`: returns same instance on repeated calls (singleton); raises `DeezerAuthenticationError` when `login_via_arl()` returns `False`; error message does not contain the ARL value — in `tests/api/test_deezer.py`
- [ ] T005 [P] Implement `DeezerTrack(ServiceTrack)` — `service_name = "DEEZER"` class constant; `_track_id` (digit-string); all properties from GW dict (all-caps keys: `SNG_ID`, `SNG_TITLE`, `ART_NAME`, `ALB_TITLE`, `DURATION`, `ISRC`, `TRACK_NUMBER`) and public API dict (lowercase keys: `id`, `title`, `artist.name`, `album.title`, `duration`, `isrc`, `track_position`); `permalink` property returning `https://www.deezer.com/track/{_track_id}`; ISRC normalised to uppercase with hyphens stripped — in `src/tracks/deezer_track.py`
- [ ] T006 [P] Write unit tests for `DeezerTrack` covering: GW data shape, API data shape, all property values, `permalink` canonical form, ISRC normalisation, `track_number` defaults to `0` when absent, raises on empty/non-digit `_track_id` — in `tests/tracks/test_deezer_track.py`

**Checkpoint**: `DeezerAuthenticationError`, `get_deezer_client()`, and `DeezerTrack` are implemented and all tests passing.

---

## Phase 3: User Story 6 — Honor cached TXXX:DEEZER tag (Priority: P1)

**Goal**: Any matching operation reads an existing `TXXX:DEEZER` tag first and uses the cached URL directly — skipping all network lookups. `"SKIP"` silently excludes the track.

**Independent Test**: Pre-set `TXXX:DEEZER` on local test files; run any matching operation; assert no Deezer search or ISRC API call is made.

- [ ] T007 [P] [US6] Write unit tests for `DeezerMatcher` steps 1–2: canonical URL used directly without any network call; URL variants (no-`www.`, locale prefix, query string) normalised to canonical and used; `"SKIP"` raises `SkipTrackError`; malformed value falls through to next step — in `tests/matchers/test_deezer_matcher.py`
- [ ] T008 [US6] Implement `DeezerMatcher(Matcher)` skeleton: module-level `DEEZER_TRACK_URL_PATTERN` regex (`^https://(www\.)?deezer\.com(/[a-z]{2}(-[a-z]{2})?)?/track/(\d+)(\?.*)?$`); `_is_valid_deezer_url(url: str) -> bool`; `_normalise_deezer_url(url: str) -> str` (extracts numeric ID → returns `https://www.deezer.com/track/<id>`); `get_instance()` classmethod singleton calling `get_deezer_client()`; `_match_by_cached_ref(track)` (steps 1+2); `match(track)` four-step dispatcher — in `src/matchers/deezer_matcher.py`

**Checkpoint**: US6 independently testable — cached-ref and SKIP resolution paths verified by tests.

---

## Phase 4: User Story 7 — ISRC lookup (Priority: P1)

**Goal**: When there is no valid cached tag and the local file carries an ISRC, query `dz.api.get_track_by_ISRC()` for an exact catalog match. Transient network errors warn-and-continue.

**Independent Test**: Provide a local track with a known ISRC and no `TXXX:DEEZER` tag; verify `DeezerMatcher.match()` returns the correct `DeezerTrack` without invoking fuzzy search.

- [ ] T009 [P] [US7] Write unit tests for `DeezerMatcher._match_by_isrc()`: ISRC present and found in catalog returns `DeezerTrack`; ISRC present but not found returns `None`; no ISRC on local track skips lookup; network/API error logs `logging.warning()` and returns `None` — in `tests/matchers/test_deezer_matcher.py`
- [ ] T010 [US7] Implement `_match_by_isrc(track)` (step 3) calling `dz.api.get_track_by_ISRC(track.isrc)`, wrapping exceptions with `logging.warning()` and `return None`, wired into the `match()` dispatcher — in `src/matchers/deezer_matcher.py`

**Checkpoint**: US7 independently testable — ISRC resolution path verified by tests.

---

## Phase 5: User Story 1 — Import a local playlist to Deezer (Priority: P1) 🎯 MVP

**Goal**: `deezer import` creates a new Deezer playlist from a local `.m3u` file, resolves each track via the four-step matcher (steps 1–3 operational at this point), adds matched tracks, and optionally embeds `TXXX:DEEZER` tags.

**Independent Test**: Run `deezer import --source <small.m3u> --destination "Test"` with a real ARL; verify a new Deezer playlist is created containing the expected tracks.

- [ ] T011 [P] [US1] Write unit tests for `DeezerPlaylist`: `create()` classmethod creates playlist and returns instance; `tracks` property lazy-loads via `dz.gw.get_playlist_tracks()` and caches; `add_tracks()` calls `dz.gw.add_songs_to_playlist()` and invalidates `_tracks` cache; `import_tracks()` resolves via `track_matcher()` and delegates to `add_tracks()`; `create_from_another_playlist()` creates a new playlist and populates it from a `LocalPlaylist` in one call; `track_matcher()` returns `DeezerMatcher` instance — in `tests/playlists/test_deezer_playlist.py`
- [ ] T012 [US1] Implement `DeezerPlaylist(Playlist, SyncTarget)` — `create(name, public, *, deezer)` classmethod; lazy `tracks` property; `add_tracks(tracks)`; `import_tracks(tracks, autopilot, embed_matches)`; `create_from_another_playlist(name, source, public, *, deezer, autopilot, embed_matches)` facade (calls `create()` then `import_tracks()`; called by CLI); `track_matcher()` static method returning `DeezerMatcher.get_instance()` — in `src/playlists/deezer_playlist.py`
- [ ] T013 [US1] Add `deezer` Click group to `src/main.py` and implement `deezer import` subcommand with `--source` (multiple, required), `--destination` (multiple, required), `--autopilot`, `--embed-matches`, `--public`, `--from-path`/`--to-path`; always calls `DeezerPlaylist.create_from_another_playlist()` — never modifies existing playlist (FR-019); exit codes per `contracts/cli.md`

**Checkpoint**: MVP complete — `deezer import` is end-to-end functional for tracks resolvable via cached ref or ISRC.

---

## Phase 6: User Story 8 — Fuzzy search fallback (Priority: P2)

**Goal**: When ISRC lookup yields no result, `DeezerMatcher` falls back to `dz.gw.search()` with `_match_constraints()` filtering. Non-Latin (Cyrillic/CJK) queries forwarded as-is; misses log a warning.

**Independent Test**: Provide a local track with no ISRC and no cached `TXXX:DEEZER` tag; verify a `dz.gw.search()` call is issued and the candidate is presented for confirmation (or auto-accepted under `--autopilot`).

- [ ] T014 [P] [US8] Write unit tests for `_match_by_fuzzy_search()`: result above threshold + `--autopilot` auto-accepts; result below threshold without `--autopilot` prompts user; no results logs `logging.warning()` and returns `None`; non-Latin artist/title query string forwarded unchanged to `dz.gw.search()`; network error logs warning and returns `None` — in `tests/matchers/test_deezer_matcher.py`
- [ ] T015 [US8] Implement `_match_by_fuzzy_search(track)` (step 4) calling `dz.gw.search(f"{artist} {title}")`; apply inherited `Matcher._match_constraints()` (defined in base class per T032); wrap exceptions with `logging.warning()` and `return None` — in `src/matchers/deezer_matcher.py`
- [ ] T016 [US8] Implement `_match_constraints(source, suggestion)` static method, `suggest_match(track) -> list[DeezerTrack]`, and `match_list(tracks, autopilot, embed_matches)` with `tqdm` progress bar — in `src/matchers/deezer_matcher.py`

**Checkpoint**: Full four-step resolution in `DeezerMatcher` is operational; `deezer import` now handles all resolution paths.

---

## Phase 7: User Story 2 — Sync local playlist to existing Deezer playlist (Priority: P2)

**Goal**: `deezer sync` adds tracks missing from Deezer, removes tracks absent from the local `.m3u`, and optionally reorders the Deezer playlist to match local `.m3u` order.

**Independent Test**: Modify a `.m3u` after a prior import; run `deezer sync`; verify the Deezer playlist reflects the additions and removals.

- [ ] T017 [P] [US2] Write unit tests for `DeezerPlaylist` sync operations: `remove_track()` calls `dz.gw.remove_songs_from_playlist()` and invalidates `_tracks` cache; `sync_tracks()` adds missing and removes extra tracks; `sync_tracks()` on an already-up-to-date playlist makes zero add/remove calls and exits with success (SC-005); sort-tracks reorders Deezer playlist to local order — in `tests/playlists/test_deezer_playlist.py`
- [ ] T018 [US2] Implement `DeezerPlaylist.remove_track(tracks)` (calls `dz.gw.remove_songs_from_playlist()`, invalidates cache), sort-tracks logic, and `sync_tracks(local_tracks, autopilot, embed_matches, sort_tracks)` orchestration method — in `src/playlists/deezer_playlist.py`
- [ ] T019 [US2] Implement `deezer sync` subcommand in `src/main.py` with `--source` (required), `--destination` (required), `--autopilot`, `--embed-matches`, `--sort-tracks`, `--from-path`/`--to-path` flags

**Checkpoint**: `deezer import` and `deezer sync` both functional.

---

## Phase 8: User Story 3 — Pre-populate TXXX:DEEZER tags (Priority: P2)

**Goal**: `deezer match` resolves each track and always writes `TXXX:DEEZER` — embedding is unconditional (no `--embed-matches` flag). It never creates or modifies any Deezer playlist.

**Independent Test**: Run `deezer match --source <playlist.m3u>`; verify `TXXX:DEEZER` tags are written and no Deezer playlist is created or modified.

- [ ] T020 [P] [US3] Write unit tests for `deezer match` CLI behaviour: existing valid tag is preserved with no re-lookup; resolved track always writes tag regardless of flag; unresolvable track logs warning and writes no tag — in `tests/matchers/test_deezer_matcher.py`
- [ ] T021 [US3] Implement `deezer match` subcommand in `src/main.py` with `--source` (multiple, required), `--autopilot`, `--from-path`/`--to-path`; embedding unconditional (FR-005); no playlist operations

**Checkpoint**: `deezer match` functional and independently testable.

---

## Phase 9: User Story 4 — Compare local playlist against Deezer playlist (Priority: P3)

**Goal**: `deezer compare` prints a human-readable diff between a local `.m3u` (identified by `TXXX:DEEZER` values) and a live Deezer playlist.

**Independent Test**: Add a track to the Deezer playlist that is absent from the local `.m3u`; verify it appears under "Only in Deezer playlist" in compare output.

- [ ] T022 [P] [US4] Write unit tests for `compare_deezer_playlists()`: tracks only in local listed correctly; tracks only in Deezer listed correctly; identical playlists return no differences; return type is `CompareResult` (defined in T033) — in `tests/playlists/test_deezer_compare.py`
- [ ] T023 [US4] Implement `compare_deezer_playlists(left: TrackCollection, right: TrackCollection) -> CompareResult` using `TXXX:DEEZER` permalink as the identity key (mirrors `compare.py` pattern for Spotify) — in `src/playlists/deezer_compare.py`
- [ ] T024 [US4] Implement `deezer compare` subcommand in `src/main.py` with `--source` (required), `--destination` (required), `--from-path`/`--to-path`; print diff in format specified in `contracts/cli.md`

**Checkpoint**: `deezer compare` functional and independently testable.

---

## Phase 10: User Story 5 — Detect duplicate TXXX:DEEZER tags (Priority: P3)

**Goal**: `deezer duplicates` reports all tracks in a local `.m3u` that share the same `TXXX:DEEZER` value.

**Independent Test**: Create a `.m3u` with two entries sharing the same `TXXX:DEEZER` value; verify both are reported as duplicates.

- [ ] T025 [P] [US5] Write unit tests for `deezer duplicates`: two tracks sharing the same `TXXX:DEEZER` value appear in a duplicate group; playlist with no duplicates produces clean output — in `tests/playlists/test_deezer_duplicates.py`
- [ ] T026 [US5] Implement `deezer duplicates` subcommand in `src/main.py` with `--source` (required); group tracks by `TXXX:DEEZER` value; print duplicate groups in format specified in `contracts/cli.md`

**Checkpoint**: All five `deezer` subcommands reachable and functional (SC-004).

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Quality gates — ruff, mypy, pytest, manual quickstart validation.

- [ ] T027 [P] Run `uv run ruff format .` and `uv run ruff check .`; fix all lint and formatting issues across all new and modified files
- [ ] T028 [P] Run `uv run mypy .` in strict mode; fix all type errors; add `# type: ignore[no-untyped-call]` where `deezer-py` lacks type stubs (consistent with existing `spotipy` pattern in the codebase)
- [ ] T029 Run `uv run pytest tests/` and confirm all 30+ new tests pass with zero failures or skips
- [ ] T030 [P] Validate `quickstart.md` setup steps manually: config section readable, all five `deezer --help` outputs reachable without a valid ARL (SC-004), ARL never appears in any log or error output (FR-018)

---

## Dependencies & Execution Order

### Phase Dependencies

| Phase | Depends On | Notes |
|-------|-----------|-------|
| Phase 1 (Setup) | — | Start immediately |
| Phase 2 (Foundational) | Phase 1 | **Blocks all user stories** |
| Phase 3 (US6) | Phase 1 (T032), Phase 2 | `DeezerTrack` and `Matcher._match_constraints()` required |
| Phase 4 (US7) | Phase 3 | `DeezerMatcher` skeleton required |
| Phase 5 (US1) | Phase 4 | Full P1 matcher + new `DeezerPlaylist` |
| Phase 6 (US8) | Phase 4 | Extends `DeezerMatcher` (step 4) |
| Phase 7 (US2) | Phase 5, Phase 6 | `DeezerPlaylist` required; fuzzy recommended |
| Phase 8 (US3) | Phase 6 | Full four-step matcher required |
| Phase 9 (US4) | Phase 1 (T033), Phase 5 | `CompareResult` definition and `DeezerPlaylist.tracks` required |
| Phase 10 (US5) | Phase 2 | Reads `TXXX:DEEZER` only; no matcher needed |
| Phase 11 (Polish) | All desired stories | Final quality gate |

### User Story Dependencies

| Story | Depends On |
|-------|-----------|
| US6 — cached ref | Foundational (DeezerTrack) |
| US7 — ISRC lookup | US6 (DeezerMatcher skeleton) |
| US1 — import | US6, US7 (P1 matcher complete) |
| US8 — fuzzy search | US7 (extends DeezerMatcher) |
| US2 — sync | US1 (DeezerPlaylist), US8 (full matcher) |
| US3 — match cmd | US8 (full four-step matcher) |
| US4 — compare | US1 (DeezerPlaylist.tracks) |
| US5 — duplicates | Foundational only (no matcher needed) |

### Parallel Opportunities

- **Phase 2**: T005 (`DeezerTrack` impl) and T006 (its tests) after T004 completes
- **Phase 3**: T007 (tests) + T008 (impl) — TDD pair; write tests first, then implement
- **Phase 5**: T011 (tests) + T012 (impl) — TDD pair; T013 (CLI) after T012
- **Phases 3–5 vs. Phase 10**: US5 (duplicates) depends only on Foundational — can be developed in parallel with any Phase 3–9 work by a second contributor
- **All [P]-marked tasks**: Safe to run in parallel within their phase

---

## Parallel Example: MVP (US6 → US7 → US1)

```bash
# Phase 2 completes (T004–T006)

# Phase 3 (US6) — TDD pair:
# Contributor A writes tests (T007), then implements (T008)

# Phase 4 (US7) — after Phase 3 checkpoint:
# Contributor A writes tests (T009), then implements (T010)

# Phase 5 (US1) — after Phase 4 checkpoint:
# Contributor A: DeezerPlaylist tests + impl (T011, T012)
# Contributor B: deezer import CLI (T013) — once T012 is merged
```

---

## Implementation Strategy

**MVP scope** (deliver first): Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5  
Produces a working `deezer import` for tracks resolvable by cached ref or ISRC — highest-accuracy, lowest-risk path.

**Incremental delivery order**:
1. **MVP**: `deezer import` with cached ref + ISRC resolution (Phases 1–5)
2. **Full matching**: fuzzy search added (Phase 6) → enables `deezer match` (Phase 8)
3. **Sync**: `deezer sync` (Phase 7)
4. **Utilities**: `deezer compare` (Phase 9) + `deezer duplicates` (Phase 10)
5. **Polish**: quality gates (Phase 11)
