"""OpenAI services."""

import os
from os import PathLike
from pathlib import Path

from .base import Boundary, Service, STTService, Transcript, TTSService

try:
    import openai
    from openai import OpenAI
    from openai.types.audio import TranscriptionVerbose
    from openai.types.audio.speech_create_params import VoiceID
except ImportError:
    raise ImportError("Please install openai with `pip install openai`.")


class OpenAIService(Service):
    def __init__(self, *, api_key: str | None = None, base_url: str | None = None) -> None:
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key is None:
                raise ValueError("OpenAI API key is not provided")

        self.client = OpenAI(api_key=api_key, base_url=base_url)

    @property
    def service_name(self) -> str:
        return "OpenAI"


class OpenAITTSService(TTSService, OpenAIService):
    def __init__(
        self,
        voice: str | VoiceID = "alloy",
        model: str = "gpt-4o-mini-tts",
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(api_key=api_key, base_url=base_url)
        self.voice = voice
        self.model = model
        self.kwargs = kwargs

    def tts(self, text: str, out_path: str | PathLike[str]) -> None:
        with self.client.audio.speech.with_streaming_response.create(
            input=text, model=self.model, voice=self.voice, **self.kwargs
        ) as response:
            response.stream_to_file(out_path)


class OpenAISTTService(STTService, OpenAIService):
    def __init__(
        self,
        model: str = "whisper-1",
        language: str | None = None,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(api_key=api_key, base_url=base_url)
        self.model = model
        self.language = language
        self.kwargs = kwargs

    def stt(self, in_path: str | PathLike[str]) -> Transcript:
        if not isinstance(in_path, Path):
            in_path = Path(in_path)

        with in_path.open("rb") as f:
            response: TranscriptionVerbose = self.client.audio.transcriptions.create(
                file=f,
                model=self.model,
                language=self.language if self.language is not None else openai.omit,
                response_format="verbose_json",
                timestamp_granularities=["word"],
                **self.kwargs,
            )

        boundaries: list[Boundary] = []
        text_offset = 0
        assert response.words is not None
        for word in response.words:
            text_start = response.text.find(word.word, text_offset)
            boundaries.append(
                Boundary(
                    text=word.word,
                    start=word.start,
                    end=word.end,
                    text_start=text_start,
                )
            )
            text_offset = text_start + len(word.word)

        return Transcript(text=response.text, boundaries=boundaries)
