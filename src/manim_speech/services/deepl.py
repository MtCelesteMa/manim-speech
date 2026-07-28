"""DeepL services."""

import os
import typing

from .base import Service, TranslationService

try:
    import deepl
except ImportError:
    raise ImportError("Please install deepl with `pip install deepl`")


class DeepLService(Service):
    def __init__(self, *, api_key: str | None = None) -> None:
        if api_key is None:
            api_key = os.getenv("DEEPL_API_KEY")
            if api_key is None:
                raise ValueError("DeepL API key is not provided")

        self.client = deepl.Translator(api_key)

    @property
    def service_name(self) -> str:
        return "DeepL"


class DeepLTranslationService(TranslationService, DeepLService):
    def __init__(self, *, api_key: str | None = None, **kwargs) -> None:
        super().__init__(api_key=api_key)
        self.kwargs = kwargs

    def translate(self, text: str, src_lang: str, dst_lang: str) -> str:
        result = self.client.translate_text(
            text,
            source_lang=src_lang,
            target_lang=dst_lang,
            tag_handling="xml",
            tag_handling_version="v2",
            **self.kwargs,
        )
        return typing.cast(deepl.TextResult, result).text
