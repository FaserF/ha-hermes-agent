"""Test Hermes Agent switch platform."""

from unittest.mock import MagicMock

import pytest

from custom_components.hermes_agent.const import (
    CONF_AUTONOMOUS_EXECUTION,
    CONF_TELEMETRY,
    DOMAIN,
)
from custom_components.hermes_agent.switch import (
    HermesAgentAutonomousSwitch,
    HermesAgentTelemetrySwitch,
    async_setup_entry,
)


@pytest.mark.asyncio
async def test_switch_setup_entry(hass, mock_config_entry):
    """Test switch platform setup."""
    mock_add = MagicMock()
    mock_coord = MagicMock()
    mock_client = MagicMock()

    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            "coordinator": mock_coord,
            "client": mock_client,
        }
    }

    await async_setup_entry(hass, mock_config_entry, mock_add)
    assert mock_add.called
    entities = mock_add.call_args[0][0]
    assert len(entities) == 2


@pytest.mark.asyncio
async def test_switch_toggle_actions(hass, mock_config_entry):
    """Test toggling autonomous and telemetry switches."""
    mock_coord = MagicMock()
    mock_client = MagicMock()

    auto_switch = HermesAgentAutonomousSwitch(
        mock_coord, mock_config_entry, mock_client
    )
    auto_switch.hass = hass
    assert auto_switch.is_on is True

    await auto_switch.async_turn_off()
    assert mock_config_entry.options[CONF_AUTONOMOUS_EXECUTION] is False

    await auto_switch.async_turn_on()
    assert mock_config_entry.options[CONF_AUTONOMOUS_EXECUTION] is True

    telemetry_switch = HermesAgentTelemetrySwitch(
        mock_coord, mock_config_entry, mock_client
    )
    telemetry_switch.hass = hass
    assert telemetry_switch.is_on is True

    await telemetry_switch.async_turn_off()
    assert mock_config_entry.options[CONF_TELEMETRY] is False

    await telemetry_switch.async_turn_on()
    assert mock_config_entry.options[CONF_TELEMETRY] is True


@pytest.mark.asyncio
async def test_job_switch(hass, mock_config_entry):
    """Test dynamic scheduled job switch toggle actions."""
    from unittest.mock import AsyncMock

    from custom_components.hermes_agent.switch import HermesAgentJobSwitch

    mock_coord = MagicMock()
    mock_coord.data = {
        "jobs": [
            {
                "id": "job_sync_1",
                "name": "Sync Job",
                "enabled": True,
                "state": "scheduled",
                "schedule_display": "every 2h",
                "last_status": "ok",
            }
        ]
    }
    mock_coord.async_request_refresh = AsyncMock()

    mock_client = MagicMock()
    mock_client.async_pause_job = AsyncMock()
    mock_client.async_resume_job = AsyncMock()

    job_switch = HermesAgentJobSwitch(
        mock_coord, mock_config_entry, mock_client, "job_sync_1", mock_coord.data["jobs"][0]
    )
    job_switch.hass = hass

    assert job_switch.is_on is True
    assert job_switch.extra_state_attributes["schedule"] == "every 2h"

    await job_switch.async_turn_off()
    mock_client.async_pause_job.assert_called_once_with("job_sync_1")

    await job_switch.async_turn_on()
    mock_client.async_resume_job.assert_called_once_with("job_sync_1")

