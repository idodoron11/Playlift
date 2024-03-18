from typing import Iterable, List

from api.spotify import SpotifyAPI
from playlists import Playlist
from tracks import Track
from tracks.spotify_track import SpotifyTrack


class SpotifyPlaylist(Playlist):
    def __init__(self, playlist_url: str = None):
        self._id = SpotifyAPI.get_instance()._get_id('playlist', playlist_url)
        self._data: dict
        self._tracks: Iterable[SpotifyTrack]

    def _load_data(self):
        self._data = SpotifyAPI.get_instance().playlist(self._id)
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
        if not self._data:
            self._load_data()
        return self._tracks

    @property
    def playlist_id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self.data['name']

    @property
    def data(self) -> dict:
        if not self._data:
            self._load_data()
        return self._data

    def remove_track(self, track: SpotifyTrack) -> None:
        raise NotImplementedError

    def add_tracks(self, tracks: List[SpotifyTrack]) -> None:
        for start in range(0, len(tracks), 100):
            end = min(len(tracks), start + 100)
            chunk = map(lambda track: track.track_id, tracks[start:end])
            SpotifyAPI.get_instance().playlist_add_items(self.playlist_id, chunk)

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, self.__class__):
            return False
        return self.playlist_id == other.playlist_id

    def __hash__(self):
        return hash(self.playlist_id)
