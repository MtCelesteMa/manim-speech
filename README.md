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

* Integrate voiceovers into Manim animations.

    * Utilize bookmarks to pause for key moments in the voiceover (identical to Manim Voiceover functionality).

* Easily translate text within Manim animations to various languages with minimal code.

* Leverage AI-driven services for text-to-speech, speech-to-text, and translation.

    * Easily utilize services that are not officially supported by subclassing `TTSService`, `STTService`, and `TranslationService`.

### Services

| Service Name | Optional Dependency Set | Is Local | Text-To-Speech | Speech-To-Text | Translation |
|--------------|-------------------------|----------|----------------|----------------|-------------|
| OpenAI       | `openai`                | No*      | Yes            | Yes            | No          |
| ElevenLabs   | `elevenlabs`            | No       | Yes            | Yes            | No          |
| Whisper      | `whisper`               | Yes      | No             | Yes            | No          |
| AssemblyAI   | `assemblyai`            | No       | No             | Yes            | No          |
| DeepL        | `deepl`                 | No       | No             | No             | Yes         |

\* The OpenAI service can use any backend compatible with the OpenAI API through the `base_url` parameter, some of which are local (e.g., LocalAI).

**Note:** This package previously included special procedures for Chinese translations as DeepL formerly did not natively support translating to Traditional Chinese. As they have since added support for Traditional Chinese, the special procedures and the relevant optional dependencies have been removed from this package.

## Usage Examples

Creating a basic scene with a voiceover with Manim Speech:
```python
import manim
from manim_speech import VoiceoverScene
from manim_speech.services.openai import OpenAISTTService, OpenAITTSService


class MeaningOfLife(VoiceoverScene):
    def construct(self) -> None:
        self.set_tts_service(OpenAITTSService())
        self.set_stt_service(OpenAISTTService())

        txt_question = manim.Text("What is the meaning of life?")
        txt_answer = manim.Text("The meaning of life is 42.")

        with self.voiceover("What is the meaning of life?<bookmark mark='reveal_answer' /> The meaning of life is 42."):
            self.play(manim.Write(txt_question), run_time=1.0)
            self.wait_until_bookmark("reveal_answer")
            self.play(manim.ReplacementTransform(txt_question, txt_answer), run_time=1.0)
            self.wait_for_voiceover()
```

The same scene, but translated into Traditional Chinese:
```python
import manim
from manim_speech import TranslationScene, VoiceoverScene
from manim_speech.services.deepl import DeepLTranslationService
from manim_speech.services.openai import OpenAISTTService, OpenAITTSService

class MeaningOfLife(VoiceoverScene, TranslationScene):
    def construct(self) -> None:
        self.set_tts_service(OpenAITTSService())
        self.set_stt_service(OpenAISTTService())
        self.set_translation_service(DeepLTranslationService())

        self.translate(__file__, "meaning_of_life", "en", "zh-HANT")
        _ = self._

        txt_question = manim.Text(_("What is the meaning of life?"))
        txt_answer = manim.Text(_("The meaning of life is 42."))

        with self.voiceover(_("What is the meaning of life?<bookmark mark='reveal_answer' /> The meaning of life is 42.")):
            self.play(manim.Write(txt_question), run_time=1.0)
            self.wait_until_bookmark("reveal_answer")
            self.play(manim.ReplacementTransform(txt_question, txt_answer), run_time=1.0)
            self.wait_for_voiceover()
```
