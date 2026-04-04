from typing import Iterable, List, Optional

import mutagen
from tqdm import tqdm

from matchers import Matcher
from playlists import Playlist
from playlists.path_mapper import PathMapper
from tracks.local_track import LocalTrack


class LocalPlaylist(Playlist):
    def __init__(self, playlist_file_path: str, path_mapper: Optional[PathMapper] = None):
        self._source_filepath = playlist_file_path
        self._path_mapper = path_mapper
        self._tracks: List[LocalTrack] = []
        with open(self._source_filepath, "r", encoding="utf-8") as f:
            lines: Iterable[str] = (x.strip() for x in f.readlines())  # remove redundant spaces
            lines = (x for x in lines if len(x) > 0 and not x.startswith("#"))  # skip empty lines
            self._load_tracks(lines)

    def _load_tracks(self, files: Iterable[str]) -> None:
        print("Reading playlist tracks metadata")
        # Apply path mapping if mapper is provided
        if self._path_mapper:
            files = map(self._path_mapper.map, files)
        for file_path in tqdm(list(files)):
            try:
                self._tracks.append(LocalTrack(file_path))
            except mutagen.MutagenError as e:  # type: ignore[attr-defined]
                print(f"Error during file scan: {e}"
                      f"\nFile: {file_path}")

    @property
    def tracks(self) -> Iterable[LocalTrack]:
        return self._tracks

    def remove_track(self, tracks: list[LocalTrack]) -> None:  # type: ignore[override]  # narrowed type is safe in practice
        for t in tracks:
            self._tracks.remove(t)

    def add_tracks(self, tracks: list[LocalTrack]) -> None:  # type: ignore[override]  # narrowed type is safe in practice
        self._tracks += tracks

    def save_playlist(self) -> None:
        files = [track.file_path for track in self._tracks]
        with open(self._source_filepath, "w", encoding='utf-8') as f:
            f.write("\n".join(files))

    @staticmethod
    def track_matcher() -> Matcher:
        raise TypeError("Local playlists don't have a track matcher")
