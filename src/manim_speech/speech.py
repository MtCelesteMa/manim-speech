"""Speech utils for Manim Speech."""

import hashlib
import pathlib
import re

import manim
import numpy as np
import pydantic
import slugify
from mutagen.mp3 import MP3

from . import services


class SpeechData(pydantic.BaseModel):
    path: pathlib.Path
    transcript: services.base.Transcript
    duration: float
    bookmarks: dict[str, float]


def remove_bookmarks(s: str) -> str:
    return re.sub(r"<bookmark\s*mark\s*=['\"]\w*[\"']\s*/>", "", s)


def get_bookmark_times(
    text: str, transcript: services.base.Transcript
) -> dict[str, float]:
    cleaned_text = remove_bookmarks(text)
    ct_len = len(cleaned_text)
    tt_len = len(transcript.text.strip())

    bookmark_dist: dict[str, int] = {}
    offset = 0
    for part in re.split(r"(<bookmark\s*mark\s*=[\'\"]\w*[\"\']\s*/>)", text):
        match = re.match(r"<bookmark\s*mark\s*=[\'\"](.*)[\"\']\s*/>", part)
        if isinstance(match, re.Match):
            bookmark_dist[match.group(1)] = offset
        else:
            offset += len(part)

    bookmark_times = np.interp(
        np.array([v for k, v in bookmark_dist.items()]) * tt_len / ct_len,
        [b.text_start for b in transcript.boundaries] + [len(transcript.text)],
        [b.start for b in transcript.boundaries] + [transcript.boundaries[-1].end],
    )
    return {name: t for name, t in zip(bookmark_dist.keys(), bookmark_times)}


def create(
    text: str,
    tts_service: services.base.TTSService | None = None,
    stt_service: services.base.STTService | None = None,
    *,
    cache_dir: pathlib.Path | str | None = None,
) -> SpeechData:
    if isinstance(cache_dir, type(None)):
        cache_dir = pathlib.Path(manim.config.media_dir) / "manim_speech"
    elif isinstance(cache_dir, str):
        cache_dir = pathlib.Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    cleaned_text = remove_bookmarks(text)
    slug = f"{slugify.slugify(cleaned_text, max_length=50, word_boundary=True, save_order=True)}-{hashlib.sha256(cleaned_text.encode()).hexdigest()[:8]}"
    cache_path = cache_dir / slug
    if not cache_path.exists():
        cache_path.mkdir(parents=True)
        with (cache_path / "text.txt").open("w") as f:
            f.write(cleaned_text)

    audio_path = cache_path / "audio.mp3"
    if not audio_path.exists():
        if isinstance(tts_service, services.base.TTSService):
            tts_service.tts(cleaned_text, audio_path)
        else:
            return SpeechData(
                path=cache_path,
                transcript=services.base.Transcript(text="", boundaries=[]),
                duration=1e-6,
                bookmarks={},
            )

    transcript_path = cache_path / "transcript.json"
    if transcript_path.exists():
        with transcript_path.open() as f:
            transcript = services.base.Transcript.model_validate_json(f.read())
    else:
        if isinstance(stt_service, services.base.STTService):
            transcript = stt_service.stt(audio_path)
            with transcript_path.open("w") as f:
                f.write(transcript.model_dump_json(indent=4))
        else:
            transcript = services.base.Transcript(
                text=cleaned_text,
                boundaries=[
                    services.base.Boundary(
                        text=cleaned_text,
                        start=0.0,
                        end=MP3(audio_path).info.length,
                        text_start=0,
                    )
                ],
            )

    return SpeechData(
        path=cache_path,
        transcript=transcript,
        duration=MP3(audio_path).info.length,
        bookmarks=get_bookmark_times(text, transcript),
    )
