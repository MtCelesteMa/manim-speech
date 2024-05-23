"""AssemblyAI services."""

from . import base

import os
import typing
import pathlib
from abc import ABC, abstractmethod

try:
    import assemblyai as aai
except ImportError:
    raise ImportError("Please install assemblyai with `pip install assemblyai`")


class AssemblyAIService(base.Service, ABC):
    def __init__(self, *, cache_dir: pathlib.Path | str | None = None, api_key: str | None = None) -> None:
        super().__init__(cache_dir=cache_dir)
        if not isinstance(api_key, str):
            api_key = os.getenv("ASSEMBLYAI_API_KEY")
            if not isinstance(api_key, str):
                raise ValueError("AssemblyAI API key is not provided")
        self.api_key = api_key
    
    @property
    def service_name(self) -> str:
        return "AssemblyAI"


class AssemblyAISTTService(base.STTService, AssemblyAIService):
    def __init__(
            self,
            model: typing.Literal["best", "nano"] = "best",
            language: str | None = None,
            word_boost: list[str] | None = None,
            custom_spelling: dict[str, str | list[str]] | None = None,
            *,
            cache_dir: pathlib.Path | str | None = None,
            api_key: str | None = None
    ) -> None:
        super().__init__(cache_dir=cache_dir, api_key=api_key)
        self.model = model
        self.language = language
        self.word_boost = word_boost if isinstance(word_boost, list) else []
        self.custom_spelling = custom_spelling if isinstance(custom_spelling, dict) else {}

        self.config = aai.TranscriptionConfig(
            speech_model=aai.SpeechModel.best if model == "best" else aai.SpeechModel.nano,
            language_code=language if isinstance(language, str) else None,
            language_detection=isinstance(language, type(None)),
            word_boost=self.word_boost,
            custom_spelling=self.custom_spelling,
            punctuate=False
        )

    def stt(self, input: base.STTInput) -> base.STTData:
        info = base.ServiceInfo(
            service_name=self.service_name,
            service_type=self.service_type,
            config={
                "model": self.model,
                "language": self.language,
                "word_boost": self.word_boost,
                "custom_spelling": self.custom_spelling
            }
        )

        aai.settings.api_key = self.api_key
        transcriber = aai.Transcriber(config=self.config)
        response = transcriber.transcribe(str(self.cache_dir / input.audio_path))
        if response.error:
            raise ValueError(response.error)

        word_boundaries: list[base.Boundary] = []
        text_offset = 0
        for word in response.words:
            word_boundaries.append(
                base.Boundary(
                    text=word.text,
                    start=word.start / 1000,
                    end=word.end / 1000,
                    text_offset=text_offset
                )
            )
            if text_offset != 0 and response.text[text_offset] == " ":
                text_offset += 1
            text_offset += len(word.text)
    
        return base.STTData(
            info=info,
            input=input,
            output=base.STTOutput(text=response.text, boundaries=word_boundaries)
        )
