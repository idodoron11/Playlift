"""Tracks"""

import json
from abc import ABC, abstractmethod


class Track(ABC):
    @property
    @abstractmethod
    def artists(self) -> list[str]:
        pass

    @property
    @abstractmethod
    def title(self) -> str:
        pass

    @property
    @abstractmethod
    def album(self) -> str:
        pass

    @property
    @abstractmethod
    def duration(self) -> float:
        pass

    @property
    def display_artist(self) -> str:
        return ", ".join(self.artists)

    @property
    @abstractmethod
    def track_id(self) -> str:
        pass

    @property
    @abstractmethod
    def track_number(self) -> int:
        pass

    @property
    @abstractmethod
    def isrc(self) -> str | None:
        pass

    def __eq__(self, other: object) -> bool:
        if other is None:
            return False
        if self is other:
            return True
        if not isinstance(other, self.__class__):
            return False
        return self.track_id == other.track_id

    def __hash__(self) -> int:
        return hash(self.track_id)

    def __repr__(self) -> str:
        json_object = {
            "track id": self.track_id,
            "title": self.title,
            "artist": self.display_artist,
            "album": self.album,
            "track number": self.track_number,
            "duration": self.duration,
        }
        return json.dumps(json_object, indent=2, ensure_ascii=False)
