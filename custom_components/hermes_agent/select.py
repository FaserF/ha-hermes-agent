"""Select platform for Hermes Agent integration."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_AI_TASK_MODEL,
    CONF_CHAT_MODEL,
    DATA_COORDINATOR,
    DEFAULT_AI_TASK_MODEL,
    DEFAULT_CHAT_MODEL,
    DOMAIN,
)
from .coordinator import HermesAgentDataUpdateCoordinator
from .helpers import get_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Hermes Agent select entities from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: HermesAgentDataUpdateCoordinator = data[DATA_COORDINATOR]

    entities: list[SelectEntity] = [
        HermesAgentChatModelSelect(coordinator, entry),
        HermesAgentTaskModelSelect(coordinator, entry),
    ]
    async_add_entities(entities)


class HermesAgentChatModelSelect(
    CoordinatorEntity[HermesAgentDataUpdateCoordinator], SelectEntity
):
    """Select entity for active conversation model."""

    _attr_has_entity_name = True
    _attr_name = "Conversation Model"
    _attr_icon = "mdi:robot"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: HermesAgentDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize active chat model select."""
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_chat_model"
        sw_version = coordinator.data.get("version") if coordinator.data else None
        self._attr_device_info = get_device_info(entry, sw_version)

    @property
    def options(self) -> list[str]:
        """Return available model options."""
        models: list[str] = []
        if self.coordinator.data:
            models = self.coordinator.data.get("models", [])
        if DEFAULT_CHAT_MODEL not in models:
            models = [DEFAULT_CHAT_MODEL] + models
        return models or [DEFAULT_CHAT_MODEL]

    @property
    def current_option(self) -> str | None:
        """Return currently selected chat model."""
        current = self.entry.options.get(CONF_CHAT_MODEL, DEFAULT_CHAT_MODEL)
        if current in self.options:
            return current
        return self.options[0] if self.options else None

    async def async_select_option(self, option: str) -> None:
        """Update active chat model in config entry options."""
        new_options = dict(self.entry.options)
        new_options[CONF_CHAT_MODEL] = option
        self.hass.config_entries.async_update_entry(self.entry, options=new_options)
        self.async_write_ha_state()


class HermesAgentTaskModelSelect(
    CoordinatorEntity[HermesAgentDataUpdateCoordinator], SelectEntity
):
    """Select entity for active AI Task engine model."""

    _attr_has_entity_name = True
    _attr_name = "AI Task Model"
    _attr_icon = "mdi:brain"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: HermesAgentDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize AI task model select."""
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_ai_task_model"
        sw_version = coordinator.data.get("version") if coordinator.data else None
        self._attr_device_info = get_device_info(entry, sw_version)

    @property
    def options(self) -> list[str]:
        """Return available model options."""
        models: list[str] = []
        if self.coordinator.data:
            models = self.coordinator.data.get("models", [])
        if DEFAULT_AI_TASK_MODEL not in models:
            models = [DEFAULT_AI_TASK_MODEL] + models
        return models or [DEFAULT_AI_TASK_MODEL]

    @property
    def current_option(self) -> str | None:
        """Return currently selected task model."""
        current = self.entry.options.get(CONF_AI_TASK_MODEL, DEFAULT_AI_TASK_MODEL)
        if current in self.options:
            return current
        return self.options[0] if self.options else None

    async def async_select_option(self, option: str) -> None:
        """Update AI task model in config entry options."""
        new_options = dict(self.entry.options)
        new_options[CONF_AI_TASK_MODEL] = option
        self.hass.config_entries.async_update_entry(self.entry, options=new_options)
        self.async_write_ha_state()
