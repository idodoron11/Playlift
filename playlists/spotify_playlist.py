from typing import Iterable, List, Optional

from api.spotify import SpotifyAPI
from matchers.spotify_matcher import SpotifyMatcher
from playlists import Playlist
from tracks import Track
from tracks.spotify_track import SpotifyTrack
from tqdm import tqdm


class SpotifyPlaylist(Playlist):
    def __init__(self, playlist_url: str = None, data: dict = None):
        self._id = SpotifyAPI.get_instance()._get_id('playlist', playlist_url)
        self._data: dict = data
        if self._data and self._data['id'] != self._id:
            raise ValueError("The data object does not match the track id")
        self._tracks: Iterable[SpotifyTrack]

    def _load_data(self):
        self._data = SpotifyAPI.get_instance().playlist_items(self.playlist_id)
        self._tracks = []
        api_tracks = self._data
        while api_tracks:
            for api_track in api_tracks['items']:
                self._tracks.append(SpotifyTrack(api_track['track']['id'], data=api_track['track']))
            api_tracks = SpotifyAPI.get_instance().next(api_tracks)

    @classmethod
    def create(cls, playlist_name: str, public: bool = False):
        user_id = SpotifyAPI.get_instance().current_user()["id"]
        playlist_resp = SpotifyAPI.get_instance().user_playlist_create(user_id, playlist_name, public=public)
        playlist_id = playlist_resp["id"]
        return cls(playlist_id)

    @classmethod
    def create_from_another_playlist(cls, playlist_name: str, source_playlist: Playlist, public: bool = False):
        sp_tracks = []
        guessed_tracks_positions = []
        for index, track in enumerate(tqdm(source_playlist.tracks)):
            match = cls.track_matcher().match(track)
            if match:
                sp_tracks.append(match)
                continue
            suggestions = cls.track_matcher().suggest_match(track)
            if suggestions:
                sp_tracks.append(next(suggestions.__iter__()))
                guessed_tracks_positions.append(index)
        print("The following tracks were guessed:\n")
        for index in guessed_tracks_positions:
            source: Track = source_playlist.tracks[index]
            target: SpotifyTrack = sp_tracks[index]
            print(
                f"{index} {source.display_artist} - {source.title}, {source.album}    --->    {target.display_artist} - {target.title}, {target.album}")
        new_playlist = cls.create(playlist_name, public=public)
        new_playlist.add_tracks(sp_tracks)
        return new_playlist

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

    @staticmethod
    def track_matcher() -> SpotifyMatcher:
        return SpotifyMatcher.get_instance()

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, self.__class__):
            return False
        return self.playlist_id == other.playlist_id

    def __hash__(self):
        return hash(self.playlist_id)
