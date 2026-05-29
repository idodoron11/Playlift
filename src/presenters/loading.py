"""Presenter helper for the playlist-loading workflow."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playlists import TrackCollection
    from playlists.path_mapper import PathMapper
    from playlists.playlist_factory import PlaylistFactory
    from views.playlist_load_view import IPlaylistLoadView


def resolve_source(
    factory: PlaylistFactory,
    view: IPlaylistLoadView,
    source: str,
    path_mapper: PathMapper | None = None,
) -> TrackCollection:
    """Resolve *source* to a TrackCollection and report progress through *view*.

    Drives the playlist-loading workflow: delegates to *factory* with
    ``view.begin_loading`` and ``view.on_track_loaded`` wired as callbacks,
    then calls ``view.end_loading()`` once construction completes.

    Domain exceptions (``InvalidPathMappingError``, ``UnrecognisedSourceError``)
    propagate to the caller unchanged; ``end_loading`` is not called in that
    case because loading never began.

    Args:
        factory: The ``PlaylistFactory`` that constructs the playlist.
        view: View interface used to report loading progress.
        source: Local path, Spotify URI/URL, or Deezer playlist URL.
        path_mapper: Optional path mapper for local file paths.

    Returns:
        The resolved ``TrackCollection``.
    """
    playlist = factory.resolve(
        source,
        path_mapper=path_mapper,
        on_loading_started=view.begin_loading,
        on_track_loaded=view.on_track_loaded,
    )
    view.end_loading()
    return playlist
