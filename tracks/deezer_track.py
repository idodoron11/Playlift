from typing import Optional, Any
import deezer

class DeezerTrack:
    def __init__(self, track_id: str | int) -> None:
        self.track_id = str(track_id)
        self._data: Optional[Any] = None
        self._client: Optional[deezer.Client] = None

    def _client_instance(self) -> deezer.Client:
        if self._client is None:
            self._client = deezer.Client()
        return self._client

    def _ensure_data(self) -> None:
        if self._data is None:
            client = self._client_instance()
            self._data = client.get_track(self.track_id)

    @property
    def title(self) -> str:
        self._ensure_data()
        return self._data.title

    @property
    def artist(self) -> str:
        self._ensure_data()
        return self._data.artist.name

    @property
    def album(self) -> str:
        self._ensure_data()
        return self._data.album.title

    @property
    def duration(self) -> int:
        self._ensure_data()
        return self._data.duration

    def __str__(self) -> str:
        return self.track_id

    def __repr__(self) -> str:
        return f"<DeezerTrack {self.track_id}>"
