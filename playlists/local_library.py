from pathlib import Path
from typing import Iterable, List

from playlists import TrackCollection
from tracks import Track
from tracks.local_track import LocalTrack


class LocalLibrary(TrackCollection):
    def __init__(self, root_directory: str):
        self._root_directory = Path(root_directory)
        supported_extensions = (".mp3", ".flac", ".m4a")
        self._tracks: List[LocalTrack] = []
        for extension in supported_extensions:
            for file in self._root_directory.glob(f"**/*{extension}"):
                self._tracks.append(LocalTrack(str(file)))

    @property
    def tracks(self) -> Iterable[Track]:
        return self._tracks
