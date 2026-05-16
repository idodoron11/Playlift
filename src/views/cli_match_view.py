"""Concrete CLI implementation of :class:`~views.match_view.IMatchView`."""

from typing import Any

import click
from tabulate import tabulate
from tqdm import tqdm

from tracks import Track
from views.match_view import IMatchView


class CliMatchView(IMatchView):
    """CLI view for the track-matching workflow.

    Uses ``tqdm`` for progress display and ``click.prompt`` for user input.
    """

    def __init__(self) -> None:
        self._pbar: tqdm[Any] | None = None

    def begin_matching(self, total: int) -> None:
        print("Matching source tracks...")
        self._pbar = tqdm(total=total)

    def on_track_processed(self) -> None:
        if self._pbar is not None:
            self._pbar.update(1)

    def end_matching(self) -> None:
        if self._pbar is not None:
            self._pbar.close()
            self._pbar = None

    def show_unmatched(self, track: Track) -> None:
        print(f"Could not match\n{track}")

    def show_skipped(self, track: Track) -> None:
        print(f"Skip track\n{track}")

    def choose_suggestion(self, track: Track, suggestions: list[Track]) -> int:
        print(f"Please choose the best match for\n{track}")
        print("If none match, type -1")
        headers = ["#", "Artist", "Track Title", "Album", "Track Position", "Duration"]
        data = [
            (pos, s.display_artist, s.title, s.album, s.track_number, s.duration) for pos, s in enumerate(suggestions)
        ]
        results_tbl_visual = tabulate(data, headers=headers)
        print(results_tbl_visual)
        return int(
            click.prompt("Enter best match index (#):", default=0, type=click.IntRange(-1, len(suggestions) - 1))
        )
