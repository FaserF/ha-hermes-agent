"""Test versioning standards and SemVer compliance for Hermes Agent."""

import json
import re
from pathlib import Path


def test_semver_format_in_manifest():
    """Verify manifest.json adheres strictly to SemVer (major.minor.patch)."""
    manifest_path = (
        Path(__file__).parent.parent
        / "custom_components"
        / "hermes_agent"
        / "manifest.json"
    )
    assert manifest_path.exists(), "manifest.json must exist"

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    version = manifest.get("version")
    assert version is not None, "manifest.json must have a version field"

    # Strictly SemVer (e.g. 1.0.0, 1.0.0-dev0, 1.2.3-rc1)
    # Must NOT be CalVer like 2026.10.0
    semver_pattern = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
    assert re.match(semver_pattern, version), f"Version '{version}' is not valid SemVer"

    # Verify not CalVer
    parts = version.split(".")[0]
    assert int(parts) < 2000, f"Version '{version}' looks like CalVer (year-based)"


def test_semver_format_in_pyproject():
    """Verify pyproject.toml version matches manifest.json and is SemVer."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml must exist"

    with open(pyproject_path, encoding="utf-8") as f:
        content = f.read()

    match = re.search(r'version\s*=\s*"([^"]+)"', content)
    assert match is not None, "pyproject.toml must have a version"
    pyproject_version = match.group(1)

    manifest_path = (
        Path(__file__).parent.parent
        / "custom_components"
        / "hermes_agent"
        / "manifest.json"
    )
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    manifest_version = manifest["version"]

    assert pyproject_version == manifest_version, (
        f"Version mismatch: pyproject={pyproject_version}, manifest={manifest_version}"
    )
