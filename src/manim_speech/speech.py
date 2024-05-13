"""Speech utils for Manim Speech."""

from . import services

import pathlib
import re

import manim
from scipy import interpolate
import pydantic
from mutagen.mp3 import MP3


class SpeechData(pydantic.BaseModel):
    text: str
    tts_data: services.base.TTSData
    stt_data: services.base.STTData
    duration: float
    bookmark_times: dict[str, float]


def remove_bookmarks(s: str) -> str:
    return re.sub(r"<bookmark\s*mark\s*=['\"]\w*[\"']\s*/>", "", s)


def get_bookmark_times(text: str, tts_data: services.base.TTSData, stt_data: services.base.STTData) -> dict[str, float]:
    interpolator = interpolate.interp1d(
        [wb.text_offset for wb in stt_data.output.word_boundaries],
        [wb.start for wb in stt_data.output.word_boundaries],
        fill_value="extrapolate"
    )

    text_len = len(tts_data.input.text)
    transcribed_text_len = len(stt_data.output.text.strip())

    bookmark_dist: dict[str, int] = {}
    content: str = ""
    for part in re.split(r"(<bookmark\s*mark\s*=[\'\"]\w*[\"\']\s*/>)", text):
        match = re.match(r"<bookmark\s*mark\s*=[\'\"](.*)[\"\']\s*/>", part)
        if not isinstance(match, type(None)):
            bookmark_dist[match.group(1)] = len(content)
        else:
            content += part
        
    bookmark_times: dict[str, float] = {}
    for mark, dist in bookmark_dist.items():
        bookmark_times[mark] = interpolator(dist * transcribed_text_len / text_len)

    return bookmark_times


def load_cache(cache_dir: pathlib.Path) -> list[SpeechData]:
    with (cache_dir / "cache.json").open("r") as f:
        return pydantic.TypeAdapter(list[SpeechData]).validate_json(f.read())


def save_cache(cache_dir: pathlib.Path, data: list[SpeechData]) -> None:
    if not cache_dir.exists():
        cache_dir.mkdir(parents=True)
    with (cache_dir / "cache.json").open("w") as f:
        f.write(pydantic.TypeAdapter(list[SpeechData]).dump_json(data, indent=4).decode("utf-8"))


def create(
        text: str,
        tts_service: services.base.TTSService,
        stt_service: services.base.STTService,
        *,
        cache_dir: pathlib.Path | str | None = None
) -> SpeechData:
    if isinstance(cache_dir, type(None)):
        cache_dir = pathlib.Path(manim.config.media_dir) / "manim_speech"
    elif isinstance(cache_dir, str):
        cache_dir = pathlib.Path(cache_dir)

    if not cache_dir.exists():
        cache_dir.mkdir(parents=True)
    
    if (cache_dir / "cache.json").exists():
        cache = load_cache(cache_dir)
        for data in cache:
            if data.text == text:
                return data
    else:
        cache = []

    input_text = remove_bookmarks(text)
    tts_data = tts_service.tts(services.base.TTSInput(text=input_text))
    stt_data = stt_service.stt(services.base.STTInput(audio_path=tts_data.output.audio_path))
    bookmark_times = get_bookmark_times(text, tts_data, stt_data)

    data = SpeechData(
        text=text,
        tts_data=tts_data,
        stt_data=stt_data,
        duration=MP3(cache_dir / tts_data.output.audio_path).info.length,
        bookmark_times=bookmark_times,
    )
    cache.append(data)
    save_cache(cache_dir, cache)

    return data
