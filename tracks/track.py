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
    def duration(self) -> int:
        pass
