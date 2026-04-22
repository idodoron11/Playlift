# Contract: `EmbeddableTrack`

**File**: `tracks/__init__.py`  
**Kind**: Abstract Base Class (ABC)  
**Extends**: `ABC` (orthogonal to `Track`)

## Purpose

A single-method write contract for tracks that can persist match data from streaming services into durable storage (audio file tags). This contract is **orthogonal** to `Track` — not all tracks are embeddable. Only local audio tracks implement it. Streaming service tracks (`SpotifyTrack`) do NOT.

Note: reading a stored service reference (`service_ref`) is a query on **any** `Track` via its concrete default method — it is not part of this contract.

## Abstract Interface

```python
class EmbeddableTrack(ABC):

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
```

## Invariants

- `embed_match` MUST be idempotent — calling it twice with the same `match` produces at most one write per tag
- `embed_match` MUST only write the `match.service_name` service tag; it MUST NOT alter tags for other services
- The matched track's ISRC is authoritative — if it differs from the stored value, `embed_match` MUST overwrite it
- If `match.isrc` is `None`, the ISRC tag MUST be left unchanged

## Known Implementations

| Class | `embed_match` |
|-------|---------------|
| `LocalTrack` | writes permalink + ISRC when changed |

## Extension Guide

To make a hypothetical `CachedLocalTrack` embeddable:
```python
class CachedLocalTrack(Track, EmbeddableTrack):
    # service_ref is inherited from Track (returns None by default)
    # Override it to read from the cache:
    def service_ref(self, service_name: str) -> str | None:
        return self._cache.get(service_name)

    def embed_match(self, match: ServiceTrack) -> None:
        if self.service_ref(match.service_name) != match.permalink:
            self._cache[match.service_name] = match.permalink
        # ... ISRC handling
```
No changes to `Matcher`, `SpotifyMatcher`, or `LocalTrack` are required.
