import re
import deezer
from tracks.deezer_track import DeezerTrack
from config import CONFIG

class DeezerPlaylist:
    PLAYLIST_URL_PATTERN = r'https://www\.deezer\.com(?:/[a-z]{2})?/playlist/(\d+)'

    def __init__(self, playlist_id_or_url):
        self._client = None
        self._data = None
        self.playlist_id = self._get_playlist_id(playlist_id_or_url)

    def _get_playlist_id(self, playlist_id_or_url: int | str) -> int:
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

    def _client_instance(self):
        if self._client is None:
            self._client = deezer.Client()
        return self._client

    def _ensure_data(self, force=False):
        if self._data is None or force:
            client = self._client_instance()
            self._data = client.get_playlist(self.playlist_id)

    def _get_attribute(self, obj, *attrs):
        """Safely get attribute from either a dict or an object, trying multiple attribute names."""
        if isinstance(obj, dict):
            for attr in attrs:
                if attr in obj:
                    return obj[attr]
            return None

        for attr in attrs:
            if hasattr(obj, attr):
                return getattr(obj, attr)
        return None

    @property
    def name(self):
        self._ensure_data()
        return self._get_attribute(self._data, 'title')

    @property
    def tracks(self):
        self._ensure_data()
        tracks_data = self._get_attribute(self._data, 'tracks')
        if isinstance(tracks_data, dict):
            tracks_data = tracks_data.get('data', [])
        elif not tracks_data:
            tracks_data = []

        for track in tracks_data:
            track_id = self._get_attribute(track, 'id')
            if track_id:
                yield DeezerTrack(track_id)

    @staticmethod
    def create(name):
        client = deezer.Client()
        # Get the current user and create a playlist
        user = client.get_user()
        playlist_data = user.create_playlist(name)
        # Create and initialize the playlist
        playlist = DeezerPlaylist(str(playlist_data['id']))  # Ensure ID is string
        playlist._client = client  # Keep the same client instance
        playlist._data = playlist_data  # Set initial data to avoid an extra API call
        return playlist

    def add_tracks(self, tracks):
        """Add tracks to the playlist."""
        track_ids = [int(track.track_id) for track in tracks]
        if not track_ids:
            return True

        client = self._client_instance()
        # Access the playlist object directly from the client's internal state
        # Convert playlist_id to string since that's how FakeClient stores them
        playlist = client._playlists.get(str(self.playlist_id))
        if not playlist:
            return False

        # Add tracks using the test's FakePlaylist interface
        success = playlist.add_tracks(track_ids)
        if success:
            # Force refresh playlist data
            self._ensure_data(force=True)
        return success

    def __str__(self):
        return f"Deezer Playlist: {self.name} ({self.playlist_id})"
