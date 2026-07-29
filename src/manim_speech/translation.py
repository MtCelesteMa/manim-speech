"""Text translation functions for Manim Speech."""

import os
import subprocess
import sys
from os import PathLike
from pathlib import Path

import manim
import polib

from . import services


def init_translation_env(file: str | PathLike[str], domain: str) -> None:
    if not Path("locales").exists():
        Path("locales").mkdir()
    result = subprocess.run(
        [
            "xgettext",
            "-d",
            domain,
            "-o",
            str(Path("locales") / f"{domain}.pot"),
            os.fspath(file),
        ],
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"xgettext failed with return code {result.returncode}")


def translate_po_file(
    domain: str,
    src_lang: str,
    target_lang: str,
    *,
    service: services.TranslationService | None = None,
) -> None:
    src_path = Path("locales") / f"{domain}.pot"
    target_path = Path("locales") / target_lang / "LC_MESSAGES" / f"{domain}"
    if not target_path.parent.exists():
        target_path.parent.mkdir(parents=True)
    manim.logger.info(f"Translating to {target_lang}...")
    if not target_path.with_suffix(".po").exists():
        pofile = polib.pofile(str(src_path))
        pofile.metadata["Content-Type"] = "text/plain; charset=UTF-8"
        if service is not None:
            manim.logger.info(f"Using {service.service_name} translation service.")
            for entry in pofile.untranslated_entries():
                translation = service.translate(entry.msgid, src_lang, target_lang)
                entry.msgstr = translation
        else:
            manim.logger.info("No translation service specified.")
        pofile.save(str(target_path.with_suffix(".po")))
        if service is None:
            manim.console.print(
                f"An empty translation file has been created at {target_path.with_suffix('.po')}. Please fill it in and then rerun `manim`."
            )
            sys.exit(1)
    else:
        manim.logger.info(f"Translation file for {target_lang} found.")
        pofile = polib.pofile(str(target_path.with_suffix(".po")))
    pofile.save_as_mofile(str(target_path.with_suffix(".mo")))
