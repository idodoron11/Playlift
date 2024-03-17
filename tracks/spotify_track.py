from __future__ import annotations

from typing import List, Optional
from api.spotify import SpotifyAPI
from tracks import Track


class SpotifyTrack(Track):
    def __init__(self, track_url: str):
        self._id = SpotifyAPI.get_instance()._get_id('track', track_url)
        self._data: Optional[dict] = None

    @property
    def data(self) -> dict:
        if not self._data:
            self._data = SpotifyAPI.get_instance().track(self._id)
        return self._data

    @property
    def artists(self) -> List[str]:
        return [item['name'] for item in self.data['artists']]

    @property
    def title(self) -> str:
        return self.data['name']

    @property
    def album(self) -> str:
        return self.data['album']['name']

    @property
    def duration(self) -> float:
        duration_ms = self.data['duration_ms']
        return duration_ms / 1000

    @property
    def track_id(self) -> str:
        return self._id

    @staticmethod
    def search(artist: str, album: str, title: str) -> List[SpotifyTrack]:
        explicit_search_string = f'artist:{artist} album:{album} track:{title}'
        free_text_search_string = f'{artist} {title}'
        response = SpotifyAPI.get_instance().search(explicit_search_string)
        if not response['tracks'] or response['tracks']['total'] == 0:
            response = SpotifyAPI.get_instance().search(free_text_search_string)
            if not response['tracks'] or response['tracks']['total'] == 0:
                return []
        return [SpotifyTrack(track['id']) for track in response['tracks']['items']]

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, self.__class__):
            return False
        return self.track_id == other.track_id
