"""DeezerPlaylist — manages a live Deezer user playlist."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from matchers.deezer_matcher import DeezerMatcher
from playlists import Playlist, SyncTarget, TrackCollection
from tracks.deezer_track import DeezerTrack

if TYPE_CHECKING:
    from collections.abc import Iterable

    from deezer import Deezer  # type: ignore[import-untyped]

    from tracks import Track


class DeezerPlaylist(Playlist, SyncTarget):
    """Represents a single Deezer user playlist.

    Mutations (add/remove) invalidate the internal ``_tracks`` cache so
    subsequent ``tracks`` reads always reflect the current server state.
    """

    def __init__(self, playlist_id: str, *, deezer: Deezer) -> None:  # type: ignore[no-any-unimported]
        self._playlist_id: str = str(playlist_id)
        self._deezer = deezer
        self._tracks: list[DeezerTrack] | None = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def playlist_id(self) -> str:
        return self._playlist_id

    @property
    def tracks(self) -> list[DeezerTrack]:
        if self._tracks is None:
            raw: list[dict[str, Any]] = self._deezer.gw.get_playlist_tracks(self._playlist_id)
            self._tracks = [DeezerTrack(t) for t in raw]
        return self._tracks

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def add_tracks(self, tracks: list[Track]) -> None:  # type: ignore[override]  # narrowed arg type is safe at runtime
        seen: set[str] = {t.track_id for t in self.tracks}  # pre-populate with existing
        new_tracks: list[Track] = []
        for t in tracks:
            if t.track_id not in seen:
                new_tracks.append(t)
                seen.add(t.track_id)
        if not new_tracks:
            return
        ids = [t.track_id for t in new_tracks]
        self._deezer.gw.add_songs_to_playlist(self._playlist_id, ids)
        self._tracks = None  # invalidate cache

    def remove_track(self, tracks: list[Track]) -> None:
        ids_to_remove: set[str] = {t.track_id for t in tracks}
        self._deezer.gw.remove_songs_from_playlist(self._playlist_id, list(ids_to_remove))
        if self._tracks is not None:
            self._tracks = [t for t in self._tracks if t.track_id not in ids_to_remove]

    def sync_tracks(
        self,
        source_tracks: Iterable[Track],
        autopilot: bool = False,
        embed_matches: bool = False,
        sort_tracks: bool = False,
    ) -> None:
        """Sync the Deezer playlist to match *source_tracks*.

        Adds tracks that are missing on Deezer and removes tracks that are no
        longer in the source.  Optionally reorders to match source order.
        """
        resolved = self.track_matcher().match_list(source_tracks, autopilot=autopilot, embed_matches=embed_matches)
        resolved_ids: set[str] = {t.track_id for t in resolved}

        current = list(self.tracks)
        current_ids: set[str] = {t.track_id for t in current}

        to_add = [t for t in resolved if t.track_id not in current_ids]
        to_remove = [t for t in current if t.track_id not in resolved_ids]

        if to_remove:
            self.remove_track(to_remove)  # type: ignore[arg-type]  # list[DeezerTrack] not covariant with list[Track]
        if to_add:
            self.add_tracks(to_add)

        if sort_tracks and resolved:
            sorted_resolved = sorted(resolved, key=lambda t: t.track_id)
            self.remove_track(list(self.tracks))
            self.add_tracks(sorted_resolved)

    def import_tracks(self, tracks: Iterable[Track], autopilot: bool = False, embed_matches: bool = False) -> None:
        """Resolve *tracks* via DeezerMatcher and add them to this playlist."""
        deezer_tracks = self.track_matcher().match_list(tracks, autopilot=autopilot, embed_matches=embed_matches)
        self.add_tracks(deezer_tracks)

    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------

    @classmethod
    def create(cls, name: str, public: bool = False, *, deezer: Deezer) -> DeezerPlaylist:  # type: ignore[no-any-unimported]
        """Create a new Deezer playlist and return a ``DeezerPlaylist`` instance."""
        status = 0 if public else 1
        playlist_id = str(deezer.gw.create_playlist(name, status=status))
        return cls(playlist_id, deezer=deezer)

    @classmethod
    def create_from_another_playlist(  # type: ignore[no-any-unimported]
        cls,
        name: str,
        source: TrackCollection,
        public: bool = False,
        *,
        deezer: Deezer,
        autopilot: bool = False,
        embed_matches: bool = False,
    ) -> DeezerPlaylist:
        """Create a new Deezer playlist and populate it from *source*.

        This is the highest-level import facade called by the ``deezer import``
        CLI command.
        """
        new_playlist = cls.create(name, public=public, deezer=deezer)
        new_playlist.import_tracks(source.tracks, autopilot=autopilot, embed_matches=embed_matches)
        return new_playlist

    # ------------------------------------------------------------------
    # SyncTarget
    # ------------------------------------------------------------------

    @staticmethod
    def track_matcher() -> DeezerMatcher:
        return DeezerMatcher.get_instance()
