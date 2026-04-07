from __future__ import annotations

import contextlib
import logging
from typing import TYPE_CHECKING, Any

import music_tag
import mutagen
from music_tag import AudioFile
from mutagen.flac import FLAC
from mutagen.id3 import (  # type: ignore[attr-defined]  # mutagen stubs don't re-export TSRC/TXXX
    TSRC,
    TXXX,
)
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4FreeForm

if TYPE_CHECKING:
    from mutagen._file import FileType as MutagenFileType

from api.spotify_utils import parse_spotify_id
from tracks import Track

logger = logging.getLogger(__name__)

_ITUNES_FREEFORM_PREFIX = "----:com.apple.iTunes:"


def _normalize_isrc(raw: str) -> str:
    """Normalize an ISRC value: uppercase and strip hyphens."""
    return raw.upper().strip().replace("-", "")


class LocalTrack(Track):
    def __init__(self, file_path: str):
        self._file_path = file_path
        self._audio: AudioFile | None = None
        self._mutagen_file: MutagenFileType | None = None
        self.reload_metadata()

    def reload_metadata(self) -> None:
        self._audio = music_tag.load_file(self._file_path)
        self._mutagen_file = self._audio.mfile

    @property
    def file_path(self) -> str:
        return self._file_path

    @property
    def artists(self) -> list[str]:
        tag = self._get_tag("artist")
        return tag.values if tag else []

    @property
    def display_artist(self) -> str:
        tag = self._get_tag("artist")
        return tag.value if tag else ""

    @property
    def title(self) -> str:
        tag = self._get_tag("title")
        return tag.first if tag else ""

    @property
    def album(self) -> str:
        tag = self._get_tag("album")
        return tag.first if tag else ""

    @property
    def duration(self) -> float:
        tag = self._get_tag("#length")
        return tag.first if tag else 0.0

    @property
    def track_number(self) -> int:
        tag = self._get_tag("tracknumber")
        return tag.value if tag else 0

    def _get_tag(self, tag_name: str, assert_not_empty: bool = False) -> Any:
        result = None
        with contextlib.suppress(Exception):
            result = self._audio[tag_name]  # type: ignore[index]
        if assert_not_empty and not result:
            raise AttributeError(f"No {tag_name} found")
        return result

    @property
    def track_id(self) -> str:
        return self.file_path

    def _get_custom_tag(self, tag_name: str) -> str | None:
        tag_name = tag_name.upper()
        if isinstance(self._mutagen_file, MP4):
            tag_name = f"{_ITUNES_FREEFORM_PREFIX}{tag_name}"
        elif isinstance(self._mutagen_file, MP3):
            tag_name = f"TXXX:{tag_name}"
        if self._mutagen_file is None or self._mutagen_file.tags is None:
            return None
        if isinstance(self._mutagen_file, MP4) and tag_name not in self._mutagen_file.tags:
            tag_name = next(
                (k for k in self._mutagen_file.tags if k.lower() == tag_name.lower()),
                tag_name,
            )
        if tag_name not in self._mutagen_file.tags:
            return None
        tag: Any = self._mutagen_file[tag_name]
        tag = tag[0] if tag else None
        if isinstance(tag, bytes):
            return tag.decode("utf-8")
        elif isinstance(tag, str):
            return tag
        return str(tag) if tag is not None else None

    def _set_custom_tag(self, tag_name: str, value: str) -> None:
        tag_name = tag_name.upper()
        if self._mutagen_file is None:
            return
        if isinstance(self._mutagen_file, MP4):
            tag_name = f"{_ITUNES_FREEFORM_PREFIX}{tag_name}"
            if self._mutagen_file.tags is None:
                raise AttributeError("MP4 file has no tags")
            self._mutagen_file.tags[tag_name] = [MP4FreeForm(value.encode("utf-8"))]
        elif isinstance(self._mutagen_file, MP3):
            frame = TXXX(encoding=3, desc=tag_name, text=value)  # type: ignore[no-untyped-call]  # mutagen stubs don't type TXXX.__init__
            if self._mutagen_file.tags is not None:
                self._mutagen_file.tags.add(frame)
        else:
            if self._mutagen_file.tags is not None:
                self._mutagen_file.tags[tag_name] = value
        try:
            self._mutagen_file.save()
        except (mutagen.MutagenError, OSError, AttributeError) as e:  # type: ignore[attr-defined]  # mutagen stubs don't export MutagenError top-level
            print(f"Could not save tags for {self.track_id} due to {e}")
        self.reload_metadata()

    @property
    def isrc(self) -> str | None:
        """Return the ISRC tag value, normalized to uppercase with hyphens stripped.

        Reads from the format-appropriate tag: TSRC (MP3), isrc Vorbis comment
        (FLAC), or iTunes freeform tag (M4A). Returns None if the tag is absent
        or empty.
        """
        raw: str | None = None
        if isinstance(self._mutagen_file, MP3):
            if self._mutagen_file.tags is not None and "TSRC" in self._mutagen_file.tags:
                frame: Any = self._mutagen_file.tags["TSRC"]
                raw = str(frame.text[0]) if frame.text else None
        elif isinstance(self._mutagen_file, FLAC):
            tag = self._get_tag("isrc")
            raw = str(tag.first) if tag and tag.first else None
        else:
            raw = self._get_custom_tag("isrc")
        if not raw or not raw.strip():
            return None
        return _normalize_isrc(raw)

    @isrc.setter
    def isrc(self, value: str) -> None:
        """Write the ISRC tag to the audio file.

        MP3 writes a TSRC ID3 frame, FLAC writes via music_tag isrc key,
        M4A writes an iTunes freeform tag. For M4A, skips the write when the
        normalized value is already stored — this guards against creating a
        second uppercase atom when the file already carries the same ISRC
        under a lowercase freeform key (a case-insensitive variant that
        _set_custom_tag would not detect on its own).
        """
        if self._mutagen_file is None:
            return
        try:
            if isinstance(self._mutagen_file, MP3):
                frame = TSRC(encoding=3, text=[value])  # type: ignore[no-untyped-call]  # mutagen stubs don't type TSRC.__init__
                if self._mutagen_file.tags is not None:
                    self._mutagen_file.tags.add(frame)
                self._mutagen_file.save()
            elif isinstance(self._mutagen_file, FLAC):
                if self._mutagen_file.tags is not None:
                    self._mutagen_file.tags["isrc"] = value  # type: ignore[index]  # VCFLACDict supports str indexing at runtime
                self._mutagen_file.save()
            elif isinstance(self._mutagen_file, MP4):
                if self.isrc is not None and self.isrc == _normalize_isrc(value):
                    return
                self._set_custom_tag("isrc", value)
                return  # _set_custom_tag handles save + reload
            else:
                raise NotImplementedError("Unsupported file type for ISRC writing")
            self.reload_metadata()
        except (mutagen.MutagenError, OSError, AttributeError) as e:  # type: ignore[attr-defined]
            logger.warning("Could not write ISRC for %s: %s", self.track_id, e)

    @property
    def spotify_ref(self) -> str | None:
        return self._get_custom_tag("spotify")

    @spotify_ref.setter
    def spotify_ref(self, spotify_ref: str) -> None:
        self._set_custom_tag("spotify", spotify_ref)

    @property
    def spotify_id(self) -> str | None:
        """Return a normalized Spotify track id derived from `spotify_ref`.

        This leaves the behavior of `spotify_ref` unchanged (it still returns
        the raw tag), and provides a convenience property for comparisons.
        The special tag value "SKIP" (case-insensitive) is treated as None.
        """
        return parse_spotify_id(self.spotify_ref)
