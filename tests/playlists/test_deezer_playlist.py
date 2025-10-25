import sys
import types

# Create a fake deezer module before importing application code
fake_deezer = types.ModuleType('deezer')

class FakePlaylist:
    def __init__(self, id, title):
        self.id = id
        self.title = title
        self.tracks = []

    def add_tracks(self, track_ids):
        self.tracks.extend(track_ids)
        return True

    def delete_tracks(self, track_ids):
        for tid in track_ids:
            if tid in self.tracks:
                self.tracks.remove(tid)
        return True

    def to_dict(self):
        # Convert track IDs to track data objects
        track_data = []
        for tid in self.tracks:
            track_data.append({
                'id': tid,
                'title': 'Fake Track',
                'artist': {'name': 'Fake Artist'},
                'album': {'title': 'Fake Album'},
                'duration': 210
            })
        return {
            'id': self.id,
            'title': self.title,
            'tracks': {
                'data': track_data,
                'next': None
            }
        }

class FakeClient:
    def __init__(self, access_token=None):
        self.access_token = access_token
        self._playlists = {}
        self._next_playlist_id = 10000
        self._tracks = {
            '12345': {
                'id': 12345,
                'title': 'Fake Track',
                'artist': {'name': 'Fake Artist'},
                'album': {'title': 'Fake Album'},
                'duration': 210
            }
        }

    def get_playlist(self, playlist_id):
        str_id = str(playlist_id)
        if str_id not in self._playlists:
            # Create a fake playlist for this id
            playlist = FakePlaylist(int(playlist_id), 'Fake Playlist')
            self._playlists[str_id] = playlist
        return self._playlists[str_id].to_dict()

    def get_track(self, track_id):
        return self._tracks.get(str(track_id))

    def get_user(self, user_id=None):
        client = self
        class User:
            def create_playlist(self, title):
                playlist_id = client._next_playlist_id
                client._next_playlist_id += 1
                playlist = FakePlaylist(playlist_id, title)
                client._playlists[str(playlist_id)] = playlist
                return playlist.to_dict()
        return User()

    def search(self, query):
        # Always return our fake track as a match
        return {
            'data': [self._tracks['12345']]
        }

fake_deezer.Client = FakeClient
sys.modules['deezer'] = fake_deezer

from playlists.deezer_playlist import DeezerPlaylist
from tracks.deezer_track import DeezerTrack


def test_deezer_playlist_create():
    playlist = DeezerPlaylist.create("Test Playlist")
    assert playlist.name == "Test Playlist"
    assert isinstance(playlist.playlist_id, int)
    assert len(list(playlist.tracks)) == 0


def test_deezer_playlist_add_tracks():
    playlist = DeezerPlaylist.create("Test Playlist")
    track = DeezerTrack("12345")
    playlist.add_tracks([track])
    # Reload playlist data
    playlist._data = None
    tracks = list(playlist.tracks)
    assert len(tracks) == 1
    assert isinstance(tracks[0], DeezerTrack)
    assert tracks[0].title == "Fake Track"


def test_deezer_playlist_properties():
    playlist = DeezerPlaylist("https://www.deezer.com/playlist/123456")
    assert playlist.name == "Fake Playlist"
    assert playlist.playlist_id == 123456
    tracks = list(playlist.tracks)
    assert len(tracks) == 0  # Fresh playlist starts empty

    # Add a track and verify
    track = DeezerTrack("12345")
    playlist.add_tracks([track])
    playlist._data = None  # Force reload
    tracks = list(playlist.tracks)
    assert len(tracks) == 1
    assert tracks[0].title == "Fake Track"
