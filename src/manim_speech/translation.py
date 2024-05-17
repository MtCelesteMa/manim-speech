"""Text translation functions for Manim Speech."""

from . import services

import subprocess
import pathlib

import polib


def init_translation_env(file: pathlib.Path | str, domain: str) -> None:
    if not pathlib.Path("locales").exists():
        pathlib.Path("locales").mkdir()
    result = subprocess.run(["xgettext", "-d", domain, "-o", str(pathlib.Path("locales") / f"{domain}.pot"), str(file)])
    if result.returncode != 0:
        raise RuntimeError(f"xgettext failed with return code {result.returncode}")


def translate_po_file(domain: str, src_lang: str, target_lang: str, *, service: services.base.TranslationService) -> None:
    src_path = pathlib.Path("locales") / f"{domain}.pot"
    target_path = pathlib.Path("locales") / target_lang / "LC_MESSAGES" / f"{domain}"
    if not target_path.parent.exists():
        target_path.parent.mkdir(parents=True)
    if not target_path.with_suffix(".po").exists():
        pofile = polib.pofile(str(src_path))
        pofile.metadata["Content-Type"] = "text/plain; charset=UTF-8"
        for entry in pofile.untranslated_entries():
            translation = service.translate(services.base.TranslationInput(text=entry.msgid, source_language=src_lang, target_language=target_lang)).output.translated_text
            entry.msgstr = translation
        pofile.save(str(target_path.with_suffix(".po")))
    else:
        pofile = polib.pofile(str(target_path.with_suffix(".po")))
    pofile.save_as_mofile(str(target_path.with_suffix(".mo")))
