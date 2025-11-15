from typing import Union

import click

from playlists.local_library import LocalLibrary
from playlists.local_playlist import LocalPlaylist
from playlists.spotify_playlist import SpotifyPlaylist
import os
from playlists.compare import compare_playlists


@click.group()
def cli():
    pass


@cli.group("spotify")
def cli_spotify():
    pass


@cli_spotify.command("import")
@click.option("--source", "-s", required=True, multiple=True, help="Source playlist path")
@click.option("--destination", "-d", required=True, multiple=True, help="Destination playlist name")
@click.option("--autopilot", is_flag=True, help="When multiple matches are found, choose the first one")
@click.option("--embed-matches", is_flag=True, help="Embed a reference to the matched track in the source track")
@click.option("--public", is_flag=True, help="Create a public playlist (default is private)")
def cli_spotify_import(source, destination, autopilot: bool = False, embed_matches: bool = False, public: bool = False):
    if len(source) != len(destination):
        raise click.BadParameter("Number of sources must match the number of destinations")
    inputs = zip(source, destination)
    for source, destination in inputs:
        playlist = get_playlist(source)
        SpotifyPlaylist.create_from_another_playlist(destination, playlist, autopilot=autopilot,
                                                     embed_matches=embed_matches, public=public)

@cli_spotify.command("sync")
@click.option("--source", "-s", required=True, help="Source playlist path")
@click.option("--destination", "-d", required=True, help="Destination playlist ID")
@click.option("--autopilot", is_flag=True, help="When multiple matches are found, choose the first one")
@click.option("--embed-matches", is_flag=True, help="Embed a reference to the matched track in the source track")
@click.option("--sort-tracks", is_flag=True, help="Sort tracks alphabetically")
def cli_spotify_sync(destination, source, autopilot: bool = False, embed_matches: bool = False, sort_tracks: bool = False):
    source_playlist = get_playlist(source)
    destination_playlist = SpotifyPlaylist(destination)
    destination_playlist.clear()
    if sort_tracks:
        tracks = sorted(source_playlist.tracks, key=lambda track: track.track_id)
    else:
        tracks = source_playlist.tracks
    destination_playlist.import_tracks(tracks, autopilot=autopilot, embed_matches=embed_matches)

@cli_spotify.command("duplicates")
@click.option("--source", "-s", required=True, help="Source playlist path")
def cli_spotify_duplicates(source):
    source_playlist = get_playlist(source)
    tracks = dict()
    for track in source_playlist.tracks:
        track_id = track.spotify_ref
        if track_id not in tracks:
            tracks[track_id] = []
        tracks[track_id].append(track)
    for track_id, tracks in tracks.items():
        if len(tracks) == 1:
            continue
        print(f"{track_id}: {len(tracks)}")
        for track in tracks:
            print(track.track_id)


@cli_spotify.command("match")
@click.option("--source", "-s", required=True, multiple=True, help="Source playlist path")
@click.option("--autopilot", is_flag=True, help="When multiple matches are found, choose the first one")
def cli_spotify_match(source, autopilot: bool = False):
    for source in source:
        playlist = get_playlist(source)
        SpotifyPlaylist.track_matcher().match_list(playlist.tracks, autopilot=autopilot, embed_matches=True)


@cli_spotify.command("compare")
@click.option("--source", "-s", required=True, help="Source local playlist path (m3u)")
@click.option("--destination", "-d", required=True, help="Destination Spotify playlist id or URL")
def cli_spotify_compare(source, destination):
    """Compare a local m3u playlist with a Spotify playlist and print differences."""
    local_only, spotify_only = compare_playlists(source, destination)

    print(f"Local-only tracks: {len(local_only)}")
    if len(local_only) > 0:
        for idx, track in enumerate(local_only, start=1):
            spotify_ref = track.spotify_ref if track.spotify_ref is not None else "(none)"
            print(f"{idx}. {track.file_path}  | spotify_ref: {spotify_ref}")

    print("")
    print(f"Spotify-only tracks: {len(spotify_only)}")
    if len(spotify_only) > 0:
        for idx, track in enumerate(spotify_only, start=1):
            artists = ", ".join(track.artists) if track.artists else ""
            title = track.title or "(unknown title)"
            print(f"{idx}. {track.track_url}  | {title} — {artists}")


def get_playlist(source: str) -> Union[LocalPlaylist, LocalLibrary]:
    if os.path.isdir(source):
        return LocalLibrary(source)
    if os.path.isfile(source):
        return LocalPlaylist(source)
    raise ValueError("Invalid source path")


if __name__ == "__main__":
    cli()
