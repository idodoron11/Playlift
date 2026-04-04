from typing import Any, Iterable

from api.spotify import SpotifyAPI
from matchers.spotify_matcher import SpotifyMatcher
from playlists import Playlist, TrackCollection
from tracks import Track
from tracks.spotify_track import SpotifyTrack


class SpotifyPlaylist(Playlist):
    def __init__(self, playlist_url: str | None = None, data: dict[str, Any] | None = None):
        self._id = SpotifyAPI.get_instance()._get_id("playlist", playlist_url)
        self._data: dict[str, Any] | None = data
        if self._data and self._data["id"] != self._id:
            raise ValueError("The data object does not match the track id")
        self._tracks: list[SpotifyTrack] = []

    def _load_data(self) -> None:
        self._data = SpotifyAPI.get_instance().playlist(self.playlist_id)
        self._tracks = []
        api_tracks = self._data["tracks"]
        while api_tracks:
            for api_track in api_tracks["items"]:
                self._tracks.append(SpotifyTrack(api_track["track"]["id"], data=api_track["track"]))
            api_tracks = SpotifyAPI.get_instance().next(api_tracks)

    @classmethod
    def create(cls, playlist_name: str, public: bool = False) -> "SpotifyPlaylist":
        user_id = SpotifyAPI.get_instance().current_user()["id"]
        playlist_resp = SpotifyAPI.get_instance().user_playlist_create(user_id, playlist_name, public=public)
        playlist_id = playlist_resp["id"]
        return cls(playlist_id)

    @classmethod
    def create_from_another_playlist(
        cls,
        playlist_name: str,
        source_playlist: TrackCollection,
        public: bool = False,
        autopilot: bool = False,
        embed_matches: bool = False,
    ) -> "SpotifyPlaylist":
        sp_tracks: list[Track] = SpotifyPlaylist.track_matcher().match_list(
            source_playlist.tracks, autopilot=autopilot, embed_matches=embed_matches
        )
        new_playlist = cls.create(playlist_name, public=public)
        new_playlist.add_tracks(sp_tracks)  # type: ignore[arg-type]  # list[Track] contains SpotifyTrack instances at runtime
        return new_playlist

    def import_tracks(self, tracks: Iterable[Track], autopilot: bool = False, embed_matches: bool = False) -> None:
        sp_tracks: list[Track] = SpotifyPlaylist.track_matcher().match_list(
            tracks, autopilot=autopilot, embed_matches=embed_matches
        )
        self.add_tracks(sp_tracks)  # type: ignore[arg-type]  # list[Track] contains SpotifyTrack instances at runtime

    @property
    def tracks(self) -> list[SpotifyTrack]:
        if not self._data:
            self._load_data()
        return self._tracks

    @property
    def playlist_id(self) -> str:
        return str(self._id)

    @property
    def name(self) -> str:
        return str(self.data["name"])

    @property
    def data(self) -> dict[str, Any]:
        if not self._data:
            self._load_data()
        assert self._data is not None
        return self._data

    def clear(self) -> None:
        self.remove_track(list(self.tracks))

    def remove_track(self, tracks: list[SpotifyTrack]) -> None:  # type: ignore[override]  # narrowed type is safe in practice
        try:
            for start in range(0, len(tracks), 100):
                end = min(len(tracks), start + 100)
                chunk = map(lambda track: track.track_id, tracks[start:end])
                SpotifyAPI.get_instance().playlist_remove_all_occurrences_of_items(self.playlist_id, chunk)
        finally:
            self._data = None

    def add_tracks(self, tracks: list[SpotifyTrack]) -> None:  # type: ignore[override]  # narrowed type is safe in practice
        try:
            for start in range(0, len(tracks), 100):
                end = min(len(tracks), start + 100)
                chunk = map(lambda track: track.track_id, tracks[start:end])
                SpotifyAPI.get_instance().playlist_add_items(self.playlist_id, chunk)
        finally:
            self._data = None

    @staticmethod
    def track_matcher() -> SpotifyMatcher:
        return SpotifyMatcher.get_instance()  # type: ignore[return-value]

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, self.__class__):
            return False
        return self.playlist_id == other.playlist_id

    def __hash__(self) -> int:
        return hash(self.playlist_id)
