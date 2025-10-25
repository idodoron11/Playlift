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
    def title(self):
        self._ensure_data()
        return self._get_attribute(self._data, 'title')

    @property
    def artist(self):
        self._ensure_data()
        artist = self._get_attribute(self._data, 'artist')
        return self._get_attribute(artist, 'name') if artist else None

    @property
    def album(self):
        self._ensure_data()
        album = self._get_attribute(self._data, 'album')
        return self._get_attribute(album, 'title') if album else None

    @property
    def duration(self):
        self._ensure_data()
        return self._get_attribute(self._data, 'duration')

    def __str__(self):
        return self.track_id

    def __repr__(self):
        return f"<DeezerTrack {self.track_id}>"
