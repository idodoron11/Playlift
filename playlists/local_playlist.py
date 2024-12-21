from typing import Iterable, List

import mutagen

from matchers import Matcher
from playlists import Playlist
from tracks.local_track import LocalTrack
from tqdm import tqdm


class LocalPlaylist(Playlist):
    def __init__(self, playlist_file_path: str):
        self._source_filepath = playlist_file_path
        self._tracks: List[LocalTrack] = []
        with open(self._source_filepath, "r", encoding="utf-8") as f:
            files = map(lambda x: x.strip(), f.readlines())  # remove redundant spaces
            files = filter(lambda x: len(x) > 0 and not x.startswith("#"), files)  # skip empty lines
            self._load_tracks(files)

    def _load_tracks(self, files: Iterable[str]) -> None:
        print("Reading playlist tracks metadata")
        for file_path in tqdm(list(files)):
            try:
                self._tracks.append(LocalTrack(file_path))
            except mutagen.MutagenError as e:
                print(f"Error during file scan: {e}"
                      f"\nFile: {file_path}")

    @property
    def tracks(self) -> Iterable[LocalTrack]:
        return self._tracks

    def remove_track(self, track: LocalTrack) -> None:
        self._tracks.remove(track)

    def add_tracks(self, tracks: List[LocalTrack]) -> None:
        self._tracks += tracks

    def save_playlist(self):
        files = [track.file_path for track in self._tracks]
        with open(self._source_filepath, "w", encoding='utf-8') as f:
            f.write("\n".join(files))

    @staticmethod
    def track_matcher() -> Matcher:
        raise TypeError("Local playlists don't have a track matcher")
