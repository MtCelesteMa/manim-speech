"""OpenAI services."""

import os
import pathlib

from . import base

try:
    import openai
except ImportError:
    raise ImportError("Please install openai with `pip install openai`.")


class OpenAIService(base.Service):
    def __init__(
        self, *, api_key: str | None = None, base_url: str | None = None
    ) -> None:
        if not isinstance(api_key, str):
            api_key = os.getenv("OPENAI_API_KEY")
            if not isinstance(api_key, str):
                raise ValueError("OpenAI API key is not provided")
        self.api_key = api_key
        self.base_url = base_url

        self.client = openai.OpenAI(api_key=self.api_key, base_url=base_url)

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
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        super().__init__(api_key=api_key, base_url=base_url)
        self.voice = voice
        self.model = model
        self.speed = speed

    def tts(self, text: str, out_path: pathlib.Path | str) -> None:
        if isinstance(out_path, str):
            out_path = pathlib.Path(out_path)

        self.client.audio.speech.create(
            input=text, model=self.model, voice=self.voice, speed=self.speed
        ).stream_to_file(out_path)


class OpenAISTTService(base.STTService, OpenAIService):
    def __init__(
        self,
        model: str = "whisper-1",
        language: str | None = None,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        super().__init__(api_key=api_key, base_url=base_url)
        self.model = model
        self.language = language

    def stt(self, in_path: pathlib.Path | str) -> base.Transcript:
        if isinstance(in_path, str):
            in_path = pathlib.Path(in_path)

        with in_path.open("rb") as af:
            if isinstance(self.language, str):
                response = self.client.audio.transcriptions.create(
                    file=af,
                    model=self.model,
                    language=self.language,
                    response_format="verbose_json",
                    timestamp_granularities=["word"],
                )
            else:
                response = self.client.audio.transcriptions.create(
                    file=af,
                    model=self.model,
                    response_format="verbose_json",
                    timestamp_granularities=["word"],
                )

        boundaries: list[base.Boundary] = []
        text_offset = 0
        for word in response.words:
            text_start = response.text.find(word["word"], text_offset)
            boundaries.append(
                base.Boundary(
                    text=word["word"],
                    start=word["start"],
                    end=word["end"],
                    text_start=text_start,
                )
            )
            text_offset = text_start + len(word["word"])

        return base.Transcript(text=response.text, boundaries=boundaries)


class OpenAITranslationService(base.TranslationService, OpenAIService):
    def __init__(
        self,
        model: str = "gpt-4o",
        src_lang: str | None = None,
        dst_lang: str | None = None,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        super().__init__(api_key=api_key, base_url=base_url)
        self.model = model
        self.src_lang = src_lang
        self.dst_lang = dst_lang
        self.system_message = """Translate the given text from {src_lang} to {dst_lang}. Do not output anything other than the translated text.
        If you encounter XML tags, do not translate their contents and insert them appropriately in the translated text. Do NOT skip any XML tags."""

    def translate(
        self, text: str, *, src_lang: str | None = None, dst_lang: str | None = None
    ) -> str:
        src_lang = src_lang if isinstance(src_lang, str) else self.src_lang
        dst_lang = dst_lang if isinstance(dst_lang, str) else self.dst_lang
        if isinstance(src_lang, type(None)) or isinstance(dst_lang, type(None)):
            raise ValueError("Either 'src_lang' or 'dst_lang' were not specified.")

        result = (
            self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": self.system_message.format(
                            src_lang=src_lang, dst_lang=dst_lang
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                model=self.model,
                max_tokens=4095,
            )
            .choices[0]
            .message.content
        )
        if isinstance(result, type(None)):
            raise ValueError(f"Unexpected response: {result}")
        return result
