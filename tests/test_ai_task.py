"""Test Hermes Agent AI Task platform."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.hermes_agent.ai_task import (
    HermesAgentAITaskEntity,
    async_setup_entry,
)
from custom_components.hermes_agent.const import DOMAIN


@pytest.mark.asyncio
async def test_ai_task_setup_entry(hass, mock_config_entry):
    """Test setting up ai_task platform."""
    mock_add = MagicMock()
    mock_client = MagicMock()
    mock_coord = MagicMock()

    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            "client": mock_client,
            "coordinator": mock_coord,
        }
    }

    await async_setup_entry(hass, mock_config_entry, mock_add)
    assert mock_add.called
    entities = mock_add.call_args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], HermesAgentAITaskEntity)


@pytest.mark.asyncio
async def test_ai_task_execution(hass, mock_config_entry):
    """Test executing generative AI task."""
    mock_client = MagicMock()
    mock_client.async_chat_completion = AsyncMock(
        return_value={
            "choices": [{"message": {"content": "Reasoning complete."}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        }
    )
    mock_coord = MagicMock()

    entity = HermesAgentAITaskEntity(mock_config_entry, mock_client, mock_coord)
    entity.hass = hass

    assert entity.device_info["manufacturer"] == "Nous Research"
    assert entity.device_info["model"] == "Hermes Agent"

    result = await entity.async_execute_task(
        prompt="Analyze automation anomalies",
        model="hermes-agent",
    )

    assert result["success"] is True
    assert result["response"] == "Reasoning complete."
    assert result["model"] == "hermes-agent"
    assert result["usage"]["total_tokens"] == 30
