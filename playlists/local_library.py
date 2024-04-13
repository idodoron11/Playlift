from typing import List, Iterable

from matchers import Matcher
from playlists import Playlist
from tracks import Track
from pathlib import Path

from tracks.local_track import LocalTrack


class LocalLibrary(Playlist):
    def __init__(self, root_directory: str):
        self._root_directory = Path(root_directory)
        supported_extensions = (".mp3", ".flac", ".m4a")
        self._tracks: List[LocalTrack] = []
        for extension in supported_extensions:
            for file in self._root_directory.glob(f'**/*{extension}'):
                self._tracks.append(LocalTrack(str(file)))

    @property
    def tracks(self) -> Iterable[Track]:
        return self._tracks

    @staticmethod
    def track_matcher() -> Matcher:
        raise TypeError("Local libraries don't have a track matcher")

    def remove_track(self, tracks: List[Track]) -> None:
        raise NotImplementedError

    def add_tracks(self, track: Track) -> None:
        raise NotImplementedError

