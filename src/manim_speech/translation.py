"""Text translation functions for Manim Speech."""

from . import services

import subprocess
import pathlib

import polib
import manim


def init_translation_env(file: pathlib.Path | str, domain: str) -> None:
    if not pathlib.Path("locales").exists():
        pathlib.Path("locales").mkdir()
    result = subprocess.run(["xgettext", "-d", domain, "-o", str(pathlib.Path("locales") / f"{domain}.pot"), str(file)])
    if result.returncode != 0:
        raise RuntimeError(f"xgettext failed with return code {result.returncode}")


def translate_po_file(domain: str, src_lang: str, target_lang: str, *, service: services.base.TranslationService | None = None) -> None:
    src_path = pathlib.Path("locales") / f"{domain}.pot"
    target_path = pathlib.Path("locales") / target_lang / "LC_MESSAGES" / f"{domain}"
    if not target_path.parent.exists():
        target_path.parent.mkdir(parents=True)
    manim.logger.info(f"Translating to {target_lang}...")
    if not target_path.with_suffix(".po").exists():
        pofile = polib.pofile(str(src_path))
        pofile.metadata["Content-Type"] = "text/plain; charset=UTF-8"
        if isinstance(service, services.base.TranslationService):
            manim.logger.info(f"Using {service.service_name} translation service.")
            for entry in pofile.untranslated_entries():
                translation = service.translate(services.base.TranslationInput(text=entry.msgid, source_language=src_lang, target_language=target_lang)).output.translated_text
                entry.msgstr = translation
        else:
            manim.logger.info("No translation service specified.")
        pofile.save(str(target_path.with_suffix(".po")))
        if not isinstance(service, services.base.TranslationService):
            manim.console.print(f"An empty translation file has been created at {target_path.with_suffix(".po")}. Please fill it in and then rerun `manim`.")
            exit(1)
    else:
        manim.logger.info(f"Translation file for {target_lang} found.")
        pofile = polib.pofile(str(target_path.with_suffix(".po")))
    pofile.save_as_mofile(str(target_path.with_suffix(".mo")))
