import click

from playlists.local_playlist import LocalPlaylist
from playlists.spotify_playlist import SpotifyPlaylist


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
    SpotifyPlaylist.create_from_another_playlist(destination, playlist)


if __name__ == "__main__":
    cli()
