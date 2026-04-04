from tracks import Track


class TrackMock(Track):
    @property
    def artists(self) -> list[str]:
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

    @property
    def track_number(self) -> int:
        return self._track_number

    def __eq__(self, other: object) -> bool:
        if other is None or not isinstance(other, self.__class__):
            return False
        return self.track_id == other.track_id

    def __hash__(self) -> int:
        return hash(self._id)

    def __init__(self, track_id: str, artists: list[str], album: str, title: str, duration: float, track_number: int) -> None:
        self._id = track_id
        self._artists = artists
        self._album = album
        self._title = title
        self._duration = duration
        self._track_number = track_number