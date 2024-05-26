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

### Services

| Service Name | Optional Dependency Set | Is Local | Text-To-Speech | Speech-To-Text | Translation |
|--------------|-------------------------|----------|----------------|----------------|-------------|
| OpenAI       | `openai`                | No       | Yes            | Yes            | Yes         |
| ElevenLabs   | `elevenlabs`            | No       | Yes            | No             | No          |
| Whisper      | `whisper`               | Yes      | No             | Yes            | No          |
| AssemblyAI   | `assemblyai`            | No       | No             | Yes            | No          |
| DeepL        | `deepl`                 | No       | No             | No             | Yes         |

#### Notes on Chinese Translations

**OpenAI Translator:** Please specify Traditional (`zh_tw`) or Simplified (`zh_cn`) when using the OpenAI translator. Only specifying `zh` has no guarantee on the script used, although tests have indicated that GPT-4o strongly prefers Simplified Chinese in such cases.

**DeepL Translator:** The DeepL translator does not natively support translating to Traditional Chinese, so translating to Traditional Chinese requires the `chinese` optional dependency set to be installed. Only specifying `zh` has the same effect as specifying `zh_cn`.

## Usage Examples

Creating a basic scene with a voiceover with Manim Speech:
```python
import manim
import manim_speech
from manim_speech.services import openai as openai_service

class MeaningOfLife(manim_speech.VoiceoverScene):
    def construct(self) -> None:
        self.set_tts_service(openai_service.OpenAITTSService()) # Remove this line if you want to manually record voiceovers.
        self.set_stt_service(openai_service.OpenAISTTService()) # Only required if you use bookmarks.

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

class MeaningOfLife(manim_speech.VoiceoverScene, manim_speech.TranslationScene):
    def construct(self) -> None:
        self.set_tts_service(openai_service.OpenAITTSService()) # Remove this line if you want to manually record voiceovers.
        self.set_stt_service(openai_service.OpenAISTTService()) # Only required if you use bookmarks.
        self.set_translation_service(openai_service.OpenAITranslationService()) # Remove this line if you want to manually translate text.

        self.translate(__file__, "meaning_of_life", "en", "zh_tw")
        _ = self._

        with self.voiceover(_("What is the meaning of life?")) as speech_data:
            txt = manim.Text(_("The meaning of life is 42."))
            self.play(manim.Write(txt), run_time=speech_data.duration)
            self.wait_for_voiceover()
            self.play(manim.FadeOut(txt))
```
