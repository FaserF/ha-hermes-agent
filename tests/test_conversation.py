"""Test Hermes Agent conversation entity."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.conversation import ConversationInput

from custom_components.hermes_agent.conversation import (
    HermesAgentConversationEntity,
    async_setup_entry,
)


@pytest.mark.asyncio
async def test_conversation_setup_entry(hass, mock_config_entry):
    """Test conversation entity setup."""
    mock_add = MagicMock()
    mock_client = MagicMock()
    mock_coord = MagicMock()

    hass.data["hermes_agent"] = {
        mock_config_entry.entry_id: {
            "client": mock_client,
            "coordinator": mock_coord,
        }
    }

    await async_setup_entry(hass, mock_config_entry, mock_add)
    assert mock_add.called
    entities = mock_add.call_args[0][0]
    assert len(entities) == 1
    assert isinstance(entities[0], HermesAgentConversationEntity)


@pytest.mark.asyncio
async def test_conversation_process_text(hass, mock_config_entry):
    """Test standard text conversation roundtrip."""
    mock_client = MagicMock()
    mock_client.async_chat_completion = AsyncMock(
        return_value={
            "id": "cmpl_1",
            "choices": [{"message": {"role": "assistant", "content": "The light is turned on."}}],
            "usage": {"total_tokens": 25},
        }
    )
    mock_coord = MagicMock()

    entity = HermesAgentConversationEntity(mock_config_entry, mock_client, mock_coord)
    entity.hass = hass

    user_input = ConversationInput(
        text="Turn on the light",
        conversation_id="conv_123",
        language="en",
    )

    result = await entity.async_process(user_input)
    assert result.response.speech == "The light is turned on."
    assert result.conversation_id == "conv_123"
    assert result.conversation_id in entity.history
