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

            # Sessions, jobs, skills, toolsets
            sessions = await self.client.async_get_sessions()
            jobs = await self.client.async_get_jobs()
            skills = await self.client.async_get_skills()
            toolsets = await self.client.async_get_toolsets()

            capabilities = await self.client.async_get_capabilities()
            model_options = await self.client.async_get_model_options()

            version = (
                detailed.get("version")
                or health.get("version")
                or get_integration_version()
            )
            metrics_today = detailed.get("metrics_today") or {}
            api_server_info = detailed.get("api_server") or {}
            platforms = detailed.get("platforms") or {}
            readiness = detailed.get("readiness") or {}
            readiness_checks = readiness.get("checks") or {}

            disk_check = readiness_checks.get("disk") or {}
            disk_used_pct = disk_check.get("used_percent")
            free_bytes = disk_check.get("free_bytes")
            disk_free_gb = (
                round(free_bytes / (1024**3), 2) if free_bytes is not None else None
            )

            background_queues = detailed.get("background_queues") or {}
            active_runs = (
                background_queues.get("active_api_runs")
                if "active_api_runs" in background_queues
                else api_server_info.get("active_runs", 0)
            )

            enabled_toolsets = [t for t in toolsets if t.get("enabled", False)]
            latest_job = jobs[0] if jobs else None

            return {
                "reachable": health.get("reachable", True),
                "status": health.get("status", "ok"),
                "latency_ms": health.get("latency_ms"),
                "latency_p95_ms": metrics_today.get("latency_p95_ms"),
                "version": str(version),
                "models": models,
                "models_count": len(models),
                "gateway_state": detailed.get("gateway_state", "running"),
                "gateway_busy": detailed.get("gateway_busy", False),
                "active_agents": detailed.get("active_agents", 0),
                "active_runs": active_runs,
                "platforms": platforms,
                "api_server": api_server_info,
                "metrics_today": metrics_today,
                "readiness": readiness,
                "readiness_checks": readiness_checks,
                "disk_used_percent": disk_used_pct,
                "disk_free_gb": disk_free_gb,
                "sessions": sessions,
                "sessions_count": len(sessions),
                "jobs": jobs,
                "jobs_count": len(jobs),
                "latest_job": latest_job,
                "skills": skills,
                "skills_count": len(skills),
                "toolsets": toolsets,
                "toolsets_count": len(enabled_toolsets),
                "toolsets_total": len(toolsets),
                "capabilities": capabilities,
                "model_options": model_options,
            }
        except (CannotConnect, InvalidAuth, HermesAgentError) as err:
            raise UpdateFailed(f"Error communicating with Hermes Agent: {err}") from err
        except Exception as err:
            raise UpdateFailed(
                f"Unexpected error updating Hermes Agent data: {err}"
            ) from err
