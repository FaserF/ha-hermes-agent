"""Sensors for Hermes Agent integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DATA_SUGGESTIONS_SENSOR, DOMAIN
from .coordinator import HermesAgentDataUpdateCoordinator
from .helpers import get_device_info


@dataclass(frozen=True, kw_only=True)
class HermesAgentSensorEntityDescription(SensorEntityDescription):
    """Describes a Hermes Agent sensor entity."""

    value_fn: Callable[[dict[str, Any]], Any]
    extra_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


SENSOR_DESCRIPTIONS: tuple[HermesAgentSensorEntityDescription, ...] = (
    HermesAgentSensorEntityDescription(
        key="status",
        name="Gateway Status",
        translation_key="status",
        icon="mdi:check-network",
        value_fn=lambda data: data.get("status", "unknown"),
    ),
    HermesAgentSensorEntityDescription(
        key="gateway_state",
        name="Gateway State",
        translation_key="gateway_state",
        icon="mdi:server",
        value_fn=lambda data: data.get("gateway_state", "running"),
    ),
    HermesAgentSensorEntityDescription(
        key="latency_ms",
        name="Response Time",
        translation_key="latency_ms",
        icon="mdi:timer-outline",
        native_unit_of_measurement="ms",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("latency_ms"),
    ),
    HermesAgentSensorEntityDescription(
        key="models_count",
        name="Available Models",
        translation_key="models_count",
        icon="mdi:robot",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("models_count", 0),
        extra_fn=lambda data: {"models": data.get("models", [])},
    ),
    HermesAgentSensorEntityDescription(
        key="active_agents",
        name="Active Agents",
        translation_key="active_agents",
        icon="mdi:account-cog",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("active_agents", 0),
    ),
    HermesAgentSensorEntityDescription(
        key="sessions_count",
        name="Active Sessions",
        translation_key="sessions_count",
        icon="mdi:forum",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("sessions_count", 0),
        extra_fn=lambda data: {
            "sessions_by_source": data.get("sessions_by_source", {}),
        },
    ),
    HermesAgentSensorEntityDescription(
        key="telegram_sessions",
        name="Telegram Sessions",
        translation_key="telegram_sessions",
        icon="mdi:telegram",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("telegram_sessions_count", 0),
        extra_fn=lambda data: {
            "latest_telegram": data.get("latest_telegram_session"),
            "telegram_sessions": data.get("telegram_sessions", []),
        },
    ),
    HermesAgentSensorEntityDescription(
        key="jobs_count",
        name="Scheduled Jobs",
        translation_key="jobs_count",
        icon="mdi:calendar-clock",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("jobs_count", 0),
    ),
    HermesAgentSensorEntityDescription(
        key="skills_count",
        name="Installed Skills",
        translation_key="skills_count",
        icon="mdi:puzzle",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("skills_count", 0),
    ),
    HermesAgentSensorEntityDescription(
        key="requests_today",
        name="Requests Today",
        translation_key="requests_today",
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.get("metrics_today", {}).get("requests", 0),
    ),
    HermesAgentSensorEntityDescription(
        key="messages_today",
        name="Messages Today",
        translation_key="messages_today",
        icon="mdi:message-text-outline",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.get("metrics_today", {}).get("messages", 0),
    ),
    HermesAgentSensorEntityDescription(
        key="tokens_today",
        name="Tokens Today",
        translation_key="tokens_today",
        icon="mdi:chip",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.get("metrics_today", {}).get("tokens", 0),
    ),
    HermesAgentSensorEntityDescription(
        key="disk_usage",
        name="Host Disk Usage",
        translation_key="disk_usage",
        icon="mdi:harddisk",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: (
            data.get("readiness", {})
            .get("checks", {})
            .get("disk", {})
            .get("used_percent")
        ),
        extra_fn=lambda data: {
            "free_bytes": data.get("readiness", {})
            .get("checks", {})
            .get("disk", {})
            .get("free_bytes")
        },
    ),
    HermesAgentSensorEntityDescription(
        key="connected_platforms",
        name="Connected Platforms",
        translation_key="connected_platforms",
        icon="mdi:lan-connect",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: len(
            [
                p
                for p, info in data.get("platforms", {}).items()
                if isinstance(info, dict) and info.get("state") == "connected"
            ]
        ),
        extra_fn=lambda data: {"platforms": list(data.get("platforms", {}).keys())},
    ),
    HermesAgentSensorEntityDescription(
        key="version",
        name="Version",
        translation_key="version",
        icon="mdi:information-outline",
        value_fn=lambda data: data.get("version", "unknown"),
    ),
    HermesAgentSensorEntityDescription(
        key="disk_free_gb",
        name="Host Disk Free",
        translation_key="disk_free_gb",
        icon="mdi:harddisk",
        native_unit_of_measurement="GB",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("disk_free_gb"),
    ),
    HermesAgentSensorEntityDescription(
        key="latency_p95_ms",
        name="Response Time P95",
        translation_key="latency_p95_ms",
        icon="mdi:timer-sand",
        native_unit_of_measurement="ms",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("latency_p95_ms"),
    ),
    HermesAgentSensorEntityDescription(
        key="active_runs",
        name="Active Background Runs",
        translation_key="active_runs",
        icon="mdi:play-circle-outline",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("active_runs", 0),
    ),
    HermesAgentSensorEntityDescription(
        key="toolsets_count",
        name="Active Toolsets",
        translation_key="toolsets_count",
        icon="mdi:tools",
        state_class=SensorStateClass.TOTAL,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("toolsets_count", 0),
        extra_fn=lambda data: {
            "total_toolsets": data.get("toolsets_total", 0),
            "toolsets": data.get("toolsets", []),
        },
    ),
    HermesAgentSensorEntityDescription(
        key="latest_job_status",
        name="Latest Job",
        translation_key="latest_job_status",
        icon="mdi:clock-check-outline",
        value_fn=lambda data: (data.get("latest_job") or {}).get("name", "None"),
        extra_fn=lambda data: data.get("latest_job") or {},
    ),
    HermesAgentSensorEntityDescription(
        key="readiness",
        name="Gateway Readiness",
        translation_key="readiness",
        icon="mdi:shield-check",
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("readiness", {}).get("status", "unknown"),
        extra_fn=lambda data: data.get("readiness_checks", {}),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Hermes Agent sensor entities from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: HermesAgentDataUpdateCoordinator = data[DATA_COORDINATOR]

    entities: list[SensorEntity] = [
        HermesAgentSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    ]
    sugg_sensor = HermesAgentAutomationSuggestionsSensor(coordinator, entry)
    entities.append(sugg_sensor)
    data[DATA_SUGGESTIONS_SENSOR] = sugg_sensor

    async_add_entities(entities)


class HermesAgentSensor(
    CoordinatorEntity[HermesAgentDataUpdateCoordinator], SensorEntity
):
    """Representation of a Hermes Agent sensor."""

    entity_description: HermesAgentSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: HermesAgentDataUpdateCoordinator,
        entry: ConfigEntry,
        description: HermesAgentSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entry = entry
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        sw_version = coordinator.data.get("version") if coordinator.data else None
        self._attr_device_info = get_device_info(entry, sw_version)

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if not self.coordinator.data or not self.entity_description.extra_fn:
            return None
        return self.entity_description.extra_fn(self.coordinator.data)


class HermesAgentAutomationSuggestionsSensor(
    CoordinatorEntity[HermesAgentDataUpdateCoordinator], SensorEntity
):
    """Sensor storing smart home automation recommendations from Hermes Agent."""

    _attr_has_entity_name = True
    _attr_name = "Automation Suggestions"
    _attr_icon = "mdi:creation-outline"

    def __init__(
        self,
        coordinator: HermesAgentDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize automation suggestions sensor."""
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_automation_suggestions"
        sw_version = coordinator.data.get("version") if coordinator.data else None
        self._attr_device_info = get_device_info(entry, sw_version)
        self._state = "No Suggestions"
        self._attributes: dict[str, Any] = {
            "description": None,
            "yaml_block": None,
            "last_update": None,
            "entities_processed_count": 0,
            "model": None,
        }

    @property
    def native_value(self) -> str:
        """Return state of sensor."""
        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return suggestions attributes."""
        return self._attributes

    def set_suggestion(
        self,
        description: str,
        yaml_block: str,
        model: str,
        entities_processed_count: int,
    ) -> None:
        """Update suggestion content and state."""
        self._state = "Suggestions Available"
        self._attributes = {
            "description": description,
            "yaml_block": yaml_block,
            "last_update": datetime.now(UTC).isoformat(),
            "entities_processed_count": entities_processed_count,
            "model": model,
        }
        self.async_write_ha_state()
