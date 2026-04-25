from __future__ import annotations

import os

import click

from api.deezer import DeezerAuthenticationError, get_deezer_client
from api.spotify import get_spotify_client
from playlists.compare import compare_playlists
from playlists.deezer_compare import compare_deezer_playlists
from playlists.deezer_playlist import DeezerPlaylist
from playlists.local_library import LocalLibrary
from playlists.local_playlist import LocalPlaylist
from playlists.path_mapper import PathMapper
from playlists.spotify_playlist import SpotifyPlaylist
from tracks.deezer_track import is_valid_deezer_url, normalise_deezer_url
from tracks.local_track import LocalTrack


@click.group()
def cli() -> None:
    pass


@cli.group("spotify")
def cli_spotify() -> None:
    pass


@cli_spotify.command("import")
@click.option("--source", "-s", required=True, multiple=True, help="Source playlist path")
@click.option("--destination", "-d", required=True, multiple=True, help="Destination playlist name")
@click.option("--autopilot", is_flag=True, help="When multiple matches are found, choose the first one")
@click.option("--embed-matches", is_flag=True, help="Embed a reference to the matched track in the source track")
@click.option("--public", is_flag=True, help="Create a public playlist (default is private)")
@click.option("--from-path", default=None, help="Source path prefix for remapping (requires --to-path)")
@click.option("--to-path", default=None, help="Destination path prefix for remapping (requires --from-path)")
def cli_spotify_import(
    source: tuple[str, ...],
    destination: tuple[str, ...],
    autopilot: bool = False,
    embed_matches: bool = False,
    public: bool = False,
    from_path: str | None = None,
    to_path: str | None = None,
) -> None:
    if len(source) != len(destination):
        raise click.BadParameter("Number of sources must match the number of destinations")

    # Create path mapper if both from_path and to_path are provided
    path_mapper = None
    if from_path and to_path:
        path_mapper = PathMapper(from_path, to_path)
    elif from_path or to_path:
        raise click.BadParameter("Both --from-path and --to-path must be provided together")

    inputs = zip(source, destination, strict=True)
    for src, dst in inputs:
        playlist = get_playlist(src, path_mapper=path_mapper)
        SpotifyPlaylist.create_from_another_playlist(
            dst, playlist, autopilot=autopilot, embed_matches=embed_matches, public=public, client=get_spotify_client()
        )


@cli_spotify.command("sync")
@click.option("--source", "-s", required=True, help="Source playlist path")
@click.option("--destination", "-d", required=True, help="Destination playlist ID")
@click.option("--autopilot", is_flag=True, help="When multiple matches are found, choose the first one")
@click.option("--embed-matches", is_flag=True, help="Embed a reference to the matched track in the source track")
@click.option("--sort-tracks", is_flag=True, help="Sort tracks alphabetically")
@click.option("--from-path", default=None, help="Source path prefix for remapping (requires --to-path)")
@click.option("--to-path", default=None, help="Destination path prefix for remapping (requires --from-path)")
def cli_spotify_sync(
    destination: str,
    source: str,
    autopilot: bool = False,
    embed_matches: bool = False,
    sort_tracks: bool = False,
    from_path: str | None = None,
    to_path: str | None = None,
) -> None:
    # Create path mapper if both from_path and to_path are provided
    path_mapper = None
    if from_path and to_path:
        path_mapper = PathMapper(from_path, to_path)
    elif from_path or to_path:
        raise click.BadParameter("Both --from-path and --to-path must be provided together")

    source_playlist = get_playlist(source, path_mapper=path_mapper)
    destination_playlist = SpotifyPlaylist(destination, client=get_spotify_client())
    destination_playlist.clear()
    if sort_tracks:
        sorted_tracks = sorted(source_playlist.tracks, key=lambda track: track.track_id)
        destination_playlist.import_tracks(sorted_tracks, autopilot=autopilot, embed_matches=embed_matches)
    else:
        destination_playlist.import_tracks(source_playlist.tracks, autopilot=autopilot, embed_matches=embed_matches)


@cli_spotify.command("duplicates")
@click.option("--source", "-s", required=True, help="Source playlist path")
def cli_spotify_duplicates(source: str) -> None:
    source_playlist = get_playlist(source)
    tracks_map: dict[str | None, list[LocalTrack]] = {}
    for track in source_playlist.tracks:
        if not isinstance(track, LocalTrack):
            continue
        track_id = track.spotify_ref
        if track_id not in tracks_map:
            tracks_map[track_id] = []
        tracks_map[track_id].append(track)
    for track_id, dupes in tracks_map.items():
        if len(dupes) == 1:
            continue
        print(f"{track_id}: {len(dupes)}")
        for t in dupes:
            print(t.track_id)


@cli_spotify.command("match")
@click.option("--source", "-s", required=True, multiple=True, help="Source playlist path")
@click.option("--autopilot", is_flag=True, help="When multiple matches are found, choose the first one")
@click.option("--from-path", default=None, help="Source path prefix for remapping (requires --to-path)")
@click.option("--to-path", default=None, help="Destination path prefix for remapping (requires --from-path)")
def cli_spotify_match(
    source: tuple[str, ...],
    autopilot: bool = False,
    from_path: str | None = None,
    to_path: str | None = None,
) -> None:
    # Create path mapper if both from_path and to_path are provided
    path_mapper = None
    if from_path and to_path:
        path_mapper = PathMapper(from_path, to_path)
    elif from_path or to_path:
        raise click.BadParameter("Both --from-path and --to-path must be provided together")

    for src in source:
        playlist = get_playlist(src, path_mapper=path_mapper)
        SpotifyPlaylist.track_matcher().match_list(playlist.tracks, autopilot=autopilot, embed_matches=True)


@cli_spotify.command("compare")
@click.option("--source", "-s", required=True, help="Source local playlist path (m3u)")
@click.option("--destination", "-d", required=True, help="Destination Spotify playlist id or URL")
@click.option("--from-path", default=None, help="Source path prefix for remapping (requires --to-path)")
@click.option("--to-path", default=None, help="Destination path prefix for remapping (requires --from-path)")
def cli_spotify_compare(
    source: str,
    destination: str,
    from_path: str | None = None,
    to_path: str | None = None,
) -> None:
    """Compare a local m3u playlist with a Spotify playlist and print differences."""
    # Create path mapper if both from_path and to_path are provided
    path_mapper = None
    if from_path and to_path:
        path_mapper = PathMapper(from_path, to_path)
    elif from_path or to_path:
        raise click.BadParameter("Both --from-path and --to-path must be provided together")

    result = compare_playlists(source, destination, path_mapper=path_mapper)

    print(f"Local-only tracks: {len(result.source_only)}")
    if len(result.source_only) > 0:
        for idx, local_track in enumerate(result.source_only, start=1):
            spotify_ref = local_track.spotify_ref if local_track.spotify_ref is not None else "(none)"
            print(f"{idx}. {local_track.file_path}  | spotify_ref: {spotify_ref}")

    print("")
    print(f"Spotify-only tracks: {len(result.target_only)}")
    if len(result.target_only) > 0:
        for idx, spotify_track in enumerate(result.target_only, start=1):
            artists = ", ".join(spotify_track.artists) if spotify_track.artists else ""
            title = spotify_track.title or "(unknown title)"
            print(f"{idx}. {spotify_track.track_url}  | {title} — {artists}")


def get_playlist(source: str, path_mapper: PathMapper | None = None) -> LocalPlaylist | LocalLibrary:
    if os.path.isdir(source):
        return LocalLibrary(source)
    if os.path.isfile(source):
        return LocalPlaylist(source, path_mapper=path_mapper)
    raise ValueError("Invalid source path")


def _build_path_mapper(from_path: str | None, to_path: str | None) -> PathMapper | None:
    if from_path and to_path:
        return PathMapper(from_path, to_path)
    if from_path or to_path:
        raise click.BadParameter("Both --from-path and --to-path must be provided together")
    return None


# ---------------------------------------------------------------------------
# deezer CLI group
# ---------------------------------------------------------------------------


@cli.group("deezer")
def cli_deezer() -> None:
    pass


@cli_deezer.command("import")
@click.option("--source", "-s", required=True, multiple=True, help="Path to local .m3u file")
@click.option("--destination", "-d", required=True, multiple=True, help="Name for the new Deezer playlist")
@click.option("--autopilot", is_flag=True)
@click.option("--embed-matches", is_flag=True)
@click.option("--public", is_flag=True)
@click.option("--from-path", default=None)
@click.option("--to-path", default=None)
def cli_deezer_import(
    source: tuple[str, ...],
    destination: tuple[str, ...],
    autopilot: bool = False,
    embed_matches: bool = False,
    public: bool = False,
    from_path: str | None = None,
    to_path: str | None = None,
) -> None:
    if len(source) != len(destination):
        raise click.BadParameter("Number of sources must match the number of destinations")
    path_mapper = _build_path_mapper(from_path, to_path)

    try:
        dz = get_deezer_client()
    except DeezerAuthenticationError as exc:
        raise click.ClickException(str(exc)) from exc

    for src, dst in zip(source, destination, strict=True):
        playlist = get_playlist(src, path_mapper=path_mapper)
        DeezerPlaylist.create_from_another_playlist(
            dst, playlist, public=public, deezer=dz, autopilot=autopilot, embed_matches=embed_matches
        )


@cli_deezer.command("sync")
@click.option("--source", "-s", required=True, help="Path to local .m3u file")
@click.option("--destination", "-d", required=True, help="Deezer playlist ID or URL")
@click.option("--autopilot", is_flag=True)
@click.option("--embed-matches", is_flag=True)
@click.option("--sort-tracks", is_flag=True)
@click.option("--from-path", default=None)
@click.option("--to-path", default=None)
def cli_deezer_sync(
    source: str,
    destination: str,
    autopilot: bool = False,
    embed_matches: bool = False,
    sort_tracks: bool = False,
    from_path: str | None = None,
    to_path: str | None = None,
) -> None:
    path_mapper = _build_path_mapper(from_path, to_path)

    try:
        dz = get_deezer_client()
    except DeezerAuthenticationError as exc:
        raise click.ClickException(str(exc)) from exc

    source_playlist = get_playlist(source, path_mapper=path_mapper)
    destination_playlist = DeezerPlaylist(destination, deezer=dz)
    destination_playlist.sync_tracks(
        source_playlist.tracks, autopilot=autopilot, embed_matches=embed_matches, sort_tracks=sort_tracks
    )


@cli_deezer.command("match")
@click.option("--source", "-s", required=True, multiple=True, help="Path to local .m3u file")
@click.option("--autopilot", is_flag=True)
@click.option("--from-path", default=None)
@click.option("--to-path", default=None)
def cli_deezer_match(
    source: tuple[str, ...],
    autopilot: bool = False,
    from_path: str | None = None,
    to_path: str | None = None,
) -> None:
    path_mapper = _build_path_mapper(from_path, to_path)

    try:
        get_deezer_client()
    except DeezerAuthenticationError as exc:
        raise click.ClickException(str(exc)) from exc

    for src in source:
        playlist = get_playlist(src, path_mapper=path_mapper)
        DeezerPlaylist.track_matcher().match_list(playlist.tracks, autopilot=autopilot, embed_matches=True)


@cli_deezer.command("compare")
@click.option("--source", "-s", required=True, help="Path to local .m3u file")
@click.option("--destination", "-d", required=True, help="Deezer playlist ID or URL")
@click.option("--from-path", default=None)
@click.option("--to-path", default=None)
def cli_deezer_compare(
    source: str,
    destination: str,
    from_path: str | None = None,
    to_path: str | None = None,
) -> None:
    path_mapper = _build_path_mapper(from_path, to_path)

    try:
        dz = get_deezer_client()
    except DeezerAuthenticationError as exc:
        raise click.ClickException(str(exc)) from exc

    local_playlist = get_playlist(source, path_mapper=path_mapper)
    deezer_playlist = DeezerPlaylist(destination, deezer=dz)
    result = compare_deezer_playlists(local_playlist, deezer_playlist)

    source_only = result.source_only
    target_only = result.target_only

    if source_only:
        print("Only in local playlist:")
        for track in source_only:
            print(f"  - {track.display_artist} — {track.title}")

    if target_only:
        print("Only in Deezer playlist:")
        for track in target_only:
            print(f"  - {track.display_artist} — {track.title}")

    if not source_only and not target_only:
        print("No differences.")


@cli_deezer.command("duplicates")
@click.option("--source", "-s", required=True, help="Path to local .m3u file")
def cli_deezer_duplicates(source: str) -> None:
    source_playlist = get_playlist(source)

    tracks_map: dict[str, list[LocalTrack]] = {}
    for track in source_playlist.tracks:
        if not isinstance(track, LocalTrack):
            continue
        ref = track.service_ref("DEEZER")
        if not ref or ref == "SKIP":
            continue
        canonical = normalise_deezer_url(ref) if is_valid_deezer_url(ref) else ref
        tracks_map.setdefault(canonical, []).append(track)

    found = False
    for ref_url, dupes in tracks_map.items():
        if len(dupes) <= 1:
            continue
        if not found:
            print("Duplicate Deezer references found:")
            found = True
        print(f"  {ref_url}")
        for t in dupes:
            print(f"    - {t.file_path}")


if __name__ == "__main__":
    cli()
