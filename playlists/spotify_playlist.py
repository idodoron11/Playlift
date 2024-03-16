from typing import Iterable

from playlists import Playlist
from tracks import Track


class SpotifyPlaylist(Playlist):
    def __init__(self, playlist_url: str = None):
        self._url = playlist_url

    @classmethod
    def create(cls, playlist_name: str):
        playlist_url = f"Create a new playlist named {playlist_name} and retrieve its url"
        return cls(playlist_url)

    @property
    def tracks(self) -> Iterable[Track]:
        return None

    def remove_track(self, track: Track) -> None:
        return None

    def add_track(self, track: Track) -> None:
        return None
