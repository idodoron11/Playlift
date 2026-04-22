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

    def service_ref(self, service_name: str) -> str | None:
        """Return any stored reference for the given streaming service.

        Returns None by default. Concrete subclasses (e.g. LocalTrack) override
        this to read from durable storage such as audio file tags.

        Args:
            service_name: Uppercased service identifier (e.g. "SPOTIFY").

        Returns:
            The stored service reference string, or None if absent.
        """
        return None

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


class ServiceTrack(Track, ABC):
    """A track hosted on a remote streaming service.

    Extends Track with a canonical URL and a stable service identifier.
    Only concrete streaming service track types (e.g. SpotifyTrack) implement
    this contract. LocalTrack does NOT.
    """

    @property
    @abstractmethod
    def permalink(self) -> str:
        """Canonical URL for this track on its streaming service.

        Returns:
            A non-empty URL string (e.g. 'https://open.spotify.com/track/abc123').
        """
        ...

    @property
    @abstractmethod
    def service_name(self) -> str:
        """Stable uppercased identifier for the streaming service.

        Used as the ID3 custom tag key when storing a service reference
        in a local audio file (e.g. 'SPOTIFY', 'DEEZER').

        Returns:
            A non-empty uppercased string.
        """
        ...


class EmbeddableTrack(ABC):
    """Write contract for tracks that persist match data into durable storage.

    Orthogonal to Track — not all tracks are embeddable. Only local audio
    tracks implement it. Streaming service tracks (SpotifyTrack) do NOT.
    """

    @abstractmethod
    def embed_match(self, match: ServiceTrack) -> None:
        """Persist match data from a streaming service track into this track's storage.

        Writes the service reference (match.permalink) under the service's tag key
        (match.service_name) and updates the ISRC if the matched track carries one
        that differs from the currently stored value.

        Only writes tags that have changed — the operation is idempotent.
        Only the tag for match.service_name is affected; other service tags are unchanged.

        Args:
            match: The streaming service track whose data should be embedded.
        """
        ...
