import os
from typing import Optional, Union

import click

from playlists.compare import compare_playlists
from playlists.local_library import LocalLibrary
from playlists.local_playlist import LocalPlaylist
from playlists.path_mapper import PathMapper
from playlists.spotify_playlist import SpotifyPlaylist
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
    from_path: Optional[str] = None,
    to_path: Optional[str] = None,
) -> None:
    if len(source) != len(destination):
        raise click.BadParameter("Number of sources must match the number of destinations")

    # Create path mapper if both from_path and to_path are provided
    path_mapper = None
    if from_path and to_path:
        path_mapper = PathMapper(from_path, to_path)
    elif from_path or to_path:
        raise click.BadParameter("Both --from-path and --to-path must be provided together")

    inputs = zip(source, destination)
    for src, dst in inputs:
        playlist = get_playlist(src, path_mapper=path_mapper)
        SpotifyPlaylist.create_from_another_playlist(
            dst, playlist, autopilot=autopilot, embed_matches=embed_matches, public=public
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
    from_path: Optional[str] = None,
    to_path: Optional[str] = None,
) -> None:
    # Create path mapper if both from_path and to_path are provided
    path_mapper = None
    if from_path and to_path:
        path_mapper = PathMapper(from_path, to_path)
    elif from_path or to_path:
        raise click.BadParameter("Both --from-path and --to-path must be provided together")

    source_playlist = get_playlist(source, path_mapper=path_mapper)
    destination_playlist = SpotifyPlaylist(destination)
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
    from_path: Optional[str] = None,
    to_path: Optional[str] = None,
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
    from_path: Optional[str] = None,
    to_path: Optional[str] = None,
) -> None:
    """Compare a local m3u playlist with a Spotify playlist and print differences."""
    # Create path mapper if both from_path and to_path are provided
    path_mapper = None
    if from_path and to_path:
        path_mapper = PathMapper(from_path, to_path)
    elif from_path or to_path:
        raise click.BadParameter("Both --from-path and --to-path must be provided together")

    local_only, spotify_only = compare_playlists(source, destination, path_mapper=path_mapper)

    print(f"Local-only tracks: {len(local_only)}")
    if len(local_only) > 0:
        for idx, local_track in enumerate(local_only, start=1):
            spotify_ref = local_track.spotify_ref if local_track.spotify_ref is not None else "(none)"
            print(f"{idx}. {local_track.file_path}  | spotify_ref: {spotify_ref}")

    print("")
    print(f"Spotify-only tracks: {len(spotify_only)}")
    if len(spotify_only) > 0:
        for idx, spotify_track in enumerate(spotify_only, start=1):
            artists = ", ".join(spotify_track.artists) if spotify_track.artists else ""
            title = spotify_track.title or "(unknown title)"
            print(f"{idx}. {spotify_track.track_url}  | {title} — {artists}")


def get_playlist(source: str, path_mapper: Optional[PathMapper] = None) -> Union[LocalPlaylist, LocalLibrary]:
    if os.path.isdir(source):
        return LocalLibrary(source)
    if os.path.isfile(source):
        return LocalPlaylist(source, path_mapper=path_mapper)
    raise ValueError("Invalid source path")


if __name__ == "__main__":
    cli()
