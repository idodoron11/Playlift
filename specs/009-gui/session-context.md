# Session Context: Playlift GUI Planning

> Load this file into a new session to continue where we left off.
> The full plan is at `specs/009-gui/plan.md`.

---

## What was discussed

### 1. Project exploration

**Playlift** (`v0.2.11`) is a CLI tool that syncs music between local `.m3u` libraries, Spotify, and Deezer using fuzzy + ISRC track matching. Key facts:

- **Entry points**: `playlift` (`src/main.py`) and `playlift-batch` (`src/sync_exported_playlists.py`)
- **Commands**: `spotify` and `deezer` groups, each with: `import`, `sync`, `match`, `compare`, `duplicates`
- **Stack**: Python ≥ 3.11, `spotipy`, `deezer-py`, `click`, `music-tag`, `tqdm`, `tabulate`; linting via `ruff`, type-checking via `mypy` (strict), tests via `pytest`, managed with `uv`
- **Config**: `~/.playlift/config.ini` (Spotify OAuth + Deezer ARL cookie)
- **Match persistence**: Matched Spotify/Deezer refs stored in `TXXX:SPOTIFY` / `TXXX:DEEZER` ID3 tags; `"SKIP"` = ignore permanently

**Layered architecture**:
```
CLI (main.py)
  ↓
Playlists layer  — LocalPlaylist, SpotifyPlaylist, DeezerPlaylist, compare logic
  ↓              ↓
  |         Matchers — SpotifyMatcher, DeezerMatcher (fuzzy + ISRC)
  ↓              ↓
Tracks layer  — LocalTrack (ID3/FLAC), SpotifyTrack, DeezerTrack
  ↓
API layer  — spotify.py, deezer.py (singleton clients)
  ↓
Config — ~/.playlift/config.ini
```

**Key abstractions**:
- `Track` (abstract) → `ServiceTrack` (adds `permalink`/`service_name`) + `EmbeddableTrack` (write refs to tags)
- `TrackCollection` / `SyncTarget` / `Playlist` (abstract playlist contracts)
- `PlaylistFactory` — resolves a source string (local path, Spotify URI, Deezer URL) to the right playlist type
- `Matcher` (abstract) — `SpotifyMatcher` and `DeezerMatcher`; currently does I/O (tqdm, print, click prompts) mid-iteration — this is the problem we're fixing

---

### 2. GUI request

The user wants to add a **native desktop GUI** (cross-platform: Windows, macOS, Linux) that is **modern, beautiful, and easy to use**.

**Decisions made:**
- **Framework**: PySide6 (Qt6, LGPL)
- **Commands to expose**: import, sync, match, compare — both Spotify and Deezer (no `duplicates`)
- **Long operations**: Show progress bars + live stats (✅ matched / ❓ needs review / ❌ unmatched / ⏭ skipped). No log panel.
- **User decisions (ambiguous matches)**: Collect all ambiguous tracks during matching, then present them **all at once** in a review panel after matching completes — no mid-operation pop-ups.

---

### 3. Core architectural change agreed upon

**Current problem**: `Matcher.match_list()` interleaves I/O (progress bars, print statements, `click.prompt()` for user decisions) with the matching loop. This is messy for both CLI and GUI.

**Agreed solution: Two-phase matching**

**Phase 1 — Auto-match (pure, no I/O)**
`Matcher.build_match_batch(tracks, progress_callback=None) -> MatchBatch`

Classifies each track into one of four buckets:
- `matched` — auto-resolved
- `needs_review` — multiple candidates; human must choose
- `unmatched` — zero candidates
- `skipped` — SKIP sentinel

**Phase 2 — Resolve decisions (caller's job)**
`MatchBatch.resolve(decisions: dict[int, int])` / `MatchBatch.resolve_autopilot()`

**Phase 3 — Apply (caller's job)**
Embed refs into tags, call `add_tracks`.

This applies to **both CLI and GUI**. The matcher never does I/O again.

---

## Current plan (full detail at `specs/009-gui/plan.md`)

### Files to create (new)

| File | Purpose |
|------|---------|
| `src/matchers/match_batch.py` | `MatchBatch` dataclass |
| `src/cli_resolver.py` | CLI-side decision prompt + tqdm progress |
| `src/playlift_gui.py` | GUI entry point shim |
| `src/gui/__init__.py` | Package marker |
| `src/gui/app.py` | QApplication bootstrap |
| `src/gui/main_window.py` | QMainWindow: sidebar + stacked pages |
| `src/gui/theme.py` | Global QSS stylesheet (accent `#1DB954`) |
| `src/gui/pages/__init__.py` | Package marker |
| `src/gui/pages/base_page.py` | Shared form + progress + review panel orchestration |
| `src/gui/pages/import_page.py` | Import command page |
| `src/gui/pages/sync_page.py` | Sync command page |
| `src/gui/pages/match_page.py` | Match command page |
| `src/gui/pages/compare_page.py` | Compare command page |
| `src/gui/widgets/__init__.py` | Package marker |
| `src/gui/widgets/progress_widget.py` | Progress bar + ✅/❓/❌/⏭ counters |
| `src/gui/widgets/review_panel.py` | All-at-once review UI for ambiguous matches |
| `src/gui/workers/__init__.py` | Package marker |
| `src/gui/workers/match_worker.py` | QThread: runs `build_match_batch`, emits progress |
| `src/gui/workers/sync_worker.py` | QThread: applies decisions, embeds, syncs |

### Files to modify (existing)

| File | Change |
|------|--------|
| `src/matchers/__init__.py` | Add abstract `build_match_batch`; remove `choose_suggestion`, `match_list`, `click`/`tabulate` imports |
| `src/matchers/spotify_matcher.py` | Implement `build_match_batch`; `prefetch_isrc` becomes public; remove all I/O |
| `src/matchers/deezer_matcher.py` | Same as above |
| `src/playlists/__init__.py` | `SyncTarget.import_tracks` takes `Iterable[ServiceTrack]` (no autopilot/embed params) |
| `src/playlists/spotify_playlist.py` | `import_tracks` just calls `add_tracks`; remove `create_from_another_playlist` |
| `src/playlists/deezer_playlist.py` | Same; `sync_tracks` takes resolved tracks |
| `src/main.py` | Each command orchestrates `build_match_batch → resolve → embed → add_tracks` |
| `pyproject.toml` | Add `pyside6>=6.7`; add `playlift-gui` script entry point |

---

## Todo list (all pending)

| # | ID | Title |
|---|----|-------|
| 1 | `match-batch` | New MatchBatch dataclass |
| 2 | `matcher-refactor` | Refactor Matcher base + both concrete matchers |
| 3 | `cli-resolver` | New cli_resolver.py + update main.py |
| 4 | `playlist-simplify` | Simplify import_tracks/sync_tracks in both playlist classes |
| 5 | `deps-and-entry` | Add PySide6 to pyproject.toml + playlift-gui entry point |
| 6 | `gui-scaffold` | Create gui/__init__.py, app.py, theme.py |
| 7 | `gui-workers` | MatchWorker and SyncWorker QThreads |
| 8 | `gui-widgets` | ProgressWidget + ReviewPanel |
| 9 | `gui-pages` | base_page + 4 operation pages |
| 10 | `gui-main-window` | MainWindow: sidebar + page routing |
| 11 | `gui-entry` | playlift_gui.py entry point shim |
| 12 | `verify` | ruff, mypy, pytest; smoke test CLI + GUI |

### Dependencies between todos

```
match-batch
  └─ matcher-refactor
       ├─ cli-resolver
       └─ playlist-simplify
            └─ gui-pages

match-batch ──┐
deps-and-entry─┤
               └─ gui-scaffold
                    ├─ gui-workers (also needs matcher-refactor)
                    └─ gui-widgets
                         └─ gui-pages (also needs gui-workers, playlist-simplify)
                              └─ gui-main-window
                                   └─ gui-entry
                                        └─ verify (also needs cli-resolver)
```

---

## UI design sketch

```
┌─────────────────────────────────────────────────────┐
│  Playlift                                [─][□][✕]  │
├──────────────┬──────────────────────────────────────┤
│  ● Spotify   │  [Import]                            │
│  ○ Deezer    │  Source _____________________ [📂]  │
│              │  Destination _____________________   │
│  ──────────  │  ☐ Autopilot  ☐ Embed matches       │
│  Import      │  ☐ Public     ☐ Sort tracks          │
│  Sync        │                                      │
│  Match       │  [  Match tracks  ]                  │
│  Compare     │                                      │
│              │  ── Matching 68/100 ──               │
│              │  [===============  ]                 │
│              │  ✅ 65  ❓ 3  ❌ 0  ⏭ 0              │
│              │                                      │
│              │  3 tracks need your review           │
│              │  [  Review & Sync  ]                 │
└──────────────┴──────────────────────────────────────┘
```

Review panel (inline, after matching):
- One card per ambiguous track: source info left, candidate table right
- "Skip" button per track; keyboard-navigable
- "X of Y reviewed" counter → "Confirm & Sync" unlocks when all reviewed

---

## How to continue in a new session

1. Load this file and `specs/009-gui/plan.md` as context
2. Start with todo `match-batch` (no dependencies) — create `src/matchers/match_batch.py`
3. Then `matcher-refactor` — refactor `src/matchers/__init__.py`, `spotify_matcher.py`, `deezer_matcher.py`
4. Then `cli-resolver` and `playlist-simplify` can proceed in parallel
5. Then the GUI todos in order (5 → 6 → 7 → 8 → 9 → 10 → 11 → 12)

Run the test suite baseline before making changes:
```bash
uv run pytest tests/ -m "not integration"
uv run mypy .
uv run ruff check .
```
