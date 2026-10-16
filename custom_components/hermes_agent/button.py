"""Button platform for Hermes Agent integration."""

from __future__ import annotations

import logging

from homeassistant.components.button import (
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import HermesAgentClient
from .const import DATA_CLIENT, DATA_COORDINATOR, DOMAIN
from .coordinator import HermesAgentDataUpdateCoordinator
from .helpers import get_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Hermes Agent button entities from a config entry."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: HermesAgentDataUpdateCoordinator = entry_data[DATA_COORDINATOR]
    client: HermesAgentClient = entry_data[DATA_CLIENT]

    entities: list[ButtonEntity] = [
        HermesAgentRefreshButton(coordinator, client, entry),
        HermesAgentHealthCheckButton(coordinator, client, entry),
    ]

    async_add_entities(entities)


class HermesAgentButton(CoordinatorEntity[HermesAgentDataUpdateCoordinator], ButtonEntity):
    """Base class for Hermes Agent buttons."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HermesAgentDataUpdateCoordinator,
        client: HermesAgentClient,
        entry: ConfigEntry,
        description: ButtonEntityDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self.client = client
        self.entry = entry
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        sw_version = None
        if coordinator.data:
            sw_version = coordinator.data.get("version")
        self._attr_device_info = get_device_info(entry, sw_version)


class HermesAgentRefreshButton(HermesAgentButton):
    """Button to force reload coordinator state and telemetry."""

    def __init__(
        self,
        coordinator: HermesAgentDataUpdateCoordinator,
        client: HermesAgentClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize refresh button."""
        super().__init__(
            coordinator,
            client,
            entry,
            ButtonEntityDescription(
                key="refresh_gateway",
                name="Refresh Gateway",
                icon="mdi:refresh",
                entity_category=EntityCategory.CONFIG,
            ),
        )

    async def async_press(self) -> None:
        """Force refresh data in coordinator."""
        _LOGGER.info("Forcing refresh of Hermes Agent gateway for %s", self.entry.entry_id)
        await self.coordinator.async_refresh()


class HermesAgentHealthCheckButton(HermesAgentButton):
    """Button to ping and run a full health check on Hermes Agent."""

    def __init__(
        self,
        coordinator: HermesAgentDataUpdateCoordinator,
        client: HermesAgentClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize health check button."""
        super().__init__(
            coordinator,
            client,
            entry,
            ButtonEntityDescription(
                key="check_health",
                name="Check Health",
                icon="mdi:heart-pulse",
                entity_category=EntityCategory.DIAGNOSTIC,
            ),
        )

    async def async_press(self) -> None:
        """Run health check and update coordinator."""
        _LOGGER.info("Running health check on Hermes Agent gateway for %s", self.entry.entry_id)
        await self.client.async_get_health_detailed()
        await self.coordinator.async_refresh()
