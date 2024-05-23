"""Whisper services."""

from . import base

import pathlib
from abc import ABC, abstractmethod

try:
    import whisper
except ImportError:
    raise ImportError("Please install whisper with `pip install whisper`")


class WhisperService(base.Service, ABC):
    @property
    def service_name(self) -> str:
        return "Whisper"


class WhisperSTTService(base.STTService, WhisperService):
    def __init__(
            self,
            model: str = "base",
            device: str | None = None,
            *,
            cache_dir: pathlib.Path | str | None = None
    ) -> None:
        super().__init__(cache_dir=cache_dir)
        self.model = model
        self.device = device

        self.model_obj = whisper.load_model(self.model, device=self.device)

    def stt(self, input: base.STTInput) -> base.STTData:
        info = base.ServiceInfo(
            service_name=self.service_name,
            service_type=self.service_type,
            config={"model": self.model, "device": self.device}
        )

        transcript = self.model_obj.transcribe(str(self.cache_dir / input.audio_path), word_timestamps=True)

        word_boundaries: list[base.Boundary] = []
        text_offset = 0
        for segment in transcript["segments"]:
            for word in segment["words"]:
                word_boundaries.append(
                    base.Boundary(
                        text=word["word"],
                        start=word["start"],
                        end=word["end"],
                        text_offset=text_offset
                    )
                )
                if text_offset != 0 and response.text[text_offset] == " ":
                    text_offset += 1
                text_offset += len(word["word"])
        
        return base.STTData(info=info, input=input, output=base.STTOutput(text=transcript["text"], boundaries=word_boundaries))

