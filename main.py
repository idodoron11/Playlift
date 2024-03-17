import click
from playlists.local_playlist import LocalPlaylist
from playlists.spotify_playlist import SpotifyPlaylist
from tracks.spotify_track import SpotifyTrack


@click.group()
def cli():
    pass


@cli.group("spotify")
def cli_spotify():
    pass


@cli_spotify.command("import")
@click.argument("source")
@click.argument("destination")
def cli_spotify_import(source, destination):
    playlist = LocalPlaylist(source)
    sp_playlist = SpotifyPlaylist.create(destination)
    sp_tracks = []
    for index, track in enumerate(playlist.tracks):
        response = SpotifyTrack.search(track.artists[0], track.album, track.title)
        sp_track = response[0]
        sp_tracks.append(sp_track)
    sp_playlist.add_tracks(sp_tracks)


if __name__ == "__main__":
    cli()
