import functools

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from config import CONFIG

scopes = ["user-library-read", "playlist-modify-public", "playlist-modify-private"]


@functools.cache
def get_spotify_client() -> spotipy.Spotify:  # type: ignore[no-any-unimported]  # spotipy ships no type stubs
    """Return the singleton authenticated Spotify client.

    Creates and caches a single spotipy.Spotify instance on first call using
    credentials from CONFIG. Subsequent calls return the cached instance.

    Returns:
        An authenticated spotipy.Spotify client.
    """
    auth_manager = SpotifyOAuth(
        scope=scopes,
        client_id=CONFIG.spotify_client_id,
        client_secret=CONFIG.spotify_client_secret,
        redirect_uri=CONFIG.spotify_redirect_url,
    )
    return spotipy.Spotify(
        auth_manager=auth_manager,
        retries=0,  # See https://github.com/spotipy-dev/spotipy/issues/913#issuecomment-1899143238
    )
