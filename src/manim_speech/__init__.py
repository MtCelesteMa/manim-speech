"""Manim plugin for adding speech to videos."""

from . import services, speech, translation
from .scene import TranslationScene, VoiceoverScene

__all__ = ["services", "speech", "translation", "TranslationScene", "VoiceoverScene"]
