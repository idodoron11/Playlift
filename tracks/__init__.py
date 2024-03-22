"""Tracks"""
import json
from abc import ABC, abstractmethod
from typing import List


class Track(ABC):
    @property
    @abstractmethod
    def artists(self) -> List[str]:
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

    def __eq__(self, other):
        if other is None:
            return False
        if self is other:
            return True
        if not isinstance(other, self.__class__):
            return False
        return self.track_id == other.track_id

    def __hash__(self):
        return hash(self.track_id)

    def __repr__(self):
        json_object = {
            'title': self.title,
            'artist': self.display_artist,
            'album': self.album,
            'track number': self.track_number,
            'duration': self.duration
        }
        return json.dumps(json_object, indent=2)
