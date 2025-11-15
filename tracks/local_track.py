from typing import List, Optional

import music_tag
import mutagen
from music_tag import AudioFile
from mutagen.id3 import TXXX
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4

from tracks import Track
from api.spotify_utils import parse_spotify_id


class LocalTrack(Track):
    def __init__(self, file_path: str):
        self._file_path = file_path
        self._audio: Optional[AudioFile] = None
        self._mutagen_file: Optional[mutagen.File] = None
        self.reload_metadata()

    def reload_metadata(self):
        self._audio = music_tag.load_file(self._file_path)
        self._mutagen_file = self._audio.mfile

    @property
    def file_path(self) -> str:
        return self._file_path

    @property
    def artists(self) -> List[str]:
        tag = self._get_tag("artist")
        return tag.values if tag else None

    @property
    def display_artist(self) -> str:
        tag = self._get_tag("artist")
        return tag.value if tag else None

    @property
    def title(self) -> str:
        tag = self._get_tag("title")
        return tag.first if tag else None

    @property
    def album(self) -> str:
        tag = self._get_tag("album")
        return tag.first if tag else None

    @property
    def duration(self) -> float:
        tag = self._get_tag("#length")
        return tag.first if tag else None

    @property
    def track_number(self) -> int:
        tag = self._get_tag("tracknumber")
        return tag.value if tag else None

    def _get_tag(self, tag_name, assert_not_empty=False):
        result = None
        try:
            result = self._audio[tag_name]
        except:
            pass
        if assert_not_empty and not result:
            raise AttributeError(f"No {tag_name} found")
        return result

    @property
    def track_id(self) -> str:
        return self.file_path

    def _get_custom_tag(self, tag_name: str):
        tag_name = tag_name.upper()
        if isinstance(self._mutagen_file, MP4):
            tag_name = f"----:com.apple.iTunes:{tag_name}"
        elif isinstance(self._mutagen_file, MP3):
            tag_name = f"TXXX:{tag_name}"
        if tag_name not in self._mutagen_file.tags:
            return None
        tag = self._mutagen_file[tag_name]
        tag = tag[0] if tag else None
        if isinstance(tag, bytes):
            return tag.decode('utf-8')
        elif isinstance(tag, str):
            return tag
        return str(tag)

    def _set_custom_tag(self, tag_name: str, value: str):
        tag_name = tag_name.upper()
        if isinstance(self._mutagen_file, MP4):
            tag_name = f"----:com.apple.iTunes:{tag_name}"
            self._mutagen_file.tags[tag_name] = value.encode('utf-8')
        elif isinstance(self._mutagen_file, MP3):
            frame = TXXX(encoding=3, desc=tag_name, text=value)
            self._mutagen_file.tags.add(frame)
        else:
            self._mutagen_file.tags[tag_name] = value
        try:
            self._mutagen_file.save()
        except (mutagen.MutagenError, OSError) as e:
            print(f"Could not save tags for {self.track_id} due to {e}")
        self.reload_metadata()

    @property
    def spotify_ref(self):
        return self._get_custom_tag("spotify")

    @spotify_ref.setter
    def spotify_ref(self, spotify_ref):
        self._set_custom_tag("spotify", spotify_ref)

    @property
    def spotify_id(self) -> Optional[str]:
        """Return a normalized Spotify track id derived from `spotify_ref`.

        This leaves the behavior of `spotify_ref` unchanged (it still returns
        the raw tag), and provides a convenience property for comparisons.
        The special tag value "SKIP" (case-insensitive) is treated as None.
        """
        return parse_spotify_id(self.spotify_ref)
