from config import CONFIG
import spotipy
from spotipy.oauth2 import SpotifyOAuth

scopes = [
    "user-library-read",
    "playlist-modify-public",
    "playlist-modify-private"
]


class SpotifyAPI:
    __instance = None

    @classmethod
    def get_instance(cls) -> spotipy.Spotify:
        if cls.__instance is None:
            auth_manager = SpotifyOAuth(
                scope=scopes,
                client_id=CONFIG.spotify_client_id,
                client_secret=CONFIG.spotify_client_secret,
                redirect_uri=CONFIG.spotify_redirect_url
            )
            cls.__instance = spotipy.Spotify(auth_manager=auth_manager)
        return cls.__instance

    def __init__(self):
        raise TypeError("Use get_instance() instead")
