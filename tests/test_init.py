"""Test Hermes Agent setup and unload lifecycles."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.hermes_agent import (
    async_reload_entry,
    async_setup,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.hermes_agent.const import (
    DOMAIN,
    SERVICE_ANALYZE_AUTOMATION,
    SERVICE_ANALYZE_CAMERA,
    SERVICE_CREATE_SESSION,
    SERVICE_DIAGNOSE_LOGS,
    SERVICE_EXECUTE_AI_TASK,
    SERVICE_PAUSE_JOB,
    SERVICE_REFRESH_STATUS,
    SERVICE_SEND_MESSAGE,
    SERVICE_SUGGEST_AUTOMATIONS,
)


@pytest.mark.asyncio
async def test_async_setup(hass):
    """Test setting up integration and services."""
    assert await async_setup(hass, {}) is True
    assert hass.services.async_register.call_count >= 2


@pytest.mark.asyncio
async def test_async_setup_and_unload_entry(hass, mock_config_entry):
    """Test setting up and unloading config entry."""
    with patch(
        "custom_components.hermes_agent.HermesAgentDataUpdateCoordinator.async_config_entry_first_refresh",
        new_callable=AsyncMock,
    ):
        result = await async_setup_entry(hass, mock_config_entry)
        assert result is True
        assert mock_config_entry.entry_id in hass.data[DOMAIN]
        assert hass.config_entries.async_forward_entry_setups.called

        unload_result = await async_unload_entry(hass, mock_config_entry)
        assert unload_result is True
        assert mock_config_entry.entry_id not in hass.data[DOMAIN]


@pytest.mark.asyncio
async def test_async_reload_entry(hass, mock_config_entry):
    """Test reloading config entry."""
    await async_reload_entry(hass, mock_config_entry)
    hass.config_entries.async_reload.assert_called_once_with(mock_config_entry.entry_id)


@pytest.mark.asyncio
async def test_services_execution(hass, mock_config_entry):
    """Test all service handlers."""
    registered_handlers = {}

    def mock_register(domain, service, handler, **kwargs):
        registered_handlers[service] = handler

    hass.services.async_register.side_effect = mock_register

    assert await async_setup(hass, {}) is True
    assert SERVICE_EXECUTE_AI_TASK in registered_handlers
    assert SERVICE_SEND_MESSAGE in registered_handlers
    assert SERVICE_REFRESH_STATUS in registered_handlers
    assert SERVICE_PAUSE_JOB in registered_handlers
    assert SERVICE_CREATE_SESSION in registered_handlers
    assert SERVICE_SUGGEST_AUTOMATIONS in registered_handlers
    assert SERVICE_ANALYZE_AUTOMATION in registered_handlers
    assert SERVICE_DIAGNOSE_LOGS in registered_handlers
    assert SERVICE_ANALYZE_CAMERA in registered_handlers

    mock_client = AsyncMock()
    mock_client.async_chat_completion = AsyncMock(
        return_value={
            "choices": [{"message": {"content": "Task result\n```yaml\nalias: Test\n```"}}],
            "model": "hermes-agent",
            "usage": {"total_tokens": 15},
        }
    )
    mock_client.async_send_session_chat = AsyncMock(return_value={"status": "ok"})
    mock_client.async_create_session = AsyncMock(return_value={"id": "sess_1", "title": "Test"})
    mock_client.async_pause_job = AsyncMock(return_value={"paused": True})

    mock_coord = AsyncMock()
    mock_coord.async_refresh = AsyncMock()
    mock_coord.data = {"status": "ok"}

    mock_sugg_sensor = MagicMock()

    hass.config_entries.async_entries.return_value = [mock_config_entry]
    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            "client": mock_client,
            "coordinator": mock_coord,
            "suggestions_sensor": mock_sugg_sensor,
        }
    }

    # Setup mock state for suggest_automations
    mock_state = MagicMock()
    mock_state.domain = "light"
    mock_state.entity_id = "light.living_room"
    mock_state.state = "on"
    mock_state.attributes = {"friendly_name": "Living Room Light"}
    hass.states.async_all.return_value = [mock_state]
    hass.states.get.return_value = mock_state

    # 1. execute_ai_task
    call_mock = AsyncMock()
    call_mock.data = {"prompt": "Run diagnostic check"}
    res = await registered_handlers[SERVICE_EXECUTE_AI_TASK](call_mock)
    assert "Task result" in res["response"]

    # 2. send_message
    call_mock.data = {"message": "Hello session", "session_id": "sess_1"}
    res2 = await registered_handlers[SERVICE_SEND_MESSAGE](call_mock)
    assert res2["session_id"] == "sess_1"

    # 3. refresh_status
    res3 = await registered_handlers[SERVICE_REFRESH_STATUS](call_mock)
    assert res3["success"] is True

    # 4. pause_job
    call_mock.data = {"job_id": "job_1"}
    res4 = await registered_handlers[SERVICE_PAUSE_JOB](call_mock)
    assert res4["success"] is True

    # 5. create_session
    call_mock.data = {"title": "New Session", "prompt": "Initial message"}
    res5 = await registered_handlers[SERVICE_CREATE_SESSION](call_mock)
    assert res5["session_id"] == "sess_1"

    # 6. suggest_automations
    call_mock.data = {"domains": ["light"], "send_notification": True}
    res6 = await registered_handlers[SERVICE_SUGGEST_AUTOMATIONS](call_mock)
    assert "yaml_block" in res6
    assert mock_sugg_sensor.set_suggestion.called

    # 7. analyze_automation
    call_mock.data = {"automation_entity_id": "automation.test"}
    res7 = await registered_handlers[SERVICE_ANALYZE_AUTOMATION](call_mock)
    assert "analysis" in res7

    # 8. diagnose_logs
    call_mock.data = {"log_text": "Sample error trace"}
    res8 = await registered_handlers[SERVICE_DIAGNOSE_LOGS](call_mock)
    assert "diagnosis" in res8

    # 9. analyze_camera
    with patch(
        "homeassistant.components.camera.async_get_image", new_callable=AsyncMock
    ) as mock_cam_img:
        mock_frame = MagicMock()
        mock_frame.content = b"fake_image_bytes"
        mock_frame.content_type = "image/jpeg"
        mock_cam_img.return_value = mock_frame

        call_mock.data = {"camera_entity_id": "camera.front_door"}
        res9 = await registered_handlers[SERVICE_ANALYZE_CAMERA](call_mock)
        assert res9["camera_entity_id"] == "camera.front_door"
        assert "analysis" in res9
