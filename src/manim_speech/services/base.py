"""Base classes for services."""

from abc import ABC, abstractmethod
from os import PathLike

from pydantic import BaseModel, computed_field


class Service(ABC):
    @property
    @abstractmethod
    def service_name(self) -> str: ...

    @property
    @abstractmethod
    def service_type(self) -> str: ...


class TTSService(Service):
    @property
    def service_type(self) -> str:
        return "TTS"

    @abstractmethod
    def tts(self, text: str, out_path: str | PathLike[str]) -> None: ...


class Boundary(BaseModel):
    text: str
    start: float
    end: float
    text_start: int

    @computed_field
    @property
    def length(self) -> int:
        return len(self.text)

    @computed_field
    @property
    def text_end(self) -> int:
        return self.text_start + self.length


class Transcript(BaseModel):
    text: str
    boundaries: list[Boundary]


class STTService(Service):
    @property
    def service_type(self) -> str:
        return "STT"

    @abstractmethod
    def stt(self, in_path: str | PathLike[str]) -> Transcript: ...


class TranslationService(Service):
    @property
    def service_type(self) -> str:
        return "Translation"

    @abstractmethod
    def translate(self, text: str, src_lang: str, dst_lang: str) -> str: ...
