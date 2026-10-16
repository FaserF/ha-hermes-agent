"""Binary sensors for Hermes Agent integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import HermesAgentDataUpdateCoordinator
from .helpers import get_device_info


@dataclass(frozen=True, kw_only=True)
class HermesAgentBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Hermes Agent binary sensor entity."""

    is_on_fn: Callable[[dict[str, Any]], bool]
    extra_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


BINARY_SENSOR_DESCRIPTIONS: tuple[HermesAgentBinarySensorEntityDescription, ...] = (
    HermesAgentBinarySensorEntityDescription(
        key="connectivity",
        name="Gateway Connectivity",
        translation_key="connectivity",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        is_on_fn=lambda data: bool(data.get("reachable", False)),
    ),
    HermesAgentBinarySensorEntityDescription(
        key="problem",
        name="Gateway Problem",
        translation_key="problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=lambda data: data.get("status") not in ("ok", "healthy"),
        extra_fn=lambda data: {
            "status": data.get("status"),
            "readiness": data.get("readiness", {}),
        },
    ),
    HermesAgentBinarySensorEntityDescription(
        key="busy",
        name="Gateway Busy",
        translation_key="busy",
        icon="mdi:progress-clock",
        is_on_fn=lambda data: bool(data.get("gateway_busy", False)),
        extra_fn=lambda data: {"active_agents": data.get("active_agents", 0)},
    ),
    HermesAgentBinarySensorEntityDescription(
        key="telegram_connected",
        name="Telegram Adapter",
        translation_key="telegram_connected",
        icon="mdi:telegram",
        is_on_fn=lambda data: (
            data.get("platforms", {}).get("telegram", {}).get("state") == "connected"
        ),
        extra_fn=lambda data: data.get("platforms", {}).get("telegram", {}),
    ),
    HermesAgentBinarySensorEntityDescription(
        key="teams_connected",
        name="Teams Adapter",
        translation_key="teams_connected",
        icon="mdi:microsoft-teams",
        is_on_fn=lambda data: (
            data.get("platforms", {}).get("teams", {}).get("state") == "connected"
        ),
        extra_fn=lambda data: data.get("platforms", {}).get("teams", {}),
    ),
    HermesAgentBinarySensorEntityDescription(
        key="webhook_connected",
        name="Webhook Adapter",
        translation_key="webhook_connected",
        icon="mdi:webhook",
        entity_registry_enabled_default=False,
        is_on_fn=lambda data: (
            data.get("platforms", {}).get("webhook", {}).get("state") == "connected"
        ),
        extra_fn=lambda data: data.get("platforms", {}).get("webhook", {}),
    ),
    HermesAgentBinarySensorEntityDescription(
        key="homeassistant_connected",
        name="Home Assistant Connector",
        translation_key="homeassistant_connected",
        icon="mdi:home-assistant",
        entity_registry_enabled_default=False,
        is_on_fn=lambda data: (
            data.get("platforms", {}).get("homeassistant", {}).get("state")
            == "connected"
        ),
        extra_fn=lambda data: data.get("platforms", {}).get("homeassistant", {}),
    ),
    HermesAgentBinarySensorEntityDescription(
        key="storage_problem",
        name="Storage Problem",
        translation_key="storage_problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_registry_enabled_default=False,
        is_on_fn=lambda data: (
            (
                data.get("readiness_checks", {}).get("state_db", {}).get("status")
                not in (None, "ok")
            )
            or (
                data.get("readiness_checks", {}).get("session_store", {}).get("status")
                not in (None, "ok")
            )
        ),
        extra_fn=lambda data: {
            "state_db": data.get("readiness_checks", {}).get("state_db", {}),
            "session_store": data.get("readiness_checks", {}).get("session_store", {}),
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: HermesAgentDataUpdateCoordinator = data[DATA_COORDINATOR]

    async_add_entities(
        HermesAgentBinarySensor(coordinator, entry, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class HermesAgentBinarySensor(
    CoordinatorEntity[HermesAgentDataUpdateCoordinator], BinarySensorEntity
):
    """Representation of a Hermes Agent binary sensor."""

    entity_description: HermesAgentBinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HermesAgentDataUpdateCoordinator,
        entry: ConfigEntry,
        description: HermesAgentBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entry = entry
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        sw_version = coordinator.data.get("version") if coordinator.data else None
        self._attr_device_info = get_device_info(entry, sw_version)

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        if not self.coordinator.data:
            return False
        return self.entity_description.is_on_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if not self.coordinator.data or not self.entity_description.extra_fn:
            return None
        return self.entity_description.extra_fn(self.coordinator.data)
