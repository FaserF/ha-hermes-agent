"""Test notify platform in ha-hermes-agent."""

from unittest.mock import AsyncMock, MagicMock

from custom_components.hermes_agent.const import (
    DATA_CLIENT,
    DATA_COORDINATOR,
    DOMAIN,
)
from custom_components.hermes_agent.notify import (
    HermesAgentNotifyEntity,
    async_setup_entry,
)


async def test_notify_setup_and_send(hass, mock_config_entry):
    """Test notify platform setup and send_message."""
    mock_coordinator = MagicMock()
    mock_client = MagicMock()
    mock_client.async_send_notification = AsyncMock()

    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            DATA_COORDINATOR: mock_coordinator,
            DATA_CLIENT: mock_client,
        }
    }

    added_entities = []
    await async_setup_entry(
        hass,
        mock_config_entry,
        lambda entities: added_entities.extend(entities),
    )

    assert len(added_entities) == 1
    notify_entity = added_entities[0]
    assert isinstance(notify_entity, HermesAgentNotifyEntity)
    assert notify_entity.unique_id == f"{mock_config_entry.entry_id}_notify"

    # Send notification
    await notify_entity.async_send_message("Test message", title="Alert")
    mock_client.async_send_notification.assert_called_once()
