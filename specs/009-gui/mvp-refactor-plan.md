# Plan: MVP Refactor — Remove UI from Model Layers

## MVP Role Assignment

| Layer | Classes |
|-------|---------|
| **Model (M)** | `SpotifyMatcher`, `DeezerMatcher`, `LocalPlaylist`, `SpotifyPlaylist`, `DeezerPlaylist`, `LocalTrack`, `SpotifyTrack`, `DeezerTrack` — pure logic, zero UI |
| **View (V)** | `IMatchView` (ABC — abstract contract) + `CliMatchView(IMatchView)` (concrete CLI impl) |
| **Presenter (P)** | `resolve_matches()` helper function + CLI command functions in `main.py` |

### Why both `IMatchView` and `CliMatchView`?

`IMatchView` is the abstract contract the Presenter depends on. `CliMatchView` is the production CLI implementation. Tests inject `FakeMatchView(IMatchView)` — no tqdm, no stdin. Classic "program to an interface."

### Why `match_list()` stays in the Model

`match_list()` is the Matcher's core batch operation — business logic. What was wrong was it conflating **two** responsibilities:

1. **Batch matching logic** → Model
2. **User decision loop** → Presenter

The fix is to split them at that boundary via a structured return type (`MatchOutcome`), not to remove the method.

---

## Root Cause Analysis

| File | Lines | Violation | Root Cause |
|------|-------|-----------|------------|
| `src/matchers/__init__.py` | 58–67 | `choose_suggestion()` prints table + `click.prompt` | Model acting as Presenter |
| `src/matchers/spotify_matcher.py` | 150–176 | `print()` + `tqdm()` in `match_list()` | Model mixing UI into batch logic |
| `src/matchers/deezer_matcher.py` | 163–173 | `print()` + `tqdm()` in `match_list()` | Model mixing UI into batch logic |
| `src/playlists/local_playlist.py` | 22–30 | `print()` + `tqdm()` in `_load_tracks()` | Model mixing display into I/O |
| `src/tracks/local_track.py` | 133 | `print()` swallows save errors silently | Model using print instead of logging |

---

## New Data Structures (Model layer, in `src/matchers/`)

### `MatchStatus` enum

```python
class MatchStatus(Enum):
    MATCHED   = "matched"    # confident single match found
    AMBIGUOUS = "ambiguous"  # multiple candidates, user choice needed
    UNMATCHED = "unmatched"  # no candidates at all
    SKIPPED   = "skipped"    # track marked SKIP by user
```

### `MatchOutcome` dataclass

```python
@dataclass
class MatchOutcome:
    source_track: Track
    status: MatchStatus
    match: Track | None       # populated when status is MATCHED
    suggestions: list[Track]  # populated when status is AMBIGUOUS
```

Both live in `src/matchers/__init__.py` alongside the `Matcher` ABC.

---

## Steps

### Phase 1 — Track layer *(independent, minimal)*

1. `src/tracks/local_track.py` → `_set_custom_tag()`:
   - Replace `print(f"Could not save tags...")` with `logger.warning(...)`. Logger is already imported.

### Phase 2 — LocalPlaylist cleanup *(independent)*

2. `src/playlists/local_playlist.py` → `_load_tracks()`:
   - `print("Reading playlist tracks metadata")` → `logger.info("Reading playlist tracks metadata")`
   - Remove `tqdm(...)` wrapper — iterate plainly
   - `print(f"Error during file scan: {e}\nFile: {file_path}")` → `logger.warning("Error during file scan: %s\nFile: %s", e, file_path)`
   - Add `import logging` and `logger = logging.getLogger(__name__)`

### Phase 3 — Reshape `Matcher.match_list()` *(Model, core change)*

3. `src/matchers/__init__.py`:
   - Add `MatchStatus` enum and `MatchOutcome` dataclass
   - Change abstract `match_list()` signature:
     - **Old**: `match_list(tracks, autopilot, embed_matches) -> list[Track]`
     - **New**: `match_list(tracks: Iterable[Track]) -> Iterator[MatchOutcome]`
   - Remove `choose_suggestion()` static method
   - Remove `import click`

4. `src/matchers/spotify_matcher.py` — new `match_list()` implementation:
   - Iterates tracks, calls `self.match(track)` and `self.suggest_match(track)`
   - Yields one `MatchOutcome` per track:
     - Confident match → `MatchStatus.MATCHED`
     - Multiple suggestions → `MatchStatus.AMBIGUOUS`
     - No suggestions → `MatchStatus.UNMATCHED`
     - `SkipTrackError` → `MatchStatus.SKIPPED`
   - No `print()`, no `tqdm`, no user interaction
   - Remove old `_match_list()` (its logic folds into the new `match_list()`)
   - Remove `from tqdm import tqdm`
   - Expose `embed_matches(pairs: list[tuple[Track, SpotifyTrack]]) -> None` as a public method: calls `_prefetch_isrc_data()` then `_update_spotify_match_in_source_track()` for each pair

5. `src/matchers/deezer_matcher.py` — same changes:
   - New `match_list()` yields `MatchOutcome`, removes all UI
   - Remove `from tqdm import tqdm`
   - Expose `embed_matches(pairs: list[tuple[Track, DeezerTrack]]) -> None`

### Phase 4 — Define `IMatchView` ABC + `CliMatchView` *(View layer)*

6. Create `src/views/__init__.py` (empty) and `src/views/match_view.py`:
   - `IMatchView(ABC)` with abstract methods:
     ```python
     def begin_matching(self, total: int) -> None: ...
     def on_track_processed(self) -> None: ...
     def end_matching(self) -> None: ...
     def show_unmatched(self, track: Track) -> None: ...
     def show_skipped(self, track: Track) -> None: ...
     def choose_suggestion(self, track: Track, suggestions: list[Track]) -> int: ...
     ```

7. Create `src/views/cli_match_view.py` with `CliMatchView(IMatchView)`:
   - `begin_matching(total)` → `print("Matching source tracks...")` + `self._pbar = tqdm(total=total)`
   - `on_track_processed()` → `self._pbar.update(1)`
   - `end_matching()` → `self._pbar.close()`
   - `show_unmatched(track)` → `print(f"Could not match\n{track}")`
   - `show_skipped(track)` → `print(f"Skip track\n{track}")`
   - `choose_suggestion(track, suggestions)` → moves the exact existing logic from `Matcher.choose_suggestion()` (tabulate table + `click.prompt`)

   > **Progress bars are preserved.** The Presenter calls `view.begin_matching(total)` before iterating and `view.on_track_processed()` after each yielded outcome. `CliMatchView` manages the `tqdm` state internally. A `FakeMatchView` in tests simply no-ops all calls.

### Phase 5 — `resolve_matches()` Presenter helper *(depends on Phases 3–4)*

8. Create `src/presenters/__init__.py` (empty) and `src/presenters/matching.py`:

   ```python
   def resolve_matches(
       tracks: list[Track],
       matcher: Matcher,
       view: IMatchView,
       autopilot: bool = False,
       embed_matches: bool = False,
   ) -> list[Track]:
   ```

   **Phase 1 — matching loop:**
   - `view.begin_matching(len(tracks))`
   - Iterate `matcher.match_list(tracks)`; for each outcome:
     - `view.on_track_processed()`
     - `MATCHED` → collect into `confirmed`
     - `AMBIGUOUS` → defer into `ambiguous` list
     - `UNMATCHED` → `view.show_unmatched(track)`
     - `SKIPPED` → `view.show_skipped(track)`
   - `view.end_matching()`

   **Phase 2 — review ambiguous cases:**
   - For each AMBIGUOUS outcome:
     - if `autopilot` → take `suggestions[0]`
     - else → `idx = view.choose_suggestion(track, suggestions)`; skip if `idx < 0`
   - Append to `confirmed`

   **Phase 3 — embed:**
   - If `embed_matches` → `matcher.embed_matches(confirmed_pairs)`

   Returns `list[Track]` (matched tracks only).

### Phase 6 — Simplify Playlist models *(depends on Phase 3)*

9. `src/playlists/spotify_playlist.py`:
   - `import_tracks()`: remove matching — accept pre-matched `Iterable[SpotifyTrack]`, just calls `self.add_tracks(tracks)`. Remove `autopilot`/`embed_matches` params.
   - `create_from_another_playlist()`: remove matching — accept `matched_tracks: list[Track]` instead of `source_playlist + autopilot + embed_matches`. Just creates + adds.
   - Remove `SpotifyMatcher` import.

10. `src/playlists/deezer_playlist.py`:
    - `sync_tracks()`: remove matching — accept pre-matched `Iterable[Track]`, just does the add/remove diff. Remove `autopilot`/`embed_matches` params.
    - `create_from_another_playlist()`: same — remove matching, accept pre-matched tracks.
    - Remove `DeezerMatcher` import.

### Phase 7 — Wire Presenter in CLI *(depends on Phases 4–6)*

11. `src/main.py` — for every matching command:
    - Instantiate `CliMatchView()`
    - Call `resolve_matches(source.tracks, matcher, view, autopilot, embed_matches)` → get `matched`
    - Call the simplified playlist method with `matched`
    - Affected commands: `cli_spotify_import`, `cli_spotify_sync`, `cli_spotify_match`, `cli_deezer_import`, `cli_deezer_sync`, `cli_deezer_match`

### Phase 8 — Tests *(depends on all above)*

12. Update `tests/matchers/matcher_mock.py`:
    - Change `match_list()` mock to return `Iterator[MatchOutcome]`

13. Add `tests/presenters/test_matching.py`:
    - Test `resolve_matches()` with `MatcherMock` + `FakeMatchView(IMatchView)`
    - Scenarios: all matched, some ambiguous (`autopilot=True`), some ambiguous (user picks), unmatched, skipped, `embed_matches=True`

14. `uv run pytest tests/` to verify all pass

---

## Affected Files

| File | Change |
|------|--------|
| `src/matchers/__init__.py` | Add `MatchStatus`, `MatchOutcome`; remove `choose_suggestion()`; reshape abstract `match_list()` |
| `src/matchers/spotify_matcher.py` | Implement new `match_list()` (yields `MatchOutcome`); expose `embed_matches()`; remove `_match_list()`, tqdm, print |
| `src/matchers/deezer_matcher.py` | Same as above |
| `src/playlists/spotify_playlist.py` | Simplify `import_tracks()`, `create_from_another_playlist()` to accept pre-matched tracks |
| `src/playlists/deezer_playlist.py` | Simplify `sync_tracks()`, `create_from_another_playlist()` |
| `src/playlists/local_playlist.py` | Replace print/tqdm with logging (INFO / WARNING) |
| `src/tracks/local_track.py` | `logger.warning` instead of `print` in `_set_custom_tag()` |
| `src/views/__init__.py` | **New** (empty) |
| `src/views/match_view.py` | **New** — `IMatchView` ABC |
| `src/views/cli_match_view.py` | **New** — `CliMatchView` |
| `src/presenters/__init__.py` | **New** (empty) |
| `src/presenters/matching.py` | **New** — `resolve_matches()` helper |
| `src/main.py` | Wire `resolve_matches()` + `CliMatchView()` in all matching commands |
| `tests/matchers/matcher_mock.py` | Update `match_list()` return type |
| `tests/presenters/test_matching.py` | **New** — Presenter tests |

---

## Verification Checklist

- [ ] `uv run pytest tests/` — all tests pass
- [ ] `uv run ruff check .` — no linting errors
- [ ] `uv run mypy .` — no type errors
- [ ] Manual smoke test: `uv run python main.py spotify import --source <path> --destination <name>` — progress bars and interactive choice prompt work as before
- [ ] `SpotifyMatcher` and `DeezerMatcher` no longer import `tqdm` or `click`

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **ABCs, not Protocols** | `IMatchView` uses `ABC` + `@abstractmethod` — explicit contract, no duck typing |
| **`match_list()` stays in Model, signature changes** | Batch matching is business logic. `autopilot`/`embed_matches` (Presenter concerns) are removed from its signature; it yields `MatchOutcome` instead. |
| **Two-phase Presenter** | Phase 1 = drive the model loop + report progress via view. Phase 2 = resolve ambiguous cases with user input. Clean separation. |
| **No Null views** | Views are required by `resolve_matches()`. Tests provide `FakeMatchView`. No default needed. |
| **LocalPlaylist: logging, no view interface** | Per-file progress dropped to keep the Model pure. Status → `INFO`, errors → `WARNING`. |
| **`embed_matches()` on Matcher** | Exposed as a public Model method. The Presenter calls it after all user decisions are collected, enabling batch ISRC prefetch before writing. |
