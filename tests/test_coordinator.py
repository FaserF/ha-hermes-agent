"""Test Hermes Agent data update coordinator."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.hermes_agent.client import CannotConnect
from custom_components.hermes_agent.coordinator import (
    HermesAgentDataUpdateCoordinator,
)


@pytest.mark.asyncio
async def test_coordinator_update_success(hass):
    """Test successful coordinator update."""
    client = MagicMock()
    client.async_check_health = AsyncMock(
        return_value={
            "status": "ok",
            "version": "1.0.0",
            "reachable": True,
            "latency_ms": 12.3,
        }
    )
    client.async_get_health_detailed = AsyncMock(
        return_value={
            "status": "healthy",
            "gateway_state": "idle",
            "active_agents": 1,
            "gateway_busy": False,
            "platforms": {"telegram": {"state": "connected"}},
            "readiness": {"api": True},
            "metrics_today": {
                "requests": 10,
                "messages": 20,
                "tokens": 500,
            },
        }
    )
    client.async_get_models = AsyncMock(return_value=["hermes-agent"])
    client.async_get_sessions = AsyncMock(
        return_value=[{"id": "sess_1"}, {"id": "sess_2"}]
    )
    client.async_get_jobs = AsyncMock(return_value=[{"id": "job_1"}])
    client.async_get_skills = AsyncMock(return_value=[{"id": "skill_1"}])
    client.async_get_toolsets = AsyncMock(return_value=[])
    client.async_get_capabilities = AsyncMock(return_value={})
    client.async_get_model_options = AsyncMock(return_value=[])

    coord = HermesAgentDataUpdateCoordinator(hass, client)
    data = await coord._async_update_data()

    assert data["status"] == "ok"
    assert data["gateway_state"] == "idle"
    assert data["models"] == ["hermes-agent"]
    assert data["active_agents"] == 1
    assert data["sessions_count"] == 2
    assert data["jobs_count"] == 1
    assert data["skills_count"] == 1
    assert data["metrics_today"]["requests"] == 10
    assert data["metrics_today"]["tokens"] == 500
    assert data["latency_ms"] == 12.3
    assert data["telegram_sessions_count"] == 0
    assert data["sessions_by_source"] == {"unknown": 2}


@pytest.mark.asyncio
async def test_coordinator_update_failure(hass):
    """Test coordinator update raises UpdateFailed on connection failure."""
    client = MagicMock()
    client.async_check_health = AsyncMock(side_effect=CannotConnect("Server down"))

    coord = HermesAgentDataUpdateCoordinator(hass, client)
    with pytest.raises(UpdateFailed):
        await coord._async_update_data()
