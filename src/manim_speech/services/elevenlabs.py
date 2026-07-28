"""ElevenLabs services."""

import os
import pathlib
from abc import ABC

from . import base

try:
    import elevenlabs
    from elevenlabs.client import ElevenLabs
    from elevenlabs.types import SpeechToTextChunkResponseModel
except ImportError:
    raise ImportError("Please install elevenlabs with `pip install elevenlabs`")


class ElevenLabsService(base.Service, ABC):
    def __init__(self, *, api_key: str | None = None) -> None:
        if api_key is None:
            api_key = os.getenv("ELEVEN_API_KEY")
            if api_key is None:
                raise ValueError("ElevenLabs API key is not provided")

        self.client = ElevenLabs(api_key=api_key)

    @property
    def service_name(self) -> str:
        return "ElevenLabs"


class ElevenLabsTTSService(base.TTSService, ElevenLabsService):
    def __init__(
        self,
        voice_id: str,
        model_id: str = "eleven_v3",
        output_format: str = "mp3_44100_128",
        *,
        api_key: str | None = None,
    ) -> None:
        super().__init__(api_key=api_key)
        self.voice_id = voice_id
        self.model_id = model_id
        self.output_format = output_format

    def tts(self, text: str, out_path: pathlib.Path | str) -> None:
        audio = self.client.text_to_speech.convert(
            text=text, voice_id=self.voice_id, model_id=self.model_id, output_format=self.output_format
        )
        elevenlabs.save(audio, str(out_path))


class ElevenLabsSTTService(base.STTService, ElevenLabsService):
    def __init__(
        self,
        model_id: str = "scribe_v2",
        language: str | None = None,
        *,
        api_key: str | None = None,
    ) -> None:
        super().__init__(api_key=api_key)
        self.model_id = model_id
        self.language = language

    def stt(self, in_path: pathlib.Path | str) -> base.Transcript:
        if not isinstance(in_path, pathlib.Path):
            in_path = pathlib.Path(in_path)

        with in_path.open("rb") as f:
            response: SpeechToTextChunkResponseModel = self.client.speech_to_text.convert(
                file=f, model_id=self.model_id, language_code=self.language, timestamps_granularity="word"
            )

        boundaries: list[base.Boundary] = []
        text_offset = 0
        for word in response.words:
            assert word.start is not None and word.end is not None
            text_start = response.text.find(word.text, text_offset)
            boundaries.append(base.Boundary(text=word.text, start=word.start, end=word.end, text_start=text_start))
            text_offset = text_start + len(word.text)

        return base.Transcript(text=response.text, boundaries=boundaries)
