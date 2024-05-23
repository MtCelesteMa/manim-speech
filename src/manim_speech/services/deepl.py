"""DeepL services."""

from . import base

import os
import pathlib
from abc import ABC, abstractmethod

try:
    import deepl
except ImportError:
    raise ImportError("Please install deepl with `pip install deepl`")


class DeepLService(base.Service, ABC):
    def __init__(self, *, cache_dir: pathlib.Path | str | None = None, api_key: str | None = None) -> None:
        super().__init__(cache_dir=cache_dir)
        if not isinstance(api_key, str):
            api_key = os.getenv("DEEPL_API_KEY")
            if not isinstance(api_key, str):
                raise ValueError("DeepL API key is not provided")
        self.api_key = api_key
    
    @property
    def service_name(self) -> str:
        return "DeepL"


class DeepLTranslationService(base.TranslationService, DeepLService):
    def __init__(self, *, cache_dir: pathlib.Path | str | None = None, api_key: str | None = None) -> None:
        super().__init__(cache_dir=cache_dir, api_key=api_key)
        self.client = deepl.Translator(auth_key=self.api_key)

    def translate(self, input: base.TranslationInput) -> base.TranslationData:
        info = base.ServiceInfo(
            service_name=self.service_name,
            service_type=self.service_type,
            config={}
        )
        if input.target_language == "zh_tw":
            try:
                import opencc
            except ImportError:
                raise ImportError("Please install opencc with `pip install opencc`")
            result = self.client.translate_text(input.text, source_lang=input.source_language, target_lang="zh", tag_handling="xml")
            return base.TranslationData(info=info, input=input, output=base.TranslationOutput(translated_text=opencc.OpenCC("s2t.json").convert(result.text)))
        target_language = input.target_language
        if target_language == "zh_cn":
            target_language = "zh"
        result = self.client.translate_text(input.text, source_lang=input.source_language, target_lang=target_language, tag_handling="xml")
        return base.TranslationData(info=info, input=input, output=base.TranslationOutput(translated_text=result.text))
