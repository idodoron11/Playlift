from singleton import Singleton
from config import CONFIG
import spotipy
from spotipy.oauth2 import SpotifyOAuth

scope = "user-library-read"


class SpotifyAPI(metaclass=Singleton):
    def __init__(self):
        auth_manager = SpotifyOAuth(
            scope=scope,
            client_id=CONFIG.spotify_client_id,
            client_secret=CONFIG.spotify_client_secret,
            redirect_uri=CONFIG.spotify_redirect_url
        )
        self.api = spotipy.Spotify(auth_manager=auth_manager)
