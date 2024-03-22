from typing import Iterable, List

import click

from api.spotify import SpotifyAPI
from matchers.spotify_matcher import SpotifyMatcher
from playlists import Playlist
from tracks import Track
from tracks.spotify_track import SpotifyTrack
from tabulate import tabulate


class SpotifyPlaylist(Playlist):
    def __init__(self, playlist_url: str = None, data: dict = None):
        self._id = SpotifyAPI.get_instance()._get_id('playlist', playlist_url)
        self._data: dict = data
        if self._data and self._data['id'] != self._id:
            raise ValueError("The data object does not match the track id")
        self._tracks: Iterable[SpotifyTrack]

    def _load_data(self):
        self._data = SpotifyAPI.get_instance().playlist(self.playlist_id)
        self._tracks = []
        api_tracks = self._data['tracks']
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
    def create_from_another_playlist(cls, playlist_name: str, source_playlist: Playlist, public: bool = False, autopilot: bool = False):
        suggestions_list = SpotifyPlaylist.track_matcher().match_list(source_playlist.tracks)
        sp_tracks: List[SpotifyTrack] = []
        for index, suggestions in enumerate(map(lambda x: list(x), suggestions_list)):
            if len(suggestions) > 1 and not autopilot:
                choice = SpotifyPlaylist.choose_suggestion(source_playlist.tracks[index], suggestions)
                if choice >= 0:
                    sp_tracks.append(suggestions[choice])
            elif len(suggestions) >= 1:
                sp_tracks.append(suggestions[0])
            else:
                print(f"Could not match\n{source_playlist.tracks[index]}")
        new_playlist = cls.create(playlist_name, public=public)
        new_playlist.add_tracks(sp_tracks)
        return new_playlist

    @staticmethod
    def choose_suggestion(track: Track, suggestions: List[SpotifyTrack]) -> int:
        print(f'Please choose the best match for\n{track}')
        print("If none match, type -1")
        headers = ["#", "Artist", "Track Title", "Album", "Track Position", "Duration"]
        data = [(pos, track.display_artist, track.title,  track.album, track.track_number, track.duration)
                for pos, track in enumerate(suggestions)]
        results_tbl_visual = tabulate(data, headers=headers)
        print(results_tbl_visual)
        return click.prompt("Enter best match index (#):", default=0, type=click.IntRange(-1, len(suggestions)))

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
