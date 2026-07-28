"""Whisper services."""

import os
from os import PathLike

from .base import Boundary, Service, STTService, Transcript

try:
    import whisper
except ImportError:
    raise ImportError("Please install whisper with `pip install whisper`")


class WhisperService(Service):
    @property
    def service_name(self) -> str:
        return "Whisper"


class WhisperSTTService(STTService, WhisperService):
    def __init__(
        self, model: str = "base", language: str | None = None, *, device: str | None = None, **kwargs
    ) -> None:
        self.model_obj = whisper.load_model(model, device=device)
        self.language = language
        self.kwargs = kwargs

    def stt(self, in_path: str | PathLike[str]) -> Transcript:
        transcript = self.model_obj.transcribe(os.fspath(in_path), word_timestamps=True, **self.kwargs)

        word_boundaries: list[Boundary] = []
        text_offset = 0
        for segment in transcript["segments"]:
            for word in segment["words"]:
                text_start: int = transcript["text"].find(word["word"], text_offset)
                word_boundaries.append(
                    Boundary(
                        text=word["word"],
                        start=word["start"],
                        end=word["end"],
                        text_start=text_start,
                    )
                )
                text_offset = text_start + len(word["word"])

        return Transcript(text=transcript["text"], boundaries=word_boundaries)
