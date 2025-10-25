import deezer

class DeezerTrack:
    def __init__(self, track_id):
        self.track_id = str(track_id)
        self._data = None
        self._client = None

    def _client_instance(self):
        if self._client is None:
            self._client = deezer.Client()
        return self._client

    def _ensure_data(self):
        if self._data is None:
            client = self._client_instance()
            self._data = client.get_track(self.track_id)

    @property
    def title(self):
        self._ensure_data()
        return self._data.title

    @property
    def artist(self):
        self._ensure_data()
        return self._data.artist.name

    @property
    def album(self):
        self._ensure_data()
        return self._data.album.title

    @property
    def duration(self):
        self._ensure_data()
        return self._data.duration

    def __str__(self):
        return self.track_id

    def __repr__(self):
        return f"<DeezerTrack {self.track_id}>"
