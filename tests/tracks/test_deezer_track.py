import sys
import types

# Inject fake deezer module before importing application code
fake_deezer = types.ModuleType('deezer')

class FakeClient:
    def __init__(self, access_token=None):
        self.access_token = access_token
    def get_track(self, id):
        return {
            'id': id,
            'title': 'Fake Title',
            'duration': 210,
            'album': {'title': 'Fake Album'},
            'artist': {'name': 'Fake Artist'},
            'contributors': [{'name': 'Fake Artist'}]
        }

fake_deezer.Client = FakeClient
sys.modules['deezer'] = fake_deezer

from tracks.deezer_track import DeezerTrack


def test_deezer_track_properties():
    dt = DeezerTrack('https://www.deezer.com/track/12345')
    assert dt.track_id == '12345'
    assert dt.track_url == 'https://www.deezer.com/track/12345'
    assert dt.title == 'Fake Title'
    assert dt.album == 'Fake Album'
    assert dt.duration == 210.0
    assert dt.artists == ['Fake Artist']
    assert dt.track_number == 0

