from __future__ import annotations

from typing import List
from api.spotify import SpotifyAPI
from tracks import Track


class SpotifyTrack(Track):
    def __init__(self, track_url: str):
        self._url = track_url
        self._track = SpotifyAPI().api.track(self._url)

    @property
    def artists(self) -> List[str]:
        return [item['name'] for item in self._track['artists']]

    @property
    def title(self) -> str:
        return self._track['name']

    @property
    def album(self) -> str:
        return self._track['album']['name']

    @property
    def duration(self) -> float:
        duration_ms = self._track['duration_ms']
        return duration_ms / 1000

    @staticmethod
    def search(artist: str, album: str, title: str) -> List[SpotifyTrack]:
        explicit_search_string = f'artist:"{artist}" album:"{album}" title:"{title}"'
        free_text_search_string = f'{artist} {title}'
        response = SpotifyAPI().api.search(explicit_search_string)
        if not response['tracks'] or response['tracks']['total'] == 0:
            response = SpotifyAPI().api.search(free_text_search_string)
        if not response['tracks'] or response['tracks']['total'] == 0:
            return []
        return [SpotifyTrack(track['id']) for track in response['tracks']['items']]
