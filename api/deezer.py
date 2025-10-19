from config import CONFIG
import deezer
from typing import Optional, Any


class DeezerAPI:
    """Simple Deezer API wrapper using deezer-python Client.

    This is a starter implementation that mirrors the SpotifyAPI pattern in this
    project. It provides a singleton client and a few helper methods we'll need
    when integrating playlists and tracks.

    Notes / assumptions:
    - The project `pyproject.toml` includes `deezer-python==7.2.0` (import name `deezer`).
    - OAuth flow is not implemented here; this wrapper expects an access token in
      `CONFIG.deezer_access_token` for authenticated actions. If you need OAuth
      authorization code flow, we can add helper methods later.
    """

    __instance: Optional[deezer.Client] = None

    @classmethod
    def get_instance(cls) -> deezer.Client:
        """Return a singleton deezer.Client instance.

        If an access token is present in `CONFIG.deezer_access_token`, the client
        will be constructed with it to allow privileged operations (create playlist,
        add tracks). Otherwise a public client is returned for read-only calls.
        """
        if cls.__instance is None:
            token = getattr(CONFIG, "deezer_access_token", None)
            if token:
                cls.__instance = deezer.Client(access_token=token)
            else:
                cls.__instance = deezer.Client()
        return cls.__instance

    def __init__(self):
        raise TypeError("An instance of this class already exists")

    # Helper to normalize ids/urls used elsewhere in the codebase
    @staticmethod
    def _get_id(url_or_id: Optional[str]) -> Optional[int]:
        """Extract a Deezer numeric id from a url or return the id as int.

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
        # Try to extract trailing numeric id from typical Deezer URLs
        parts = url_or_id.rstrip("/\n ").split("/")
        if parts and parts[-1].isdigit():
            return int(parts[-1])
        # No numeric id found
        return None
