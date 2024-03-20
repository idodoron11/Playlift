from typing import List

from tracks import Track


class TrackMock(Track):
    @property
    def artists(self) -> List[str]:
        return self._artists

    @property
    def title(self) -> str:
        return self._title

    @property
    def album(self) -> str:
        return self._album

    @property
    def duration(self) -> float:
        return self._duration

    @property
    def track_id(self) -> str:
        return self._id

    def __eq__(self, other):
        if other is None or not isinstance(other, self.__class__):
            return False
        return self.track_id == other.track_id

    def __hash__(self):
        return hash(self._id)

    def __init__(self, track_id, artists, album, title, duration):
        self._id = track_id
        self._artists = artists
        self._album = album
        self._title = title
        self._duration = duration
        