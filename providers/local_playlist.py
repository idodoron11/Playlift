from typing import Iterable, List
from providers.playlist import Playlist
from tracks.mutagen_track import MutagenTrack
from tracks.track import Track


class LocalPlaylist(Playlist):
    def __init__(self, playlist_file_path: str):
        self._source_filepath = playlist_file_path
        self._tracks: List[Track] = []
        with open(self._source_filepath, "r", encoding="utf-8") as f:
            self._load_tracks(f.readlines())

    def _load_tracks(self, files: List[str]) -> None:
        for file_path in files:
            self._tracks.append(MutagenTrack(file_path))

    @property
    def tracks(self) -> Iterable[Track]:
        return self._tracks

    def remove_track(self, track: Track) -> None:
        pass

    def add_track(self, track: Track) -> None:
        pass
