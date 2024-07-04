"""manim.Scene subclasses for voiceover and translation."""

import contextlib
import gettext
import pathlib
from collections import abc

import manim

from . import services, translation, voiceover


class VoiceoverScene(manim.Scene):
    tts_service: services.base.TTSService | None = None
    stt_service: services.base.STTService | None = None
    current_voiceover_data: voiceover.VoiceoverData | None = None
    current_voiceover_start_time: float | None = None

    def set_tts_service(self, service: services.base.TTSService) -> None:
        self.tts_service = service

    def set_stt_service(self, service: services.base.STTService) -> None:
        self.stt_service = service

    def safe_wait(self, duration: float) -> None:
        if duration > 1 / manim.config.frame_rate:
            self.wait(duration)

    def wait_for_voiceover(self) -> None:
        if not isinstance(self.current_voiceover_data, type(None)) and not isinstance(
            self.current_voiceover_start_time, type(None)
        ):
            self.safe_wait(
                self.current_voiceover_data.duration
                - (self.renderer.time - self.current_voiceover_start_time)
            )

    def wait_until_bookmark(self, key: str) -> None:
        if not isinstance(self.current_voiceover_data, type(None)) and not isinstance(
            self.current_voiceover_start_time, type(None)
        ):
            self.safe_wait(
                self.current_voiceover_data.bookmarks.get(key, 0.0)
                - (self.renderer.time - self.current_voiceover_start_time)
            )

    @contextlib.contextmanager
    def voiceover(self, text: str) -> abc.Generator[voiceover.VoiceoverData, None, None]:
        if not isinstance(self.stt_service, services.base.STTService):
            manim.logger.warning(
                "No STT service is set. Bookmark locations will be inaccurate."
            )
        try:
            self.current_voiceover_data = voiceover.create(
                text, self.tts_service, self.stt_service
            )
            self.current_voiceover_start_time = self.renderer.time
            if (self.current_voiceover_data.path / "audio.mp3").exists():
                self.add_sound(str(self.current_voiceover_data.path / "audio.mp3"))
            yield self.current_voiceover_data
        finally:
            self.wait_for_voiceover()
            self.current_voiceover_data = None
            self.current_voiceover_start_time = None


class TranslationScene(manim.Scene):
    translation_service: services.base.TranslationService | None = None
    _ = staticmethod(gettext.gettext)

    def set_translation_service(
        self, service: services.base.TranslationService
    ) -> None:
        self.translation_service = service

    def translate(
        self,
        file: pathlib.Path | str,
        domain: str,
        source_language: str,
        target_language: str,
    ) -> None:
        translation.init_translation_env(file, domain)
        translation.translate_po_file(
            domain, source_language, target_language, service=self.translation_service
        )
        trans = gettext.translation(
            domain, languages=[target_language], localedir="locales"
        )
        self._ = trans.gettext
