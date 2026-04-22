from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import spotipy

from tracks import ServiceTrack


class SpotifyTrack(ServiceTrack):
    service_name: str = "SPOTIFY"  # class-level constant; satisfies ServiceTrack.service_name

    def __init__(  # type: ignore[no-any-unimported]  # spotipy ships no type stubs
        self, track_url: str, data: dict[str, Any] | None = None, *, client: spotipy.Spotify | None = None
    ):
        if client is None:
            raise ValueError("client must be provided")
        self._client = client
        self._id = self._client._get_id("track", track_url)
        self._data: dict[str, Any] | None = data
        if self._data and self._data["id"] != self._id:
            raise ValueError("The data object does not match the track id")

    @property
    def data(self) -> dict[str, Any]:
        if not self._data:
            self._data = self._client.track(self._id)
        return self._data

    @property
    def artists(self) -> list[str]:
        return [str(item["name"]) for item in self.data["artists"]]

    @property
    def title(self) -> str:
        return str(self.data["name"])

    @property
    def album(self) -> str:
        return str(self.data["album"]["name"])

    @property
    def duration(self) -> float:
        duration_ms = self.data["duration_ms"]
        return float(duration_ms) / 1000

    @property
    def track_id(self) -> str:
        return str(self._id)

    @property
    def track_url(self) -> str:
        return f"https://open.spotify.com/track/{self.track_id}"

    @property
    def permalink(self) -> str:
        """Canonical URL for this track on Spotify.

        Returns:
            A non-empty URL string (e.g. 'https://open.spotify.com/track/abc123').
        """
        return self.track_url

    @property
    def track_number(self) -> int:
        return int(self.data["track_number"])

    @property
    def isrc(self) -> str | None:
        """Return the ISRC from Spotify's external_ids, or None if absent."""
        result: str | None = self.data.get("external_ids", {}).get("isrc")
        return result
