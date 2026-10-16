"""Test translation files for Hermes Agent."""

import json
from pathlib import Path


def _get_keys(data: dict, prefix: str = "") -> set[str]:
    keys = set()
    for k, v in data.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys.update(_get_keys(v, full_key))
        else:
            keys.add(full_key)
    return keys


def test_translation_keys_parity():
    """Verify en.json and de.json have parity with strings.json."""
    base_dir = (
        Path(__file__).parent.parent
        / "custom_components"
        / "hermes_agent"
    )
    strings_file = base_dir / "strings.json"
    en_file = base_dir / "translations" / "en.json"
    de_file = base_dir / "translations" / "de.json"

    assert strings_file.exists()
    assert en_file.exists()
    assert de_file.exists()

    with open(strings_file, encoding="utf-8") as f:
        strings_data = json.load(f)
    with open(en_file, encoding="utf-8") as f:
        en_data = json.load(f)
    with open(de_file, encoding="utf-8") as f:
        de_data = json.load(f)

    strings_keys = _get_keys(strings_data)
    en_keys = _get_keys(en_data)
    de_keys = _get_keys(de_data)

    assert strings_keys == en_keys, f"Mismatch in en.json: {strings_keys ^ en_keys}"
    assert strings_keys == de_keys, f"Mismatch in de.json: {strings_keys ^ de_keys}"
