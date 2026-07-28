"""ElevenLabs services."""

import os
from os import PathLike
from pathlib import Path

from .base import Boundary, Service, STTService, Transcript, TTSService

try:
    import elevenlabs
    from elevenlabs.client import ElevenLabs
    from elevenlabs.types import SpeechToTextChunkResponseModel
except ImportError:
    raise ImportError("Please install elevenlabs with `pip install elevenlabs`")


class ElevenLabsService(Service):
    def __init__(self, *, api_key: str | None = None) -> None:
        if api_key is None:
            api_key = os.getenv("ELEVEN_API_KEY")
            if api_key is None:
                raise ValueError("ElevenLabs API key is not provided")

        self.client = ElevenLabs(api_key=api_key)

    @property
    def service_name(self) -> str:
        return "ElevenLabs"


class ElevenLabsTTSService(TTSService, ElevenLabsService):
    def __init__(self, voice: str, model: str = "eleven_v3", *, api_key: str | None = None, **kwargs) -> None:
        super().__init__(api_key=api_key)
        self.voice = voice
        self.model = model
        self.kwargs = kwargs

    def tts(self, text: str, out_path: str | PathLike[str]) -> None:
        audio = self.client.text_to_speech.convert(text=text, voice_id=self.voice, model_id=self.model, **self.kwargs)
        elevenlabs.save(audio, os.fspath(out_path))


class ElevenLabsSTTService(STTService, ElevenLabsService):
    def __init__(
        self, model: str = "scribe_v2", language: str | None = None, *, api_key: str | None = None, **kwargs
    ) -> None:
        super().__init__(api_key=api_key)
        self.model = model
        self.language = language
        self.kwargs = kwargs

    def stt(self, in_path: str | PathLike[str]) -> Transcript:
        if not isinstance(in_path, Path):
            in_path = Path(in_path)

        with in_path.open("rb") as f:
            response: SpeechToTextChunkResponseModel = self.client.speech_to_text.convert(
                file=f, model_id=self.model, language_code=self.language, timestamps_granularity="word", **self.kwargs
            )

        boundaries: list[Boundary] = []
        text_offset = 0
        for word in response.words:
            assert word.start is not None and word.end is not None
            text_start = response.text.find(word.text, text_offset)
            boundaries.append(Boundary(text=word.text, start=word.start, end=word.end, text_start=text_start))
            text_offset = text_start + len(word.text)

        return Transcript(text=response.text, boundaries=boundaries)
