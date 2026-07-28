"""Whisper services."""

import pathlib

from . import base

try:
    import whisper
except ImportError:
    raise ImportError("Please install whisper with `pip install whisper`")


class WhisperService(base.Service):
    @property
    def service_name(self) -> str:
        return "Whisper"


class WhisperSTTService(base.STTService, WhisperService):
    def __init__(self, model: str = "base", device: str | None = None) -> None:
        self.model_obj = whisper.load_model(model, device=device)

    def stt(self, in_path: pathlib.Path | str) -> base.Transcript:
        transcript = self.model_obj.transcribe(str(in_path), word_timestamps=True)

        word_boundaries: list[base.Boundary] = []
        text_offset = 0
        for segment in transcript["segments"]:
            for word in segment["words"]:
                text_start: int = transcript["text"].find(word["word"], text_offset)
                word_boundaries.append(
                    base.Boundary(
                        text=word["word"],
                        start=word["start"],
                        end=word["end"],
                        text_start=text_start,
                    )
                )
                text_offset = text_start + len(word["word"])

        return base.Transcript(text=transcript["text"], boundaries=word_boundaries)
