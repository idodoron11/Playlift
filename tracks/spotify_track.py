from __future__ import annotations

from typing import Any
from api.spotify import SpotifyAPI
from tracks import Track


class SpotifyTrack(Track):
    def __init__(self, track_url: str, data: dict[str, Any] | None = None):
        self._id = SpotifyAPI.get_instance()._get_id('track', track_url)
        self._data: dict[str, Any] | None = data
        if self._data and self._data['id'] != self._id:
            raise ValueError("The data object does not match the track id")

    @property
    def data(self) -> dict[str, Any]:
        if not self._data:
            self._data = SpotifyAPI.get_instance().track(self._id)
        return self._data

    @property
    def artists(self) -> list[str]:
        return [str(item['name']) for item in self.data['artists']]

    @property
    def title(self) -> str:
        return str(self.data['name'])

    @property
    def album(self) -> str:
        return str(self.data['album']['name'])

    @property
    def duration(self) -> float:
        duration_ms = self.data['duration_ms']
        return float(duration_ms) / 1000

    @property
    def track_id(self) -> str:
        return str(self._id)

    @property
    def track_url(self) -> str:
        return f"https://open.spotify.com/track/{self.track_id}"

    @property
    def track_number(self) -> int:
        return int(self.data['track_number'])
