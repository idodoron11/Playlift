from __future__ import annotations

from typing import List, Optional
from api.deezer import DeezerAPI
from tracks import Track


class DeezerTrack(Track):
    def __init__(self, track_url: str, data: Optional[object] = None):
        # Use the static helper to extract numeric id without creating an authenticated client
        self._id: Optional[int] = DeezerAPI._get_id('track', track_url)
        if self._id is None:
            raise ValueError(f"Invalid Deezer track id or URL: {track_url}")
        self._data = data
        if self._data is not None:
            # Normalize id from provided data and validate match when possible
            data_id = None
            if isinstance(self._data, dict):
                data_id = self._data.get('id')
            else:
                data_id = getattr(self._data, 'id', None)
            if data_id is not None and int(data_id) != int(self._id):
                raise ValueError("The data object does not match the track id")

    @property
    def data(self) -> dict:
        if not self._data:
            # Ensure we don't trigger interactive OAuth by creating a non-auth client first
            DeezerAPI.get_instance(auto_authorize=False)
            self._data = DeezerAPI.track(self._id)
        return self._data

    @property
    def artists(self) -> List[str]:
        d = self.data
        # Deezer track resources typically have 'artist' (single) or 'contributors' (list)
        if isinstance(d, dict):
            if 'contributors' in d and isinstance(d['contributors'], list):
                return [c.get('name') for c in d['contributors'] if c and 'name' in c]
            if 'artists' in d and isinstance(d['artists'], list):
                return [a.get('name') for a in d['artists'] if a and 'name' in a]
            if 'artist' in d and isinstance(d['artist'], dict):
                name = d['artist'].get('name')
                return [name] if name else []
        # Fallback: empty list
        return []

    @property
    def title(self) -> str:
        d = self.data
        # Deezer uses 'title'
        if isinstance(d, dict):
            return d.get('title') or d.get('name') or ''
        return ''

    @property
    def album(self) -> str:
        d = self.data
        if isinstance(d, dict):
            album = d.get('album')
            if isinstance(album, dict):
                return album.get('title') or album.get('name') or ''
        return ''

    @property
    def duration(self) -> float:
        d = self.data
        if isinstance(d, dict):
            # Deezer duration is in seconds
            if 'duration' in d and d['duration'] is not None:
                try:
                    return float(d['duration'])
                except Exception:
                    pass
            # Fallback: maybe duration_ms
            if 'duration_ms' in d and d['duration_ms'] is not None:
                try:
                    return float(d['duration_ms']) / 1000.0
                except Exception:
                    pass
        return 0.0

    @property
    def track_id(self) -> str:
        return str(self._id)

    @property
    def track_url(self) -> str:
        return f"https://www.deezer.com/track/{self.track_id}"

    @property
    def track_number(self) -> int:
        d = self.data
        if isinstance(d, dict):
            # Deezer may use 'track_position' or 'track_number'
            if 'track_position' in d and d['track_position'] is not None:
                try:
                    return int(d['track_position'])
                except Exception:
                    pass
            if 'track_number' in d and d['track_number'] is not None:
                try:
                    return int(d['track_number'])
                except Exception:
                    pass
            # Album track info sometimes under 'track_position' in album
            album = d.get('album')
            if isinstance(album, dict) and 'track_position' in album and album['track_position'] is not None:
                try:
                    return int(album['track_position'])
                except Exception:
                    pass
        return 0

