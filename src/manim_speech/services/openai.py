"""OpenAI services."""

import os
import pathlib

from . import base

try:
    import openai
except ImportError:
    raise ImportError("Please install openai with `pip install openai`.")


class OpenAIService(base.Service):
    def __init__(self, *, api_key: str | None = None, base_url: str | None = None) -> None:
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key is None:
                raise ValueError("OpenAI API key is not provided")

        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)

    @property
    def service_name(self) -> str:
        return "OpenAI"


class OpenAITTSService(base.TTSService, OpenAIService):
    def __init__(
        self,
        voice: str = "alloy",
        model: str = "gpt-4o-mini-tts",
        speed: float = 1.0,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        super().__init__(api_key=api_key, base_url=base_url)
        self.voice = voice
        self.model = model
        self.speed = speed

    def tts(self, text: str, out_path: pathlib.Path | str) -> None:
        if isinstance(out_path, str):
            out_path = pathlib.Path(out_path)

        with self.client.audio.speech.with_streaming_response.create(
            input=text, model=self.model, voice=self.voice, speed=self.speed
        ) as response:
            response.stream_to_file(out_path)


class OpenAISTTService(base.STTService, OpenAIService):
    def __init__(
        self,
        model: str = "whisper-1",
        language: str | None = None,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        super().__init__(api_key=api_key, base_url=base_url)
        self.model = model
        self.language = language

    def stt(self, in_path: pathlib.Path | str) -> base.Transcript:
        if isinstance(in_path, str):
            in_path = pathlib.Path(in_path)

        with in_path.open("rb") as af:
            response = self.client.audio.transcriptions.create(
                file=af,
                model=self.model,
                language=self.language if self.language is not None else openai.omit,
                response_format="verbose_json",
                timestamp_granularities=["word"],
            )

        boundaries: list[base.Boundary] = []
        text_offset = 0
        assert response.words is not None
        for word in response.words:
            text_start = response.text.find(word.word, text_offset)
            boundaries.append(
                base.Boundary(
                    text=word.word,
                    start=word.start,
                    end=word.end,
                    text_start=text_start,
                )
            )
            text_offset = text_start + len(word.word)

        return base.Transcript(text=response.text, boundaries=boundaries)
