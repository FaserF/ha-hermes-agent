"""Test Hermes Agent diagnostics."""

from unittest.mock import MagicMock

import pytest

from custom_components.hermes_agent.const import DOMAIN
from custom_components.hermes_agent.diagnostics import (
    async_get_config_entry_diagnostics,
)


@pytest.mark.asyncio
async def test_diagnostics_redaction(hass, mock_config_entry):
    """Test diagnostics redacts sensitive keys."""
    mock_coord = MagicMock()
    mock_coord.last_update_success = True
    mock_coord.data = {
        "status": "ok",
        "models": ["hermes-agent"],
    }

    mock_client = MagicMock()
    mock_client.v1_url = "http://100.64.0.1:8642/v1"
    mock_client.root_url = "http://100.64.0.1:8642"
    mock_client._api_key = "secret_key"

    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            "coordinator": mock_coord,
            "client": mock_client,
        }
    }

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert "entry" in diag
    assert diag["entry"]["data"]["api_key"] == "**REDACTED**"
    assert diag["client"]["has_api_key"] is True
    assert diag["coordinator"]["models_count"] == 1
    assert len(diag["devices"]) >= 1
    assert len(diag["entities"]) >= 1
