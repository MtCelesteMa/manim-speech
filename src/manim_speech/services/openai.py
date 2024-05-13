"""OpenAI services."""

from . import base

import os
import pathlib
from abc import ABC, abstractmethod

try:
    import openai
except ImportError:
    raise ImportError("Please install openai with `pip install openai`")


class OpenAIService(base.Service, ABC):
    def __init__(self, *, cache_dir: pathlib.Path | str | None = None, api_key: str | None = None) -> None:
        super().__init__(cache_dir=cache_dir)
        if not isinstance(api_key, str):
            api_key = os.getenv("OPENAI_API_KEY")
            if not isinstance(api_key, str):
                raise ValueError("OpenAI API key is not provided")
        self.api_key = api_key

        self.client = openai.OpenAI(api_key=self.api_key)
    
    @property
    def service_name(self) -> str:
        return "OpenAI"


class OpenAITTSService(base.TTSService, OpenAIService):
    def __init__(
            self,
            voice: str = "alloy",
            model: str = "tts-1-hd",
            speed: float = 1.0,
            *,
            cache_dir: pathlib.Path | str | None = None,
            api_key: str | None = None
    ) -> None:
        super().__init__(cache_dir=cache_dir, api_key=api_key)
        self.voice = voice
        self.model = model
        self.speed = speed
    
    def tts(self, input: base.TTSInput) -> base.TTSData:
        file_name = self.get_file_name(input)

        data = base.TTSData(
            info=base.ServiceInfo(
                service_name=self.service_name,
                service_type=self.service_type,
                config={
                    "voice": self.voice,
                    "model": self.model,
                    "speed": self.speed
                }
            ),
            input=input,
            output=base.TTSOutput(audio_path=file_name)
        )

        if not (self.cache_dir / file_name).exists():
            response = self.client.audio.speech.create(
                input=input.text,
                model=self.model,
                voice=self.voice,
                speed=self.speed
            )
            response.stream_to_file(self.cache_dir / file_name)
        
        return data


class OpenAISTTService(base.STTService, OpenAIService):
    def __init__(
            self,
            model: str = "whisper-1",
            *,
            cache_dir: pathlib.Path | str | None = None,
            api_key: str | None = None
    ) -> None:
        super().__init__(cache_dir=cache_dir, api_key=api_key)
        self.model = model
    
    def stt(self, input: base.STTInput) -> base.STTData:
        info = base.ServiceInfo(
            service_name=self.service_name,
            service_type=self.service_type,
            config={"model": self.model}
        )

        response = self.client.audio.transcriptions.create(
            file=(self.cache_dir / input.audio_path).open("rb"),
            model=self.model,
            response_format="verbose_json",
            timestamp_granularities=["word"]
        )

        word_boundaries: list[base.WordBoundary] = []
        text_offset = 0
        for word in response.words:
            word_boundaries.append(
                base.WordBoundary(
                    word=word["word"],
                    start=word["start"],
                    end=word["end"],
                    text_offset=text_offset
                )
            )
            if text_offset != 0 and response.text[text_offset] == " ":
                text_offset += 1
            text_offset += len(word["word"])
        
        return base.STTData(info=info, input=input, output=base.STTOutput(text=response.text, word_boundaries=word_boundaries))
