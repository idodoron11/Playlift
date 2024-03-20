from typing import List, Optional

from playlists.spotify_playlist import SpotifyPlaylist
from tracks import Track
from tracks.spotify_track import SpotifyTrack


class SpotifyPlaylistSpy(SpotifyPlaylist):
    def __init__(self, playlist_url: str = None):
        self._id = playlist_url
        self._data: Optional[dict] = {}
        self._tracks: List[Track] = []

    @classmethod
    def create(cls, playlist_name: str, public: bool = False):
        return cls("dummy playlist id")

    @property
    def tracks(self) -> List[Track]:
        return self._tracks

    @property
    def data(self):
        return self._data

    def add_tracks(self, tracks: List[SpotifyTrack]) -> None:
        self._tracks.extend(tracks)

    def remove_track(self, track: SpotifyTrack) -> None:
        for track in self._tracks:
            self._tracks.remove(track)
