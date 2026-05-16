# Plan: Refactor Matching + Add Native Desktop GUI to Playlift

## Problem

Two concerns:

1. **Architectural**: The matcher currently does I/O (tqdm, print, click prompts) while
   iterating. User decisions should be deferred until after the full auto-matching pass.
2. **Feature**: Add a cross-platform native desktop GUI (PySide6) that is modern and easy
   to use.

---

## Core Architecture Change: Two-Phase Matching

### Principle: Matcher is pure — it only produces data

**Phase 1 — Auto-match (pure, no I/O)**
`Matcher.build_match_batch(tracks, progress_callback=None) -> MatchBatch`
Iterates all tracks and classifies each into one of four buckets:

- `matched` — auto-resolved (cached ref, ISRC hit, or single fuzzy result)
- `needs_review` — multiple fuzzy candidates; human must choose
- `unmatched` — zero candidates found
- `skipped` — SKIP sentinel in tags

**Phase 2 — Resolve decisions (caller's job)**
`MatchBatch.resolve(decisions: dict[int, int]) -> list[tuple[Track, ServiceTrack]]`
Merges `matched` + human decisions for `needs_review`. Returns source-match pairs.
`MatchBatch.resolve_autopilot()` — auto-picks first candidate for all `needs_review`.

**Phase 3 — Apply (caller's job)**
Caller embeds refs into tags (if requested) and adds tracks to the playlist.

This separation applies to **both CLI and GUI**.

---

## New `MatchBatch` Data Class (`src/matchers/match_batch.py`)

```python
@dataclass
class MatchBatch:
    matched:      list[tuple[Track, ServiceTrack]]
    needs_review: list[tuple[Track, list[ServiceTrack]]]  # (source, [candidates])
    unmatched:    list[Track]
    skipped:      list[Track]

    def resolve(self, decisions: dict[int, int]) -> list[tuple[Track, ServiceTrack]]:
        """Apply user decisions. decisions maps needs_review index → candidate idx (-1 = skip)."""

    def resolve_autopilot(self) -> list[tuple[Track, ServiceTrack]]:
        """Auto-pick first candidate for all needs_review."""
```

---

## Changes to Existing Code

### `src/matchers/__init__.py` (Matcher base)

- Add abstract `build_match_batch(tracks, progress_callback=None) -> MatchBatch`
- Remove `choose_suggestion` (CLI-only; moves to `src/cli_resolver.py`)
- Remove `match_list` abstract method
- Remove `click` and `tabulate` imports

### `src/matchers/spotify_matcher.py`

- Implement `build_match_batch()` — fills the four buckets, no tqdm/print
- Remove `_match_list` and `match_list` implementations
- ISRC prefetch becomes a public helper `prefetch_isrc(pairs)` called by the orchestrator
  before embedding

### `src/matchers/deezer_matcher.py`

- Same refactor: implement `build_match_batch()`, remove tqdm/print/choose_suggestion

### `src/playlists/spotify_playlist.py` and `deezer_playlist.py`

- `import_tracks` now receives **already-resolved** `Iterable[ServiceTrack]` — just calls
  `add_tracks`. No matching inside.
- `sync_tracks` (Deezer) same: receives resolved service tracks, does the add/remove diff.
- `create_from_another_playlist` removed (matching was its only job; caller orchestrates now).

### `src/playlists/__init__.py` (SyncTarget ABC)

- `import_tracks(tracks: Iterable[ServiceTrack]) -> None` — no autopilot/embed params

### `src/main.py` (CLI commands)

Each command orchestrates the full flow explicitly:

```python
batch = matcher.build_match_batch(tracks, progress_callback=tqdm_update)
pairs = resolve_decisions_cli(batch, autopilot)   # prompts if needed
if embed_matches:
    embed_pairs(pairs)
playlist.add_tracks([match for _, match in pairs])
```

`create_from_another_playlist` call sites replaced by this inline pattern.

### `src/cli_resolver.py` (NEW)

- `resolve_decisions_cli(batch, autopilot) -> list[tuple[Track, ServiceTrack]]`
- Contains the old `choose_suggestion` tabulate/click.prompt logic for `needs_review`
- Wraps the matching pass with `tqdm` progress display
- Prints unmatched/skipped summaries after the pass

---

## GUI

### Framework

**PySide6** (Qt6 Python bindings, LGPL, truly cross-platform Win/Mac/Linux).

### GUI-specific flow

1. **Matching phase**: `MatchWorker` (QThread) calls `build_match_batch()`, emits
   `progress(n, total)` after each track → live progress bar + running stats.
2. **Review phase** (non-autopilot only): after matching completes, a `ReviewPanel` shows
   all `needs_review` tracks at once. Each row has source track info + a candidate picker.
   "Skip" is available per track. A "Confirm & Sync" button unlocks when all are reviewed.
3. **Sync phase**: `SyncWorker` (QThread) applies decisions, embeds tags, calls
   `add_tracks`, emits progress + final stats.

No per-track pop-up dialogs. All decisions in one review screen.

### UI Layout

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

**Review panel** (appears inline after matching):

- Card per ambiguous track: source metadata on left, candidate table on right
- Keyboard-navigable; "Skip" button per track
- Progress indicator: "3 of 3 reviewed" → "Confirm & Sync" button unlocks

### New GUI files (`src/gui/`)

```
gui/__init__.py
gui/app.py                      — QApplication bootstrap
gui/main_window.py              — QMainWindow: sidebar + stacked pages
gui/theme.py                    — Global QSS (modern, accent #1DB954)
gui/pages/__init__.py
gui/pages/base_page.py          — Shared form: source, dest, flags, run button, progress
gui/pages/import_page.py
gui/pages/sync_page.py
gui/pages/match_page.py
gui/pages/compare_page.py
gui/widgets/__init__.py
gui/widgets/progress_widget.py  — progress bar + ✅/❓/❌/⏭ counters
gui/widgets/review_panel.py     — inline review: all needs_review at once
gui/workers/__init__.py
gui/workers/match_worker.py     — QThread: build_match_batch, emits progress
gui/workers/sync_worker.py      — QThread: embed + add_tracks, emits done/error
src/playlift_gui.py             — entry point shim
```

### `pyproject.toml`

- Add `pyside6>=6.7` to `[project.dependencies]`
- Add `playlift-gui = "playlift_gui:main"` to `[project.scripts]`

---

## Implementation Order

| # | Todo ID | Description |
|---|---------|-------------|
| 1 | `match-batch` | New `MatchBatch` dataclass |
| 2 | `matcher-refactor` | Refactor `Matcher` base + both concrete matchers (`build_match_batch`, remove I/O) |
| 3 | `cli-resolver` | New `cli_resolver.py`; update CLI commands in `main.py` to use two-phase flow |
| 4 | `playlist-simplify` | Simplify `import_tracks`/`sync_tracks`/`create_from_another_playlist` in both playlist classes |
| 5 | `deps-and-entry` | Add PySide6 to `pyproject.toml` + `playlift-gui` entry point |
| 6 | `gui-scaffold` | Create `gui/__init__.py`, `app.py`, `theme.py` |
| 7 | `gui-workers` | `match_worker.py` and `sync_worker.py` (QThreads) |
| 8 | `gui-widgets` | `progress_widget.py` + `review_panel.py` |
| 9 | `gui-pages` | `base_page.py` + 4 operation pages |
| 10 | `gui-main-window` | `MainWindow`: sidebar + page routing |
| 11 | `gui-entry` | `playlift_gui.py` entry point shim |
| 12 | `verify` | `ruff`, `mypy`, `pytest`; smoke test both CLI and GUI |
