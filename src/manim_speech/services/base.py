"""Base classes for services."""

import pathlib
import hashlib
from abc import ABC, abstractmethod

import manim
import pydantic


class ServiceInfo(pydantic.BaseModel):
    service_name: str
    service_type: str
    config: pydantic.JsonValue


class Service(ABC):
    def __init__(self, *, cache_dir: pathlib.Path | str | None = None) -> None:
        if isinstance(cache_dir, type(None)):
            cache_dir = pathlib.Path(manim.config.media_dir) / "manim_speech"
        elif isinstance(cache_dir, str):
            cache_dir = pathlib.Path(cache_dir)
        self.cache_dir = cache_dir

        if not self.cache_dir.exists():
            self.cache_dir.mkdir(parents=True)
    
    @property
    @abstractmethod
    def service_name(self) -> str:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def service_type(self) -> str:
        raise NotImplementedError


class TTSInput(pydantic.BaseModel):
    text: str


class TTSOutput(pydantic.BaseModel):
    audio_path: pathlib.Path


class TTSData(pydantic.BaseModel):
    info: ServiceInfo | None
    input: TTSInput
    output: TTSOutput


class TTSService(Service, ABC):
    @property
    def service_type(self) -> str:
        return "TTS"
    
    @staticmethod
    def get_file_name(input: TTSInput) -> pathlib.Path:
        return pathlib.Path(f"{hashlib.sha256(input.text.encode()).hexdigest()}.mp3")
    
    @abstractmethod
    def tts(self, input: TTSInput) -> TTSData:
        raise NotImplementedError


class Boundary(pydantic.BaseModel):
    text: str
    start: float
    end: float
    text_offset: int

    @property
    def length(self) -> int:
        return len(self.text)


class STTInput(pydantic.BaseModel):
    audio_path: pathlib.Path


class STTOutput(pydantic.BaseModel):
    text: str
    boundaries: list[Boundary]


class STTData(pydantic.BaseModel):
    info: ServiceInfo | None
    input: STTInput
    output: STTOutput


class STTService(Service, ABC):
    @property
    def service_type(self) -> str:
        return "STT"
    
    @abstractmethod
    def stt(self, input: STTInput) -> STTData:
        raise NotImplementedError


class TranslationInput(pydantic.BaseModel):
    text: str
    source_language: str
    target_language: str


class TranslationOutput(pydantic.BaseModel):
    translated_text: str


class TranslationData(pydantic.BaseModel):
    info: ServiceInfo | None
    input: TranslationInput
    output: TranslationOutput


class TranslationService(Service, ABC):
    @property
    def service_type(self) -> str:
        return "Translation"
    
    @abstractmethod
    def translate(self, input: TranslationInput) -> TranslationData:
        raise NotImplementedError
