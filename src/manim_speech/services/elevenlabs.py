"""ElevenLabs services."""

from . import base

import os
import pathlib
from abc import ABC, abstractmethod

try:
    import elevenlabs.client
except ImportError:
    raise ImportError("Please install elevenlabs with `pip install elevenlabs`")


class ElevenLabsService(base.Service, ABC):
    def __init__(self, *, cache_dir: pathlib.Path | str | None = None, api_key: str | None = None) -> None:
        super().__init__(cache_dir=cache_dir)
        if not isinstance(api_key, str):
            api_key = os.getenv("ELEVEN_API_KEY")
            if not isinstance(api_key, str):
                raise ValueError("ElevenLabs API key is not provided")
        self.api_key = api_key

        self.client = elevenlabs.client.ElevenLabs(api_key=self.api_key)
    
    @property
    def service_name(self) -> str:
        return "ElevenLabs"


class ElevenLabsTTSService(base.TTSService, ElevenLabsService):
    def __init__(
            self,
            voice: str,
            model: str = "eleven_multilingual_v2",
            *,
            cache_dir: pathlib.Path | str | None = None,
            api_key: str | None = None
    ) -> None:
        super().__init__(cache_dir=cache_dir, api_key=api_key)
        self.voice = voice
        self.model = model

    def tts(self, input: base.TTSInput) -> base.TTSData:
        file_name = self.get_file_name(input)

        data = base.TTSData(
            info=base.ServiceInfo(
                service_name=self.service_name,
                service_type=self.service_type,
                config={
                    "voice": self.voice,
                    "model": self.model
                }
            ),
            input=input,
            output=base.TTSOutput(audio_path=file_name)
        )

        if not (self.cache_dir / file_name).exists():
            response = self.client.generate(
                text=input.text,
                voice=self.voice,
                model=self.model
            )
            elevenlabs.save(response, str(self.cache_dir / file_name))
        
        return data
