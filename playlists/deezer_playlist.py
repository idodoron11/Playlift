from typing import Optional, Any, Iterator
import re
import deezer
from tracks.deezer_track import DeezerTrack
from api.deezer import DeezerAPI

class DeezerPlaylist:
    PLAYLIST_URL_PATTERN = r'https://www\.deezer\.com(?:/[a-z]{2})?/playlist/(\d+)'

    def __init__(self, playlist_id_or_url: str | int) -> None:
        self._client: Optional[deezer.Client] = None
        self._data: Optional[Any] = None
        self.playlist_id: int = self._get_playlist_id(playlist_id_or_url)

    def _get_playlist_id(self, playlist_id_or_url: str | int) -> int:
        # Handle URLs by extracting the ID
        if isinstance(playlist_id_or_url, str) and playlist_id_or_url.startswith('http'):
            match = re.match(self.PLAYLIST_URL_PATTERN, playlist_id_or_url)
            if not match:
                raise ValueError(f"Invalid Deezer playlist URL: {playlist_id_or_url}")

            candidate = match.group(1)
            if not candidate:
                raise ValueError(f"Invalid Deezer playlist URL: {playlist_id_or_url}")
            if not candidate.isdigit():
                raise ValueError(f"Invalid Deezer playlist URL: {playlist_id_or_url}")

            return int(candidate)
        elif isinstance(playlist_id_or_url, int):
            return playlist_id_or_url
        elif isinstance(playlist_id_or_url, str) and playlist_id_or_url.isdigit():
            return int(playlist_id_or_url)
        else:
            raise ValueError("playlist_id_or_url must be an integer ID or a valid Deezer playlist URL")

    def _client_instance(self) -> deezer.Client:
        if self._client is None:
            self._client = DeezerAPI.get_instance()
        return self._client

    def _ensure_data(self, force: bool = False) -> None:
        if self._data is None or force:
            client = self._client_instance()
            self._data = client.get_playlist(self.playlist_id)

    @property
    def name(self) -> str:
        self._ensure_data()
        return self._data.title

    @property
    def tracks(self) -> Iterator[DeezerTrack]:
        self._ensure_data()
        for track in self._data.tracks:
            yield DeezerTrack(track.id)

    @staticmethod
    def create(name: str) -> 'DeezerPlaylist':
        client = DeezerAPI.get_instance()
        # Get the current user and create a playlist
        user = client.get_user()
        playlist_id = user.create_playlist(name)
        # Create and initialize the playlist with just the ID
        result = DeezerPlaylist(playlist_id)
        result._client = client  # Keep the same client instance
        return result

    def add_tracks(self, tracks: list[DeezerTrack]) -> bool:
        """Add tracks to the playlist."""
        track_ids = [int(track.track_id) for track in tracks]
        if not track_ids:
            return True

        try:
            client = self._client_instance()
            playlist = client.get_playlist(self.playlist_id)
            # When using the real Deezer API, add_tracks is a method on the playlist object
            success = playlist.add_tracks(track_ids)
            if success:
                self._ensure_data(force=True)
            return success
        except Exception as e:
            # Log or handle the error appropriately
            return False

    def __str__(self) -> str:
        return f"Deezer Playlist: {self.name} ({self.playlist_id})"
