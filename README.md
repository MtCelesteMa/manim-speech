# Manim Speech

Manim plugin for adding speech to videos.

Special thanks to [osolmaz](https://github.com/osolmaz) and others who worked on [Manim Voiceover](https://github.com/ManimCommunity/manim-voiceover), which Manim Speech is heavily based on.

## Installation

Manim Speech can be installed via pip using the following command:
```shell
pip install "manim_speech[*optional_dependency_sets*]"
```

Where `*optional_dependency_sets*` is a list of optional dependency sets for Manim Speech.

## Features

* Adding AI-generated voiceovers to Manim animations.
* Translating text between languages.

### Services

| Service Name | Optional Dependency Set | Is Local | Text-To-Speech | Speech-To-Text | Translation |
|--------------|-------------------------|----------|----------------|----------------|-------------|
| OpenAI       | `openai`                | No       | Yes            | Yes            | No          |
| ElevenLabs   | `elevenlabs`            | No       | Yes            | No             | No          |
| Whisper      | `whisper`               | Yes      | No             | Yes            | No          |
| AssemblyAI   | `assemblyai`            | No       | No             | Yes            | No          |
| DeepL        | `deepl`                 | No       | No             | No             | Yes         |

**Note:** Translating to Traditional Chinese (`zh_tw`) using the DeepL service requires the `chinese` optional dependency set to be installed.

## Usage Examples

Creating a basic scene with a voiceover with Manim Speech:
```python
import manim
import manim_speech
from manim_speech.services import openai as openai_service

class MeaningOfLife(manim_speech.VoiceoverScene):
    def construct(self) -> None:
        self.set_tts_service(openai_service.OpenAITTSService())
        self.set_stt_service(openai_service.OpenAISTTService())

        with self.voiceover("What is the meaning of life?") as speech_data:
            txt = manim.Text("The meaning of life is 42.")
            self.play(manim.Write(txt), run_time=speech_data.duration)
            self.wait_for_voiceover()
            self.play(manim.FadeOut(txt))
```

The same scene, but translated into Traditional Chinese:
```python
import manim
import manim_speech
from manim_speech.services import openai as openai_service
from manim_speech.services import deepl as deepl_service

class MeaningOfLife(manim_speech.VoiceoverScene, manim_speech.TranslationScene):
    def construct(self) -> None:
        self.set_tts_service(openai_service.OpenAITTSService())
        self.set_stt_service(openai_service.OpenAISTTService())
        self.set_translation_service(deepl_service.DeepLTranslationService())

        self.translate(__file__, "meaning_of_life", "en", "zh_tw")
        _ = self._

        with self.voiceover(_("What is the meaning of life?")) as speech_data:
            txt = manim.Text(_("The meaning of life is 42."))
            self.play(manim.Write(txt), run_time=speech_data.duration)
            self.wait_for_voiceover()
            self.play(manim.FadeOut(txt))
```
