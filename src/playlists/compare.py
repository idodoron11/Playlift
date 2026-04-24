from __future__ import annotations

from typing import TYPE_CHECKING

from api.spotify import get_spotify_client
from playlists import CompareResult
from playlists.local_playlist import LocalPlaylist
from playlists.spotify_playlist import SpotifyPlaylist

if TYPE_CHECKING:
    from playlists.path_mapper import PathMapper
    from tracks.local_track import LocalTrack
    from tracks.spotify_track import SpotifyTrack


def compare_playlists(
    local_playlist_path: str,
    spotify_playlist_id_or_url: str,
    path_mapper: PathMapper | None = None,
) -> CompareResult[LocalTrack, SpotifyTrack]:
    """Compare a local m3u playlist with a Spotify playlist.

    Returns a CompareResult where:
      - source_only contains LocalTrack instances that are in the local
        playlist but not present on the Spotify playlist (based on spotify_id)
      - target_only contains SpotifyTrack instances that are in the
        Spotify playlist but not referenced by any local track's spotify_ref.

    Notes:
      - A local track whose spotify_ref is missing or the special value "SKIP"
        is considered source-only.
      - Comparison is performed by normalizing the local track's spotify_ref
        into a spotify id (property `LocalTrack.spotify_id`) and comparing that
        id to `SpotifyTrack.track_id`.
    """
    local_playlist = LocalPlaylist(local_playlist_path, path_mapper=path_mapper)
    spotify_playlist = SpotifyPlaylist(spotify_playlist_id_or_url, client=get_spotify_client())

    # Build a set/map of spotify ids referenced by local tracks
    local_id_set: set[str] = set()
    local_map: dict[str | None, list[LocalTrack]] = {}  # spotify_id -> list[LocalTrack]
    for lt in local_playlist.tracks:
        sid = getattr(lt, "spotify_id", None)
        # sid will be None for missing/"SKIP" tags
        local_map.setdefault(sid, []).append(lt)
        if sid:
            local_id_set.add(sid)

    # Build a map of spotify playlist tracks
    spotify_map: dict[str, SpotifyTrack] = {}  # spotify_id -> SpotifyTrack
    for st in spotify_playlist.tracks:
        if st is None:
            continue
        spotify_map[st.track_id] = st

    # source-only: any local track with no spotify id or an id not found on Spotify
    source_only: list[LocalTrack] = []
    for sid, ltracks in local_map.items():
        if sid is None or sid not in spotify_map:
            source_only.extend(ltracks)

    # target-only: any spotify id not referenced by local tracks
    target_only: list[SpotifyTrack] = [t for id_, t in spotify_map.items() if id_ not in local_id_set]

    return CompareResult(source_only=source_only, target_only=target_only)
