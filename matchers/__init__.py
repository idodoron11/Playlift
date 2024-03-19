from abc import ABC, abstractmethod
from typing import Iterable, Optional

from tracks import Track


class Matcher(ABC):
    __instance = None

    def __init__(self):
        if Matcher.__instance is not None:
            raise TypeError("An instance of this class already exists")

    @classmethod
    def get_instance(cls):
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    @abstractmethod
    def match(self, track: Track) -> Optional[Track]:
        """
        :param track: track instance, of type A
        :return: track instance, of type B, that matches the input track
        """
        pass

    @abstractmethod
    def suggest_match(self, track: Track) -> Iterable[Track]:
        """
        :param track: track instance, of type A
        :return: a collection of tracks, of type B, that may match the input track
        """
        pass
