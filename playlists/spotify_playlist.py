from typing import Iterable, List

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
        self._data = SpotifyAPI.get_instance().playlist(self._url)
        self._tracks = []
        api_tracks = self._data['tracks']
        while api_tracks:
            for api_track in api_tracks['items']:
                self._tracks.append(SpotifyTrack(api_track['track']['id']))
            api_tracks = SpotifyAPI.get_instance().next(api_tracks)

    @classmethod
    def create(cls, playlist_name: str, public: bool = False):
        user_id = SpotifyAPI.get_instance().current_user()["id"]
        playlist_resp = SpotifyAPI.get_instance().user_playlist_create(user_id, playlist_name, public=public)
        playlist_id = playlist_resp["id"]
        return cls(playlist_id)

    @property
    def tracks(self) -> Iterable[Track]:
        return self._tracks

    @property
    def playlist_id(self) -> str:
        return self._data['id']

    @property
    def name(self) -> str:
        return self._data['name']

    def remove_track(self, track: SpotifyTrack) -> None:
        raise NotImplementedError

    def add_tracks(self, tracks: List[SpotifyTrack]) -> None:
        SpotifyAPI.get_instance().playlist_add_items(self.playlist_id, map(lambda track: track.track_id, tracks))
