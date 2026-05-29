"""Concrete CLI implementation of :class:`~views.playlist_load_view.IPlaylistLoadView`."""

from typing import Any

from tqdm import tqdm

from views.playlist_load_view import IPlaylistLoadView


class CliPlaylistLoadView(IPlaylistLoadView):
    """CLI view for the local track-loading workflow.

    Uses ``tqdm`` for progress display.
    """

    def __init__(self) -> None:
        self._pbar: tqdm[Any] | None = None

    def begin_loading(self, total: int) -> None:
        self._pbar = tqdm(total=total, desc="Loading playlist tracks information")

    def on_track_loaded(self) -> None:
        if self._pbar is not None:
            self._pbar.update(1)

    def end_loading(self) -> None:
        if self._pbar is not None:
            self._pbar.close()
            self._pbar = None
