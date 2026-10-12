"""Tests that keep the translations complete."""
import json
from pathlib import Path

import pytest

TRANSLATIONS = Path("custom_components/mygekko/translations")
LANGUAGES = sorted(path.stem for path in TRANSLATIONS.glob("*.json"))


def _keys(data, prefix=""):
    keys = set()
    for key, value in data.items():
        if isinstance(value, dict):
            keys |= _keys(value, f"{prefix}{key}.")
        else:
            keys.add(f"{prefix}{key}")
    return keys


def _load(language):
    return json.loads((TRANSLATIONS / f"{language}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("language", [lang for lang in LANGUAGES if lang != "en"])
def test_language_is_complete(language):
    """Every text of the English translation exists in the other languages."""
    english = _keys(_load("en"))
    missing = english - _keys(_load(language))
    assert not missing, f"{language} misses {sorted(missing)}"


def test_icons_use_existing_translation_keys():
    """icons.json only describes entities that have a translation key."""
    icons = json.loads(
        Path("custom_components/mygekko/icons.json").read_text(encoding="utf-8")
    )
    english = _load("en")["entity"]
    for domain, entities in icons["entity"].items():
        for key in entities:
            assert key in english.get(domain, {}), f"{domain}.{key} has no translation"
