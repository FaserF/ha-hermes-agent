"""DataUpdateCoordinator for Hermes Agent."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import CannotConnect, HermesAgentClient, HermesAgentError, InvalidAuth
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER
from .helpers import get_integration_version

UPDATE_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)


class HermesAgentDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Hermes Agent data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: HermesAgentClient,
        update_interval: timedelta | None = None,
    ) -> None:
        """Initialize the coordinator."""
        if update_interval is None:
            update_interval = UPDATE_INTERVAL

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.client = client
        self.models: list[str] = []

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch status and telemetry from Hermes Agent."""
        try:
            health = await self.client.async_check_health()
            try:
                models = await self.client.async_get_models()
                self.models = models
            except Exception as err:
                if self.models:
                    LOGGER.debug("Could not refresh models, using cached list: %s", err)
                    models = self.models
                else:
                    raise

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
            if isinstance(model_options, dict):
                opt_models: list[str] = []
                for p in model_options.get("providers", []):
                    if isinstance(p, dict) and "models" in p:
                        p_models = p["models"]
                        if isinstance(p_models, dict):
                            opt_models.extend(list(p_models.keys()))
                        elif isinstance(p_models, list):
                            opt_models.extend([str(x) for x in p_models])
                if not opt_models and "models" in model_options:
                    raw_models = model_options["models"]
                    if isinstance(raw_models, dict):
                        opt_models = list(raw_models.keys())
                    elif isinstance(raw_models, list):
                        opt_models = [str(x) for x in raw_models]
                for m in opt_models:
                    if m not in models:
                        models.append(m)

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

            telegram_sessions = [s for s in sessions if s.get("source") == "telegram"]
            latest_telegram = telegram_sessions[0] if telegram_sessions else None

            sessions_by_source: dict[str, int] = {}
            for s in sessions:
                src = s.get("source", "unknown")
                sessions_by_source[src] = sessions_by_source.get(src, 0) + 1

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
                "sessions_by_source": sessions_by_source,
                "telegram_sessions": telegram_sessions,
                "telegram_sessions_count": len(telegram_sessions),
                "latest_telegram_session": latest_telegram,
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
