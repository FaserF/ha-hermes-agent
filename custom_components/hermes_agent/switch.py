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

    known_job_ids: set[str] = set()

    def _get_new_job_entities() -> list[SwitchEntity]:
        new_entities: list[SwitchEntity] = []
        jobs = coordinator.data.get("jobs", []) if coordinator.data else []
        for job in jobs:
            job_id = job.get("id")
            if job_id and job_id not in known_job_ids:
                known_job_ids.add(job_id)
                new_entities.append(
                    HermesAgentJobSwitch(coordinator, entry, client, job_id, job)
                )
        return new_entities

    entities.extend(_get_new_job_entities())
    async_add_entities(entities)

    coordinator.async_add_listener(
        lambda: async_add_entities(_get_new_job_entities())
    )


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


class HermesAgentJobSwitch(
    CoordinatorEntity[HermesAgentDataUpdateCoordinator], SwitchEntity
):
    """Switch entity to pause or resume a Hermes Agent scheduled job."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:calendar-sync"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: HermesAgentDataUpdateCoordinator,
        entry: ConfigEntry,
        client: HermesAgentClient,
        job_id: str,
        job_data: dict[str, Any],
    ) -> None:
        """Initialize job switch."""
        super().__init__(coordinator)
        self.entry = entry
        self.client = client
        self.job_id = job_id
        job_name = job_data.get("name") or job_id
        self._attr_name = f"Job {job_name}"
        self._attr_unique_id = f"{entry.entry_id}_job_{job_id}"
        sw_version = coordinator.data.get("version") if coordinator.data else None
        self._attr_device_info = get_device_info(entry, sw_version)

    def _get_job_data(self) -> dict[str, Any]:
        """Get live job data from coordinator."""
        if not self.coordinator.data:
            return {}
        jobs = self.coordinator.data.get("jobs", [])
        for job in jobs:
            if job.get("id") == self.job_id:
                return job
        return {}

    @property
    def is_on(self) -> bool:
        """Return whether job is currently active/enabled."""
        job = self._get_job_data()
        if not job:
            return False
        return bool(job.get("enabled", True) and job.get("state") != "paused")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes for this job."""
        job = self._get_job_data()
        return {
            "job_id": self.job_id,
            "schedule": (
                job.get("schedule_display")
                or (job.get("schedule", {}) or {}).get("expr")
            ),
            "next_run_at": job.get("next_run_at"),
            "last_run_at": job.get("last_run_at"),
            "last_status": job.get("last_status"),
            "failure_streak": job.get("failure_streak", 0),
            "state": job.get("state"),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Resume the scheduled job."""
        await self.client.async_resume_job(self.job_id)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Pause the scheduled job."""
        await self.client.async_pause_job(self.job_id)
        await self.coordinator.async_request_refresh()

