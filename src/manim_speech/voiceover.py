"""Voiceover utils for Manim Speech."""

import hashlib
import re
from os import PathLike
from pathlib import Path

import manim
import numpy as np
import slugify
from mutagen import File
from pydantic import BaseModel

from . import services


class VoiceoverData(BaseModel):
    path: Path
    transcript: services.Transcript
    duration: float
    bookmarks: dict[str, float]


def remove_bookmarks(s: str) -> str:
    return re.sub(r"<bookmark\s*mark\s*=['\"]\w*[\"']\s*/>", "", s)


def get_bookmark_times(text: str, transcript: services.Transcript) -> dict[str, float]:
    cleaned_text = remove_bookmarks(text)
    ct_len = len(cleaned_text)
    tt_len = len(transcript.text.strip())

    bookmark_dist: dict[str, int] = {}
    offset = 0
    for part in re.split(r"(<bookmark\s*mark\s*=[\'\"]\w*[\"\']\s*/>)", text):
        match = re.match(r"<bookmark\s*mark\s*=[\'\"](.*)[\"\']\s*/>", part)
        if match is not None:
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
    tts_service: services.TTSService | None = None,
    stt_service: services.STTService | None = None,
    *,
    cache_dir: str | PathLike[str] | None = None,
) -> VoiceoverData:
    if cache_dir is None:
        cache_dir = Path(manim.config.media_dir) / "manim_speech"
    elif not isinstance(cache_dir, Path):
        cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    cleaned_text = remove_bookmarks(text)
    slug = f"{slugify.slugify(cleaned_text, max_length=50, word_boundary=True, save_order=True)}-{hashlib.sha256(cleaned_text.encode()).hexdigest()[:8]}"
    cache_path = cache_dir / slug
    if not cache_path.exists():
        cache_path.mkdir(parents=True)
        with (cache_path / "text.txt").open("w") as f:
            f.write(cleaned_text)

    manim.logger.info(
        f'Processing voiceover "{f"{cleaned_text[:50]}..." if len(cleaned_text) > 50 else cleaned_text}" stored at {slug}...'
    )

    audio_path = cache_path / "audio.mp3"
    if not audio_path.exists():
        manim.logger.info(f'Audio file for "{slug}" not found.')
        if tts_service is not None:
            manim.logger.info(f"Generating audio using {tts_service.service_name} TTS service...")
            tts_service.tts(cleaned_text, audio_path)
        else:
            manim.logger.info(f'No TTS service specified. Skipping "{slug}".')
            return VoiceoverData(
                path=cache_path,
                transcript=services.Transcript(text="", boundaries=[]),
                duration=1e-6,
                bookmarks={},
            )

    transcript_path = cache_path / "transcript.json"
    if transcript_path.exists():
        with transcript_path.open() as f:
            transcript = services.Transcript.model_validate_json(f.read())
    else:
        manim.logger.info(f'Transcript file for "{slug}" not found.')
        if stt_service is not None:
            manim.logger.info(f"Generating transcript using {stt_service.service_name} STT service...")
            transcript = stt_service.stt(audio_path)
            with transcript_path.open("w") as f:
                f.write(transcript.model_dump_json(indent=4))
        else:
            manim.logger.info(f'No STT service specified. Using default method for "{slug}".')
            transcript = services.Transcript(
                text=cleaned_text,
                boundaries=[
                    services.Boundary(
                        text=cleaned_text,
                        start=0.0,
                        end=File(audio_path).info.length,
                        text_start=0,
                    )
                ],
            )

    return VoiceoverData(
        path=cache_path,
        transcript=transcript,
        duration=File(audio_path).info.length,
        bookmarks=get_bookmark_times(text, transcript),
    )
