"""Diagnostics support for Hermes Agent integration."""

from __future__ import annotations

import math
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_API_KEY,
    DATA_CLIENT,
    DATA_COORDINATOR,
    DEFAULT_MANUFACTURER,
    DEFAULT_MODEL,
    DOMAIN,
)
from .coordinator import HermesAgentDataUpdateCoordinator

TO_REDACT = {
    CONF_API_KEY,
    "api_key",
    "token",
    "authorization",
    "password",
    "secret",
}


def _to_json_safe(obj: Any) -> Any:
    """Convert object to JSON safe representation."""
    if isinstance(obj, bool) or obj is None:
        return obj
    if isinstance(obj, (int, str)):
        return obj
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return str(obj)
        return obj
    if isinstance(obj, (list, tuple, set)):
        return [_to_json_safe(i) for i in obj]
    if isinstance(obj, dict):
        return {str(k): _to_json_safe(v) for k, v in obj.items()}
    if hasattr(obj, "__dict__"):
        return _to_json_safe(obj.__dict__)
    return str(obj)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator: HermesAgentDataUpdateCoordinator | None = entry_data.get(
        DATA_COORDINATOR
    )
    client = entry_data.get(DATA_CLIENT)

    diag: dict[str, Any] = {
        "entry": {
            "title": entry.title,
            "version": entry.version,
            "domain": entry.domain,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
            "pref_disable_new_entities": entry.pref_disable_new_entities,
            "pref_disable_polling": entry.pref_disable_polling,
        },
        "client": {
            "v1_url": client.v1_url if client else None,
            "root_url": client.root_url if client else None,
            "has_api_key": bool(client and client._api_key),
        },
    }

    if coordinator:
        diag["coordinator"] = {
            "last_update_success": coordinator.last_update_success,
            "data": _to_json_safe(coordinator.data),
            "models_count": len(coordinator.data.get("models", [])) if coordinator.data else 0,
        }
    else:
        diag["coordinator"] = None

    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)

    devices: list[dict[str, Any]] = []
    for dev in dr.async_entries_for_config_entry(device_registry, entry.entry_id):
        devices.append(
            {
                "id": dev.id,
                "name": dev.name,
                "identifiers": [list(ident) for ident in dev.identifiers],
                "manufacturer": dev.manufacturer or DEFAULT_MANUFACTURER,
                "model": dev.model or DEFAULT_MODEL,
                "sw_version": dev.sw_version,
            }
        )
    diag["devices"] = devices

    entities: list[dict[str, Any]] = []
    for ent in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        entities.append(
            {
                "entity_id": ent.entity_id,
                "original_name": ent.original_name,
                "platform": ent.platform,
                "disabled_by": ent.disabled_by,
                "device_class": ent.device_class,
                "unique_id": ent.unique_id,
            }
        )
    diag["entities"] = entities

    return diag
