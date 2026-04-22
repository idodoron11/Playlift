# Contract: `ServiceTrack`

**File**: `tracks/__init__.py`  
**Kind**: Abstract Base Class (ABC)  
**Extends**: `Track`, `ABC`

## Purpose

Represents a track from a remote streaming service. Extends `Track` with two properties that identify the track on its service. Only concrete streaming service track types (e.g. `SpotifyTrack`) implement this contract. `LocalTrack` and `TrackMock` do NOT.

## Abstract Interface

```python
class ServiceTrack(Track, ABC):

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
```

## Invariants

- `permalink` MUST return a non-empty string; it MUST NOT return `None`
- `service_name` MUST be uppercased, stable across calls, and non-empty
- Every class that implements `ServiceTrack` MUST override both properties

## Known Implementations

| Class | `permalink` | `service_name` |
|-------|-------------|----------------|
| `SpotifyTrack` | `self.track_url` (`https://open.spotify.com/track/{id}`) | `"SPOTIFY"` |

## Extension Guide

To add Deezer support:
```python
class DeezerTrack(ServiceTrack):
    @property
    def permalink(self) -> str:
        return f"https://www.deezer.com/track/{self._id}"

    @property
    def service_name(self) -> str:
        return "DEEZER"
```
No changes to any other existing class are required.
