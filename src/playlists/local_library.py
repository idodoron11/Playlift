from collections.abc import Callable, Iterable
from pathlib import Path

from playlists import TrackCollection
from tracks import Track
from tracks.local_track import LocalTrack


class LocalLibrary(TrackCollection):
    def __init__(
        self,
        root_directory: str,
        on_loading_started: Callable[[int], None] | None = None,
        on_track_loaded: Callable[[], None] | None = None,
    ):
        self._root_directory = Path(root_directory)
        supported_extensions = (".mp3", ".flac", ".m4a")
        all_files = [
            str(file) for extension in supported_extensions for file in self._root_directory.glob(f"**/*{extension}")
        ]
        self._tracks: list[LocalTrack] = []
        if on_loading_started:
            on_loading_started(len(all_files))
        for file_path in all_files:
            self._tracks.append(LocalTrack(file_path))
            if on_track_loaded:
                on_track_loaded()

    @property
    def tracks(self) -> Iterable[Track]:
        return self._tracks
