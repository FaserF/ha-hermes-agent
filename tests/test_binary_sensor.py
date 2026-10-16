"""Test Hermes Agent binary sensor platform."""

from unittest.mock import MagicMock

import pytest

from custom_components.hermes_agent.binary_sensor import (
    BINARY_SENSOR_DESCRIPTIONS,
    HermesAgentBinarySensor,
    async_setup_entry,
)
from custom_components.hermes_agent.const import DOMAIN


@pytest.mark.asyncio
async def test_binary_sensor_setup_entry(hass, mock_config_entry):
    """Test setup of all binary sensor entities."""
    mock_add = MagicMock()
    mock_coord = MagicMock()
    mock_coord.data = {
        "status": "ok",
        "reachable": True,
        "gateway_busy": True,
        "platforms": {
            "telegram": {"state": "connected"},
            "teams": {"state": "disconnected"},
        },
    }

    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            "coordinator": mock_coord,
        }
    }

    await async_setup_entry(hass, mock_config_entry, mock_add)
    assert mock_add.called
    entities = list(mock_add.call_args[0][0])
    assert len(entities) == len(BINARY_SENSOR_DESCRIPTIONS)


@pytest.mark.asyncio
async def test_binary_sensor_states(mock_config_entry):
    """Test binary sensor evaluation logic."""
    mock_coord = MagicMock()
    mock_coord.last_update_success = True
    mock_coord.data = {
        "status": "ok",
        "reachable": True,
        "gateway_busy": True,
        "platforms": {
            "telegram": {"state": "connected"},
            "teams": {"state": "disconnected"},
        },
    }

    desc_conn = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "connectivity")
    conn_sensor = HermesAgentBinarySensor(mock_coord, mock_config_entry, desc_conn)
    assert conn_sensor.is_on is True

    desc_prob = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "problem")
    prob_sensor = HermesAgentBinarySensor(mock_coord, mock_config_entry, desc_prob)
    assert prob_sensor.is_on is False

    desc_busy = next(d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "busy")
    busy_sensor = HermesAgentBinarySensor(mock_coord, mock_config_entry, desc_busy)
    assert busy_sensor.is_on is True

    desc_telegram = next(
        d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "telegram_connected"
    )
    telegram_sensor = HermesAgentBinarySensor(
        mock_coord, mock_config_entry, desc_telegram
    )
    assert telegram_sensor.is_on is True

    desc_teams = next(
        d for d in BINARY_SENSOR_DESCRIPTIONS if d.key == "teams_connected"
    )
    teams_sensor = HermesAgentBinarySensor(mock_coord, mock_config_entry, desc_teams)
    assert teams_sensor.is_on is False
