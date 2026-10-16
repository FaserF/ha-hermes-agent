"""DataUpdateCoordinator for Hermes Agent."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import CannotConnect, HermesAgentClient, HermesAgentError, InvalidAuth
from .const import DOMAIN, LOGGER
from .helpers import get_integration_version

UPDATE_INTERVAL = timedelta(seconds=30)


class HermesAgentDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Hermes Agent data."""

    def __init__(self, hass: HomeAssistant, client: HermesAgentClient) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client
        self.models: list[str] = []

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch status and telemetry from Hermes Agent."""
        try:
            # Basic health check
            health = await self.client.async_check_health()
            models = await self.client.async_get_models()
            self.models = models

            # Detailed health and gateway state
            try:
                detailed = await self.client.async_get_health_detailed()
            except Exception as err:
                LOGGER.debug("Could not fetch detailed health: %s", err)
                detailed = {}

            # Sessions, jobs, skills
            sessions = await self.client.async_get_sessions()
            jobs = await self.client.async_get_jobs()
            skills = await self.client.async_get_skills()

            version = detailed.get("version") or health.get("version") or get_integration_version()
            metrics_today = detailed.get("metrics_today") or {}
            api_server_info = detailed.get("api_server") or {}
            platforms = detailed.get("platforms") or {}
            readiness = detailed.get("readiness") or {}

            return {
                "reachable": health.get("reachable", True),
                "status": health.get("status", "ok"),
                "latency_ms": health.get("latency_ms"),
                "version": str(version),
                "models": models,
                "models_count": len(models),
                "gateway_state": detailed.get("gateway_state", "running"),
                "gateway_busy": detailed.get("gateway_busy", False),
                "active_agents": detailed.get("active_agents", 0),
                "platforms": platforms,
                "api_server": api_server_info,
                "metrics_today": metrics_today,
                "readiness": readiness,
                "sessions": sessions,
                "sessions_count": len(sessions),
                "jobs": jobs,
                "jobs_count": len(jobs),
                "skills": skills,
                "skills_count": len(skills),
            }
        except (CannotConnect, InvalidAuth, HermesAgentError) as err:
            raise UpdateFailed(f"Error communicating with Hermes Agent: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error updating Hermes Agent data: {err}") from err
