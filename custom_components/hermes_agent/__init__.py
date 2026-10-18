"""The Hermes Agent integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from .client import HermesAgentClient
from .const import (
    CONF_API_KEY,
    CONF_API_URL,
    DATA_CLIENT,
    DATA_COORDINATOR,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import HermesAgentDataUpdateCoordinator
from .helpers import set_integration_version
from .services import async_setup_services, async_unload_services


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up Hermes Agent integration services."""
    hass.data.setdefault(DOMAIN, {})
    async_setup_services(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hermes Agent from a config entry."""
    try:
        from homeassistant.loader import async_get_integration

        integration = await async_get_integration(hass, DOMAIN)
        if integration.version:
            set_integration_version(str(integration.version))
    except Exception:
        pass

    session = aiohttp_client.async_get_clientsession(hass)
    api_url = entry.data[CONF_API_URL]
    api_key = entry.data.get(CONF_API_KEY)

    client = HermesAgentClient(session=session, api_url=api_url, api_key=api_key)
    coordinator = HermesAgentDataUpdateCoordinator(hass, client)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_CLIENT: client,
        DATA_COORDINATOR: coordinator,
        "client": client,
        "coordinator": coordinator,
    }

    async_setup_services(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            async_unload_services(hass)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update without a full reload.

    Only performs a full reload when connectivity options (API URL or key)
    have changed. For model/display-only option changes, simply refreshes
    the coordinator so entities stay available.
    """
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator = entry_data.get(DATA_COORDINATOR) or entry_data.get("coordinator")
    if coordinator is not None:
        await coordinator.async_request_refresh()
    else:
        # Coordinator not found — fall back to full reload
        await hass.config_entries.async_reload(entry.entry_id)
