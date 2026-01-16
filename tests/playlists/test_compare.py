from playlists import compare as compare_module


class FakeLocalTrack:
    def __init__(self, file_path, spotify_ref):
        self.file_path = file_path
        self._spotify_ref = spotify_ref

    @property
    def spotify_ref(self):
        return self._spotify_ref

    @property
    def spotify_id(self):
        # reuse parse logic via attribute access used in compare
        return getattr(self, "_spotify_id", None) or self._spotify_ref


class FakeSpotifyTrack:
    def __init__(self, track_id, title="t", artists=None):
        self._id = track_id
        self._title = title
        self._artists = artists or ["Artist"]

    @property
    def track_id(self):
        return self._id

    @property
    def track_url(self):
        return f"https://open.spotify.com/track/{self._id}"

    @property
    def title(self):
        return self._title

    @property
    def artists(self):
        return self._artists


def test_compare_simple(monkeypatch):
    # local has two tracks: one references S1, the other has SKIP
    local_tracks = [FakeLocalTrack("/tmp/a.mp3", "S1"), FakeLocalTrack("/tmp/b.mp3", "SKIP")]

    class FakeLocalPlaylist:
        def __init__(self, path, path_mapper=None):
            self._tracks = local_tracks

        @property
        def tracks(self):
            return self._tracks

    # spotify playlist has tracks S1 and S2
    spotify_tracks = [FakeSpotifyTrack("S1"), FakeSpotifyTrack("S2")]

    class FakeSpotifyPlaylist:
        def __init__(self, pid):
            self._tracks = spotify_tracks

        @property
        def tracks(self):
            return self._tracks

    monkeypatch.setattr(compare_module, "LocalPlaylist", FakeLocalPlaylist)
    monkeypatch.setattr(compare_module, "SpotifyPlaylist", FakeSpotifyPlaylist)

    local_only, spotify_only = compare_module.compare_playlists("dummy.m3u", "spotify:playlist:pid")

    # local_only should contain the SKIP track
    assert len(local_only) == 1
    assert local_only[0].file_path == "/tmp/b.mp3"

    # spotify_only should contain S2
    assert len(spotify_only) == 1
    assert spotify_only[0].track_id == "S2"

