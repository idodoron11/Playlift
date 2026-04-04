from typing import List, Optional, Tuple

from playlists.local_playlist import LocalPlaylist
from playlists.path_mapper import PathMapper
from playlists.spotify_playlist import SpotifyPlaylist
from tracks.local_track import LocalTrack
from tracks.spotify_track import SpotifyTrack


def compare_playlists(local_playlist_path: str, spotify_playlist_id_or_url: str, path_mapper: Optional[PathMapper] = None) -> Tuple[List[LocalTrack], List[SpotifyTrack]]:
    """Compare a local m3u playlist with a Spotify playlist.

    Returns a tuple (local_only, spotify_only) where:
      - local_only is a list of LocalTrack instances that are in the local
        playlist but not present on the Spotify playlist (based on spotify_id)
      - spotify_only is a list of SpotifyTrack instances that are in the
        Spotify playlist but not referenced by any local track's spotify_ref.

    Notes:
      - A local track whose spotify_ref is missing or the special value "SKIP"
        is considered local-only.
      - Comparison is performed by normalizing the local track's spotify_ref
        into a spotify id (property `LocalTrack.spotify_id`) and comparing that
        id to `SpotifyTrack.track_id`.
    """
    local_playlist = LocalPlaylist(local_playlist_path, path_mapper=path_mapper)
    spotify_playlist = SpotifyPlaylist(spotify_playlist_id_or_url)

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
    spotify_map = dict()  # spotify_id -> SpotifyTrack
    for st in spotify_playlist.tracks:
        if st is None:
            continue
        spotify_map[st.track_id] = st

    # Local-only: any local track with no spotify id or an id not found on Spotify
    local_only: List[LocalTrack] = []
    for sid, ltracks in local_map.items():
        if sid is None or sid not in spotify_map:
            local_only.extend(ltracks)

    # Spotify-only: any spotify id not referenced by local tracks
    spotify_only: List[SpotifyTrack] = [t for id_, t in spotify_map.items() if id_ not in local_id_set]

    return local_only, spotify_only

