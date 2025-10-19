from config import CONFIG
import config as config_module
import deezer
from typing import Optional, cast, Any
import re
import requests
import webbrowser
from urllib.parse import urlparse, parse_qs, quote_plus
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading


class DeezerAPI:
    """Simple Deezer API wrapper using deezer-python Client.

    This is a starter implementation that mirrors the SpotifyAPI pattern in this
    project. It provides a singleton client and a few helper methods we'll need
    when integrating playlists and tracks, plus OAuth helpers to obtain an access token.
    """

    __instance: Optional[deezer.Client] = None

    @classmethod
    def get_instance(cls, auto_authorize: bool = True) -> deezer.Client:
        """Return a singleton deezer.Client instance.

        If an access token is present in `CONFIG.deezer_access_token`, the client
        will be constructed with it to allow privileged operations. If not and
        `auto_authorize` is True, attempt to obtain one via OAuth authorize flow.
        """
        if cls.__instance is None:
            token = getattr(CONFIG, "deezer_access_token", None)
            if not token and auto_authorize:
                # Attempt interactive authorization flow to get token
                token = cls.authorize_interactive()
                # If token obtained, persist it to config
                if token:
                    try:
                        if not config_module.CONFIG.config.has_section('DEEZER'):
                            config_module.CONFIG.config.add_section('DEEZER')
                        config_module.CONFIG.config.set('DEEZER', 'ACCESS_TOKEN', token)
                        with open(config_module.CONFIG_PATH, 'w') as f:
                            config_module.CONFIG.config.write(f)
                    except Exception:
                        # If saving fails, ignore; token is still returned for this session
                        pass
            if token:
                cls.__instance = deezer.Client(access_token=token)
            else:
                cls.__instance = deezer.Client()
        return cls.__instance

    def __init__(self):
        raise TypeError("An instance of this class already exists")

    # OAuth helpers
    @staticmethod
    def get_auth_url(perms: str = "basic_access,manage_library,manage_community") -> str:
        """Construct the Deezer authorization URL.

        perms: comma-separated permissions. See Deezer docs for available perms.
        """
        app_id = CONFIG.deezer_app_id
        redirect = CONFIG.deezer_redirect_url
        if not app_id or not redirect:
            raise RuntimeError("DEEZER APP_ID and REDIRECT_URL must be set in config to build auth URL")
        base = "https://connect.deezer.com/oauth/auth.php"
        # URL-encode redirect URI
        redirect_enc = quote_plus(redirect)
        # Deezer expects app_id, redirect_uri and perms
        return f"{base}?app_id={app_id}&redirect_uri={redirect_enc}&perms={perms}"

    @staticmethod
    def exchange_code_for_access_token(code: str) -> Optional[dict]:
        """Exchange authorization code for an access token using Deezer's endpoint.

        Returns a dict { 'access_token': str, 'expires': int } on success or None on failure.
        """
        app_id = CONFIG.deezer_app_id
        app_secret = CONFIG.deezer_app_secret
        if not app_id or not app_secret:
            raise RuntimeError("DEEZER APP_ID and APP_SECRET must be set in config to exchange code for token")
        token_endpoint = "https://connect.deezer.com/oauth/access_token.php"
        params = {
            'app_id': app_id,
            'secret': app_secret,
            'code': code,
            'output': 'json'
        }
        try:
            resp = requests.get(token_endpoint, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            # Expecting {'access_token': '...', 'expires': 3600}
            if 'access_token' in data:
                return data
            return None
        except Exception:
            return None

    @classmethod
    def authorize_interactive(cls, perms: str = "basic_access,manage_library,manage_community", timeout: int = 120) -> Optional[str]:
        """Interactive OAuth flow:
        - If redirect URI is localhost, open the browser and start a temporary HTTP server to capture the code.
        - Otherwise, return the auth URL for manual use (caller must copy the `code` query param and call exchange_code_for_access_token).

        Returns the access token string on success, or None.
        """
        auth_url = cls.get_auth_url(perms=perms)
        redirect = CONFIG.deezer_redirect_url
        parsed = urlparse(redirect) if redirect else None

        # If redirect points to localhost, attempt to run a temporary server to capture the code
        if parsed and parsed.hostname in ("localhost", "127.0.0.1"):
            port = parsed.port or 80
            # Annotate the container to satisfy static type checkers
            code_container: dict[str, Optional[str]] = {'code': None}

            class _Handler(BaseHTTPRequestHandler):
                def do_GET(self):
                    qs = parse_qs(urlparse(self.path).query)
                    code = qs.get('code', [None])[0]
                    code_container['code'] = code
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"<html><body><h1>Authorization complete</h1><p>You may close this window.</p></body></html>")

                # Suppress logging
                def log_message(self, format, *args):
                    return

            # Cast handler class to Any to satisfy static type checkers about factory signature
            server = HTTPServer((parsed.hostname, port), cast(Any, _Handler))

            def run_server():
                try:
                    server.handle_request()
                except Exception:
                    pass

            thread = threading.Thread(target=run_server, daemon=True)
            thread.start()

            # Open the user's browser to the auth URL
            try:
                webbrowser.open(auth_url)
            except Exception:
                pass

            # Wait for code to be set or timeout
            thread.join(timeout)
            server.server_close()

            code = code_container.get('code')
            if not code:
                return None

            # Help static analyzers: ensure `code` is not None here
            assert code is not None
            token_data = cls.exchange_code_for_access_token(code)
            return token_data.get('access_token') if token_data else None

        # Non-localhost redirect: fall back to manual flow
        # Caller must visit auth_url, approve, and provide the 'code' param to exchange_code_for_access_token
        # We'll open the browser for convenience and prompt the user to paste the code.
        try:
            webbrowser.open(auth_url)
        except Exception:
            pass

        # Prompt for the authorization code so this can work with non-local redirects
        try:
            print("Please visit the following URL in your browser and authorize the application:")
            print(auth_url)
            code = input("After authorizing, paste the 'code' query parameter here: ").strip()
        except Exception:
            # If input isn't available (non-interactive), raise with guidance
            raise RuntimeError(f"Visit this URL and obtain the 'code' query parameter: {auth_url}")

        if not code:
            return None
        token_data = cls.exchange_code_for_access_token(code)
        return token_data.get('access_token') if token_data else None

    # Helper to normalize ids/urls used elsewhere in the codebase
    @staticmethod
    def _get_id(kind: str, url_or_id: Optional[str]) -> Optional[int]:
        """Extract a Deezer numeric id from a url or return the id as int.

        Uses `kind` to try a targeted lookup first (e.g. '/track/123' or '/playlist/456'),
        then falls back to previous heuristics (numeric string or trailing numeric segment).

        Returns an int id when possible, or None when no numeric id can be found.
        """
        if url_or_id is None:
            return None
        # If it's already an int, return it
        if isinstance(url_or_id, int):
            return url_or_id
        # If it's a numeric string, convert to int
        if isinstance(url_or_id, str) and url_or_id.isdigit():
            return int(url_or_id)

        # Attempt to find '/{kind}/<digits>' in the URL using regex (case-insensitive)
        try:
            pattern = rf"/{re.escape(kind)}/(\d+)"
            m = re.search(pattern, url_or_id, flags=re.IGNORECASE)
            if m:
                return int(m.group(1))
        except re.error:
            # If regex fails for any reason, ignore and continue to fallback
            pass

        # Fallback: Try to extract trailing numeric id from typical Deezer URLs
        parts = str(url_or_id).rstrip("/\n ").split("/")
        if parts and parts[-1].isdigit():
            return int(parts[-1])
        # No numeric id found
        return None

    # Basic read operations
    @classmethod
    def track(cls, track_id_or_url: str) -> object:
        client = cls.get_instance()
        track_id = cls._get_id('track', track_id_or_url)
        if track_id is None:
            raise ValueError(f"Invalid Deezer track id or URL: {track_id_or_url}")
        return client.get_track(track_id)

    @classmethod
    def playlist(cls, playlist_id_or_url: str) -> object:
        client = cls.get_instance()
        playlist_id = cls._get_id('playlist', playlist_id_or_url)
        if playlist_id is None:
            raise ValueError(f"Invalid Deezer playlist id or URL: {playlist_id_or_url}")
        return client.get_playlist(playlist_id)

    @classmethod
    def next(cls, paging_object: object) -> Optional[object]:
        """Return the next page object when given a Deezer paging dict or resource.

        The deezer-python client returns paging structures or resource containers with
        a 'next' url; this helper will fetch the next page or return None.
        """
        if not paging_object:
            return None
        next_url = None
        # paging_object may be a dict-like or resource with attribute 'next'
        try:
            next_url = paging_object.get('next') if hasattr(paging_object, 'get') else getattr(paging_object, 'next', None)
        except Exception:
            next_url = None
        if not next_url:
            return None
        client = cls.get_instance()
        # Use the client's get method for arbitrary URLs; return object
        try:
            # deezer.Client.get expects a path like 'playlist/123/tracks' or a full URL
            return client.get(next_url)
        except Exception:
            # Some versions may require different approach; silently return None for starter
            return None

    # Authenticated write operations - these require an access token with proper scopes
    @classmethod
    def create_playlist(cls, user_id: Optional[str], title: str) -> object:
        client = cls.get_instance()
        # deezer.Client.get_user accepts Optional[int] where None denotes current user
        if user_id is None or (isinstance(user_id, str) and user_id.lower() in ("me", "current", "self")):
            user = client.get_user(None)
        else:
            uid = cls._get_id('user', user_id)
            if uid is None:
                raise ValueError(f"Invalid Deezer user id: {user_id}")
            user = client.get_user(uid)
        return user.create_playlist(title)

    @classmethod
    def add_tracks_to_playlist(cls, playlist_id_or_url: str, track_ids: list) -> object:
        playlist_id = cls._get_id('playlist', playlist_id_or_url)
        if playlist_id is None:
            raise ValueError(f"Invalid Deezer playlist id or URL: {playlist_id_or_url}")
        client = cls.get_instance()
        playlist = client.get_playlist(playlist_id)
        return playlist.add_tracks(track_ids)

    @classmethod
    def remove_tracks_from_playlist(cls, playlist_id_or_url: str, track_ids: list) -> object:
        playlist_id = cls._get_id('playlist', playlist_id_or_url)
        if playlist_id is None:
            raise ValueError(f"Invalid Deezer playlist id or URL: {playlist_id_or_url}")
        client = cls.get_instance()
        playlist = client.get_playlist(playlist_id)
        # deezer-python may expose delete_tracks or remove_tracks; try delete_tracks first
        if hasattr(playlist, 'delete_tracks'):
            return playlist.delete_tracks(track_ids)
        if hasattr(playlist, 'remove_tracks'):
            return playlist.remove_tracks(track_ids)
        # If neither exists, return None as a no-op for now
        return None
