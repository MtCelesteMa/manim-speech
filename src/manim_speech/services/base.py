"""Base classes for services."""

import pathlib
from abc import ABC, abstractmethod

import pydantic


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
    def tts(self, text: str, out_path: pathlib.Path | str) -> None: ...


class Boundary(pydantic.BaseModel):
    text: str
    start: float
    end: float
    text_start: int

    @pydantic.computed_field
    @property
    def length(self) -> int:
        return len(self.text)

    @pydantic.computed_field
    @property
    def text_end(self) -> int:
        return self.text_start + self.length


class STTResults(pydantic.BaseModel):
    text: str
    boundaries: list[Boundary]


class STTService(Service):
    @property
    def service_type(self) -> str:
        return "STT"

    @abstractmethod
    def stt(self, in_path: pathlib.Path | str) -> STTResults: ...


class TranslationService(Service):
    @property
    def service_type(self) -> str:
        return "Translation"

    @abstractmethod
    def translate(
        self, text: str, *, src_lang: str | None = None, dst_lang: str | None = None
    ) -> str: ...
