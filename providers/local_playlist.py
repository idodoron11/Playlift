from typing import Iterable, List
from providers import Playlist
from tracks.local_track import LocalTrack
from tracks import Track


class LocalPlaylist(Playlist):
    def __init__(self, playlist_file_path: str):
        self._source_filepath = playlist_file_path
        self._tracks: List[Track] = []
        with open(self._source_filepath, "r", encoding="utf-8") as f:
            files = filter(lambda x: x, f.readlines())  # skip empty lines
            files = map(lambda x: x.strip(), files)  # remove redundant spaces
            self._load_tracks(files)

    def _load_tracks(self, files: Iterable[str]) -> None:
        for file_path in files:
            self._tracks.append(LocalTrack(file_path))

    @property
    def tracks(self) -> Iterable[Track]:
        return self._tracks

    def remove_track(self, track: Track) -> None:
        pass

    def add_track(self, track: Track) -> None:
        pass
