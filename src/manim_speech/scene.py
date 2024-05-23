"""manim.Scene subclass with speech."""

from . import services
from . import speech
from . import translation

from collections import abc
import contextlib
import pathlib
import gettext

import manim


class VoiceoverScene(manim.Scene):
    tts_service: services.base.TTSService | None = None
    stt_service: services.base.STTService | None = None
    current_speech_data: speech.SpeechData | None = None
    current_speech_start_time: float | None = None

    def set_tts_service(self, service: services.base.TTSService) -> None:
        self.tts_service = service
    
    def set_stt_service(self, service: services.base.STTService) -> None:
        self.stt_service = service
    
    def safe_wait(self, duration: float) -> None:
        if duration > 1 / manim.config.frame_rate:
            self.wait(duration)
    
    def wait_for_voiceover(self) -> None:
        if not isinstance(self.current_speech_data, type(None)) and not isinstance(self.current_speech_start_time, type(None)):
            self.safe_wait(self.current_speech_data.duration - (self.renderer.time - self.current_speech_start_time))
    
    def wait_until_bookmark(self, key: str) -> None:
        if not isinstance(self.current_speech_data, type(None)) and not isinstance(self.current_speech_start_time, type(None)):
            self.safe_wait(self.current_speech_data.bookmark_times[key] - (self.renderer.time - self.current_speech_start_time))
    
    @contextlib.contextmanager
    def voiceover(self, text: str) -> abc.Generator[speech.SpeechData, None, None]:
        if not isinstance(self.stt_service, services.base.STTService):
            manim.logger.warning("No STT service is set. Bookmark locations will be inaccurate.")
        try:
            self.current_speech_data = speech.create(text, self.tts_service, self.stt_service)
            self.current_speech_start_time = self.renderer.time
            self.add_sound(str(pathlib.Path(manim.config.media_dir) / "manim_speech" / self.current_speech_data.tts_data.output.audio_path))
            yield self.current_speech_data
        finally:
            self.wait_for_voiceover()
            self.current_speech_data = None
            self.current_speech_start_time = None


class TranslationScene(manim.Scene):
    translation_service: services.base.TranslationService | None = None
    _ = staticmethod(gettext.gettext)

    def set_translation_service(self, service: services.base.TranslationService) -> None:
        self.translation_service = service
    
    def translate(self, file: pathlib.Path | str, domain: str, source_language: str, target_language: str,) -> None:
        translation.init_translation_env(file, domain)
        translation.translate_po_file(domain, source_language, target_language, service=self.translation_service)
        trans = gettext.translation(domain, languages=[target_language], localedir="locales")
        self._ = trans.gettext
