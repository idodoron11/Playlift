from playlists import Playlist
from tracks import Track


class PlaylistMock(Playlist):
    def __init__(self, tracks: list[Track]) -> None:
        self._tracks = tracks

    @property
    def tracks(self) -> list[Track]:
        return self._tracks

    def remove_track(self, tracks: list[Track]) -> None:
        for track in tracks:
            self._tracks.remove(track)

    def add_tracks(self, track: Track) -> None:
        self._tracks.append(track)
