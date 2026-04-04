from typing import Any

from playlists.spotify_playlist import SpotifyPlaylist
from tracks.spotify_track import SpotifyTrack


class SpotifyPlaylistSpy(SpotifyPlaylist):
    def __init__(self, playlist_url: str | None = None) -> None:
        self._id = playlist_url or ""
        self._data: dict[str, Any] | None = {}
        self._tracks: list[SpotifyTrack] = []

    @classmethod
    def create(cls, playlist_name: str, public: bool = False) -> "SpotifyPlaylistSpy":
        return cls("dummy playlist id")

    @property
    def tracks(self) -> list[SpotifyTrack]:
        return self._tracks

    @property
    def data(self) -> dict[str, Any]:
        return self._data or {}

    def add_tracks(self, tracks: list[SpotifyTrack]) -> None:  # type: ignore[override]
        self._tracks.extend(tracks)

    def remove_track(self, tracks: list[SpotifyTrack]) -> None:  # type: ignore[override]
        for track in list(self._tracks):
            if track in tracks:
                self._tracks.remove(track)
