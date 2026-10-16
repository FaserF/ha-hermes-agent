"""Switch platform for Hermes Agent integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import HermesAgentClient
from .const import (
    CONF_AUTONOMOUS_EXECUTION,
    CONF_TELEMETRY,
    DATA_CLIENT,
    DATA_COORDINATOR,
    DEFAULT_AUTONOMOUS_EXECUTION,
    DEFAULT_TELEMETRY,
    DOMAIN,
)
from .coordinator import HermesAgentDataUpdateCoordinator
from .helpers import get_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Hermes Agent switch entities from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    client: HermesAgentClient = data[DATA_CLIENT]
    coordinator: HermesAgentDataUpdateCoordinator = data[DATA_COORDINATOR]

    entities: list[SwitchEntity] = [
        HermesAgentAutonomousSwitch(coordinator, entry, client),
        HermesAgentTelemetrySwitch(coordinator, entry, client),
    ]
    async_add_entities(entities)


class HermesAgentAutonomousSwitch(
    CoordinatorEntity[HermesAgentDataUpdateCoordinator], SwitchEntity
):
    """Switch entity for autonomous task and tool execution."""

    _attr_has_entity_name = True
    _attr_name = "Autonomous Execution"
    _attr_icon = "mdi:robot-confused-outline"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: HermesAgentDataUpdateCoordinator,
        entry: ConfigEntry,
        client: HermesAgentClient,
    ) -> None:
        """Initialize autonomous execution switch."""
        super().__init__(coordinator)
        self.entry = entry
        self.client = client
        self._attr_unique_id = f"{entry.entry_id}_autonomous_execution"
        sw_version = coordinator.data.get("version") if coordinator.data else None
        self._attr_device_info = get_device_info(entry, sw_version)

    @property
    def is_on(self) -> bool:
        """Return whether autonomous execution is enabled."""
        return self.entry.options.get(
            CONF_AUTONOMOUS_EXECUTION, DEFAULT_AUTONOMOUS_EXECUTION
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable autonomous execution."""
        new_options = dict(self.entry.options)
        new_options[CONF_AUTONOMOUS_EXECUTION] = True
        self.hass.config_entries.async_update_entry(self.entry, options=new_options)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable autonomous execution."""
        new_options = dict(self.entry.options)
        new_options[CONF_AUTONOMOUS_EXECUTION] = False
        self.hass.config_entries.async_update_entry(self.entry, options=new_options)
        self.async_write_ha_state()


class HermesAgentTelemetrySwitch(
    CoordinatorEntity[HermesAgentDataUpdateCoordinator], SwitchEntity
):
    """Switch entity for Hermes Agent telemetry and status polling."""

    _attr_has_entity_name = True
    _attr_name = "Telemetry Reporting"
    _attr_icon = "mdi:chart-timeline-variant"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: HermesAgentDataUpdateCoordinator,
        entry: ConfigEntry,
        client: HermesAgentClient,
    ) -> None:
        """Initialize telemetry switch."""
        super().__init__(coordinator)
        self.entry = entry
        self.client = client
        self._attr_unique_id = f"{entry.entry_id}_telemetry"
        sw_version = coordinator.data.get("version") if coordinator.data else None
        self._attr_device_info = get_device_info(entry, sw_version)

    @property
    def is_on(self) -> bool:
        """Return whether telemetry collection is enabled."""
        return self.entry.options.get(CONF_TELEMETRY, DEFAULT_TELEMETRY)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable telemetry reporting."""
        new_options = dict(self.entry.options)
        new_options[CONF_TELEMETRY] = True
        self.hass.config_entries.async_update_entry(self.entry, options=new_options)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable telemetry reporting."""
        new_options = dict(self.entry.options)
        new_options[CONF_TELEMETRY] = False
        self.hass.config_entries.async_update_entry(self.entry, options=new_options)
        self.async_write_ha_state()
