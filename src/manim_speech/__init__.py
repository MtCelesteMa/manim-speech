"""Manim plugin for adding speech to videos."""

from . import services
from .scene import TranslationScene, VoiceoverScene

__all__ = ["services", "TranslationScene", "VoiceoverScene"]
