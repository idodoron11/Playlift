import logging
from collections.abc import Callable, Iterable

import mutagen

from playlists import Playlist
from playlists.path_mapper import PathMapper
from tracks.local_track import LocalTrack

logger = logging.getLogger(__name__)


class LocalPlaylist(Playlist):
    def __init__(
        self,
        playlist_file_path: str,
        path_mapper: PathMapper | None = None,
        on_loading_started: Callable[[int], None] | None = None,
        on_track_loaded: Callable[[], None] | None = None,
    ):
        self._source_filepath = playlist_file_path
        self._path_mapper = path_mapper
        self._tracks: list[LocalTrack] = []
        with open(self._source_filepath, encoding="utf-8") as f:
            lines: Iterable[str] = (x.strip() for x in f.readlines())  # remove redundant spaces
            lines = (x for x in lines if len(x) > 0 and not x.startswith("#"))  # skip empty lines
            self._load_tracks(lines, on_loading_started, on_track_loaded)

    def _load_tracks(
        self,
        files: Iterable[str],
        on_loading_started: Callable[[int], None] | None = None,
        on_track_loaded: Callable[[], None] | None = None,
    ) -> None:
        logger.info("Reading playlist tracks metadata")
        # Apply path mapping if mapper is provided
        if self._path_mapper:
            files = map(self._path_mapper.map, files)
        file_list = list(files)
        if on_loading_started:
            on_loading_started(len(file_list))
        for file_path in file_list:
            try:
                self._tracks.append(LocalTrack(file_path))
            except mutagen.MutagenError as e:  # type: ignore[attr-defined]
                logger.warning("Error during file scan: %s\nFile: %s", e, file_path)
            if on_track_loaded:
                on_track_loaded()

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
        with open(self._source_filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(files))
