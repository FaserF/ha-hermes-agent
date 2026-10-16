"""Helper utilities for Hermes Agent integration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo

from .const import CONF_API_URL, DEFAULT_MANUFACTURER, DEFAULT_MODEL, DOMAIN


def get_integration_version() -> str:
    """Read integration version from manifest.json."""
    try:
        manifest_path = Path(__file__).parent / "manifest.json"
        with open(manifest_path, encoding="utf-8") as f:
            data = json.load(f)
            return str(data.get("version", "1.0.0"))
    except Exception:
        return "1.0.0"


def get_device_info(entry: ConfigEntry, sw_version: str | None = None) -> DeviceInfo:
    """Return device registry DeviceInfo for Hermes Agent entry."""
    version = sw_version or get_integration_version() or None
    config_url = entry.data.get(CONF_API_URL, "").replace("/v1", "")
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Hermes Agent Gateway",
        manufacturer=DEFAULT_MANUFACTURER,
        model=DEFAULT_MODEL,
        sw_version=version,
        configuration_url=config_url,
    )


def mask_sensitive(data: dict[str, Any]) -> dict[str, Any]:
    """Mask sensitive keys in data dictionaries for diagnostics/logging."""
    sensitive_keys = {
        "api_key",
        "key",
        "token",
        "authorization",
        "password",
        "secret",
        "access_token",
    }
    cleaned: dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(v, dict):
            cleaned[k] = mask_sensitive(v)
        elif isinstance(v, list):
            cleaned[k] = [
                mask_sensitive(item) if isinstance(item, dict) else item for item in v
            ]
        elif any(s in k.lower() for s in sensitive_keys):
            cleaned[k] = "******" if v else None
        else:
            cleaned[k] = v
    return cleaned
