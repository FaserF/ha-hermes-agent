"""Test Hermes Agent button platform."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.hermes_agent.button import (
    HermesAgentHealthCheckButton,
    HermesAgentRefreshButton,
    async_setup_entry,
)
from custom_components.hermes_agent.const import DOMAIN


@pytest.mark.asyncio
async def test_button_setup_entry(hass, mock_config_entry):
    """Test button platform setup."""
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
async def test_button_press_actions(hass, mock_config_entry):
    """Test pressing refresh and health check buttons."""
    mock_coord = MagicMock()
    mock_coord.async_refresh = AsyncMock()
    mock_coord.data = {"version": "1.0.0"}

    mock_client = MagicMock()
    mock_client.async_get_health_detailed = AsyncMock()

    btn_refresh = HermesAgentRefreshButton(mock_coord, mock_client, mock_config_entry)
    await btn_refresh.async_press()
    assert mock_coord.async_refresh.called

    btn_health = HermesAgentHealthCheckButton(
        mock_coord, mock_client, mock_config_entry
    )
    await btn_health.async_press()
    assert mock_client.async_get_health_detailed.called


@pytest.mark.asyncio
async def test_trigger_job_button(mock_config_entry):
    """Test HermesAgentTriggerJobButton press action."""
    from custom_components.hermes_agent.button import HermesAgentTriggerJobButton

    mock_coord = MagicMock()
    mock_coord.async_request_refresh = AsyncMock()
    mock_coord.data = {"version": "1.0.0"}

    mock_client = MagicMock()
    mock_client.async_run_job = AsyncMock()

    btn_job = HermesAgentTriggerJobButton(
        mock_coord, mock_client, mock_config_entry, "job_sync_1", {"name": "Sync Job"}
    )
    await btn_job.async_press()
    mock_client.async_run_job.assert_called_once_with("job_sync_1")
    assert mock_coord.async_request_refresh.called
