"""deezer_compare — compare a local playlist against a Deezer playlist."""

from __future__ import annotations

from typing import TYPE_CHECKING

from playlists import CompareResult
from tracks.deezer_track import extract_deezer_track_id

if TYPE_CHECKING:
    from playlists.deezer_playlist import DeezerPlaylist
    from playlists.local_library import LocalLibrary
    from playlists.local_playlist import LocalPlaylist
    from tracks import Track
    from tracks.deezer_track import DeezerTrack


def compare_deezer_playlists(
    source_playlist: LocalPlaylist | LocalLibrary,
    deezer_playlist: DeezerPlaylist,
) -> CompareResult[Track, DeezerTrack]:
    """Compare *source_playlist* against *deezer_playlist* using ``TXXX:DEEZER`` permalinks.

    Tracks are identified by their canonical Deezer permalink.  A source track is
    considered matched when its ``service_ref("DEEZER")`` equals the canonical URL
    of a track in the Deezer playlist.

    The source must be a local playlist — only ``LocalTrack`` objects carry
    embedded ``TXXX:DEEZER`` tags.  Passing a service playlist (e.g.
    ``SpotifyPlaylist``) would yield no matches.

    Args:
        source_playlist: Local playlist whose tracks carry ``TXXX:DEEZER`` tags.
        deezer_playlist: The Deezer playlist to compare against.

    Returns:
        A ``CompareResult`` with ``source_only`` and ``target_only`` lists.
    """
    # Build a set of Deezer track IDs referenced by source tracks
    local_id_set: set[str] = set()
    for lt in source_playlist.tracks:
        ref = lt.service_ref("DEEZER")
        if ref and ref != "SKIP":
            track_id = extract_deezer_track_id(ref)
            if track_id:
                local_id_set.add(track_id)

    # Build a map of Deezer playlist track IDs
    deezer_map: dict[str, DeezerTrack] = {dt.track_id: dt for dt in deezer_playlist.tracks}

    # source_only: source tracks whose Deezer ref is not in the Deezer playlist
    source_only: list[Track] = []
    for lt in source_playlist.tracks:
        ref = lt.service_ref("DEEZER")
        matched = False
        if ref and ref != "SKIP":
            track_id = extract_deezer_track_id(ref)
            if track_id and track_id in deezer_map:
                matched = True
        if not matched:
            source_only.append(lt)

    # target_only: Deezer playlist tracks not referenced by source tracks
    target_only: list[DeezerTrack] = [t for tid, t in deezer_map.items() if tid not in local_id_set]

    return CompareResult(source_only=source_only, target_only=target_only)
