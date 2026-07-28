"""AssemblyAI services."""

import os
from os import PathLike

from .base import Boundary, Service, STTService, Transcript

try:
    import assemblyai as aai
except ImportError:
    raise ImportError("Please install assemblyai with `pip install assemblyai`")


class AssemblyAIService(Service):
    def __init__(self, *, api_key: str | None = None) -> None:
        if api_key is None:
            api_key = os.getenv("ASSEMBLYAI_API_KEY")
            if api_key is None:
                raise ValueError("AssemblyAI API key is not provided")

        self.api_key = api_key

    @property
    def service_name(self) -> str:
        return "AssemblyAI"


class AssemblyAISTTService(STTService, AssemblyAIService):
    def __init__(
        self, model: str = "universal-3-5-pro", language: str | None = None, *, api_key: str | None = None, **kwargs
    ) -> None:
        super().__init__(api_key=api_key)
        self.config = aai.TranscriptionConfig(
            speech_models=[model],
            language_code=language,
            language_detection=(language is None),
            punctuate=False,
            **kwargs,
        )

    def stt(self, in_path: str | PathLike[str]) -> Transcript:
        aai.settings.api_key = self.api_key
        response = aai.Transcriber(config=self.config).transcribe(os.fspath(in_path))
        if response.error:
            raise ValueError(response.error)

        word_boundaries: list[Boundary] = []
        text_offset = 0
        assert response.words is not None and response.text is not None
        for word in response.words:
            text_start = response.text.find(word.word, text_offset)
            word_boundaries.append(
                Boundary(
                    text=word.text,
                    start=word.start / 1000,
                    end=word.end / 1000,
                    text_start=text_start,
                )
            )
            text_offset = text_start + len(word.text)

        return Transcript(text=response.text, boundaries=word_boundaries)
