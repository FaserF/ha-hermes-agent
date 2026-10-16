"""Test Hermes Agent sensor platform."""

from unittest.mock import MagicMock

import pytest

from custom_components.hermes_agent.const import DOMAIN
from custom_components.hermes_agent.sensor import (
    SENSOR_DESCRIPTIONS,
    HermesAgentAutomationSuggestionsSensor,
    HermesAgentSensor,
    async_setup_entry,
)


@pytest.mark.asyncio
async def test_sensor_setup_entry(hass, mock_config_entry):
    """Test setup of all sensor entities."""
    mock_add = MagicMock()
    mock_coord = MagicMock()
    mock_coord.data = {
        "status": "healthy",
        "gateway_state": "idle",
        "latency_ms": 42.5,
        "models": ["hermes-agent"],
        "models_count": 1,
        "active_agents": 2,
        "sessions_count": 5,
        "jobs_count": 1,
        "skills_count": 8,
        "metrics_today": {
            "requests": 120,
            "messages": 450,
            "tokens": 25000,
        },
        "readiness": {
            "checks": {"disk": {"used_percent": 35.8, "free_bytes": 1000000000}}
        },
        "platforms": {"telegram": {"state": "connected"}},
        "version": "1.0.0",
    }

    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            "coordinator": mock_coord,
        }
    }

    await async_setup_entry(hass, mock_config_entry, mock_add)
    assert mock_add.called
    entities = list(mock_add.call_args[0][0])
    assert len(entities) == len(SENSOR_DESCRIPTIONS) + 1


@pytest.mark.asyncio
async def test_sensor_native_values(mock_config_entry):
    """Test specific sensor readings."""
    mock_coord = MagicMock()
    mock_coord.data = {
        "latency_ms": 15.2,
        "readiness": {
            "checks": {"disk": {"used_percent": 42.0, "free_bytes": 500000000}}
        },
        "active_agents": 3,
        "platforms": {"telegram": {"state": "connected"}},
    }

    desc_latency = next(d for d in SENSOR_DESCRIPTIONS if d.key == "latency_ms")
    sensor_latency = HermesAgentSensor(mock_coord, mock_config_entry, desc_latency)
    assert sensor_latency.native_value == 15.2

    desc_disk = next(d for d in SENSOR_DESCRIPTIONS if d.key == "disk_usage")
    sensor_disk = HermesAgentSensor(mock_coord, mock_config_entry, desc_disk)
    assert sensor_disk.native_value == 42.0

    desc_platforms = next(
        d for d in SENSOR_DESCRIPTIONS if d.key == "connected_platforms"
    )
    sensor_platforms = HermesAgentSensor(mock_coord, mock_config_entry, desc_platforms)
    assert sensor_platforms.native_value == 1

    mock_coord.data.update(
        {
            "disk_free_gb": 18.15,
            "latency_p95_ms": 120.4,
            "active_runs": 2,
            "toolsets_count": 14,
            "latest_job": {"name": "Test Backup Job", "last_status": "ok"},
            "readiness": {"status": "ok"},
        }
    )

    desc_df = next(d for d in SENSOR_DESCRIPTIONS if d.key == "disk_free_gb")
    assert (
        HermesAgentSensor(mock_coord, mock_config_entry, desc_df).native_value == 18.15
    )

    desc_p95 = next(d for d in SENSOR_DESCRIPTIONS if d.key == "latency_p95_ms")
    assert (
        HermesAgentSensor(mock_coord, mock_config_entry, desc_p95).native_value == 120.4
    )

    desc_runs = next(d for d in SENSOR_DESCRIPTIONS if d.key == "active_runs")
    assert HermesAgentSensor(mock_coord, mock_config_entry, desc_runs).native_value == 2

    desc_ts = next(d for d in SENSOR_DESCRIPTIONS if d.key == "toolsets_count")
    assert HermesAgentSensor(mock_coord, mock_config_entry, desc_ts).native_value == 14

    desc_job = next(d for d in SENSOR_DESCRIPTIONS if d.key == "latest_job_status")
    assert (
        HermesAgentSensor(mock_coord, mock_config_entry, desc_job).native_value
        == "Test Backup Job"
    )

    desc_ready = next(d for d in SENSOR_DESCRIPTIONS if d.key == "readiness")
    assert (
        HermesAgentSensor(mock_coord, mock_config_entry, desc_ready).native_value
        == "ok"
    )


@pytest.mark.asyncio
async def test_automation_suggestions_sensor(mock_config_entry):
    """Test suggestions sensor updates."""
    mock_coord = MagicMock()
    sugg_sensor = HermesAgentAutomationSuggestionsSensor(mock_coord, mock_config_entry)
    assert sugg_sensor.native_value == "No Suggestions"

    sugg_sensor.set_suggestion(
        description="Turn off lights when away",
        yaml_block="alias: Away Lights",
        model="hermes-agent",
        entities_processed_count=5,
    )
    assert sugg_sensor.native_value == "Suggestions Available"
    assert (
        sugg_sensor.extra_state_attributes["description"] == "Turn off lights when away"
    )
    assert sugg_sensor.extra_state_attributes["entities_processed_count"] == 5
