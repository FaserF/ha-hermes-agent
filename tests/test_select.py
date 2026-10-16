"""Test Hermes Agent select platform."""

from unittest.mock import MagicMock

import pytest

from custom_components.hermes_agent.const import (
    CONF_AI_TASK_MODEL,
    CONF_CHAT_MODEL,
    DOMAIN,
)
from custom_components.hermes_agent.select import (
    HermesAgentChatModelSelect,
    HermesAgentTaskModelSelect,
    async_setup_entry,
)


@pytest.mark.asyncio
async def test_select_setup_entry(hass, mock_config_entry):
    """Test select platform setup."""
    mock_add = MagicMock()
    mock_coord = MagicMock()
    mock_coord.data = {"models": ["hermes-agent", "hermes-3-70b"]}

    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            "coordinator": mock_coord,
        }
    }

    await async_setup_entry(hass, mock_config_entry, mock_add)
    assert mock_add.called
    entities = mock_add.call_args[0][0]
    assert len(entities) == 2


@pytest.mark.asyncio
async def test_select_options_and_selection(hass, mock_config_entry):
    """Test model selection and option changes."""
    mock_coord = MagicMock()
    mock_coord.data = {"models": ["hermes-agent", "hermes-3-70b"]}

    chat_select = HermesAgentChatModelSelect(mock_coord, mock_config_entry)
    chat_select.hass = hass
    assert "hermes-agent" in chat_select.options
    assert "hermes-3-70b" in chat_select.options
    assert chat_select.current_option == "hermes-agent"

    await chat_select.async_select_option("hermes-3-70b")
    assert mock_config_entry.options[CONF_CHAT_MODEL] == "hermes-3-70b"

    task_select = HermesAgentTaskModelSelect(mock_coord, mock_config_entry)
    task_select.hass = hass
    await task_select.async_select_option("hermes-3-70b")
    assert mock_config_entry.options[CONF_AI_TASK_MODEL] == "hermes-3-70b"
