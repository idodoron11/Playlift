from typing import Iterable

from api.spotify import SpotifyAPI
from playlists import Playlist
from tracks import Track
from tracks.spotify_track import SpotifyTrack


class SpotifyPlaylist(Playlist):
    def __init__(self, playlist_url: str = None):
        self._url = playlist_url
        self._data: dict
        self._tracks: Iterable[SpotifyTrack]
        self._load_data()

    def _load_data(self):
        self._data = SpotifyAPI().api.playlist(self._url)
        self._tracks = [SpotifyTrack(api_track['track']['id']) for api_track in self._data['tracks']['items']]

    @classmethod
    def create(cls, playlist_name: str):
        playlist_url = f"Create a new playlist named {playlist_name} and retrieve its url"
        return cls(playlist_url)

    @property
    def tracks(self) -> Iterable[Track]:
        return self._tracks

    @property
    def playlist_id(self) -> str:
        return self._data['id']

    @property
    def name(self) -> str:
        return self._data['name']

    def remove_track(self, track: Track) -> None:
        raise NotImplementedError

    def add_track(self, track: Track) -> None:
        raise NotImplementedError
