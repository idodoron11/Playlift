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
            cls.__instance = spotipy.Spotify(
                auth_manager=auth_manager,
                retries=0  # See https://github.com/spotipy-dev/spotipy/issues/913#issuecomment-1899143238
            )
        return cls.__instance

    def __init__(self) -> None:
        raise TypeError("An instance of this class already exists")
