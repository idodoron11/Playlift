from __future__ import annotations

from typing import TYPE_CHECKING, Any

from playlists.spotify_playlist import SpotifyPlaylist

if TYPE_CHECKING:
    import spotipy

    from tracks.spotify_track import SpotifyTrack


class SpotifyPlaylistSpy(SpotifyPlaylist):
    def __init__(self, playlist_url: str | None = None, **kwargs: object) -> None:
        self._id = playlist_url or ""
        self._data: dict[str, Any] | None = {}
        self._tracks: list[SpotifyTrack] = []

    @classmethod
    def create(  # type: ignore[no-any-unimported]  # spotipy ships no type stubs
        cls, playlist_name: str, public: bool = False, *, client: spotipy.Spotify | None = None
    ) -> SpotifyPlaylistSpy:
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
