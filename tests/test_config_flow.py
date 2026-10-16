"""Test Hermes Agent config flow."""

from unittest.mock import AsyncMock, patch

import pytest

from custom_components.hermes_agent.client import CannotConnect, InvalidAuth
from custom_components.hermes_agent.config_flow import (
    HermesAgentConfigFlow,
    HermesAgentOptionsFlowHandler,
)
from custom_components.hermes_agent.const import (
    CONF_API_KEY,
    CONF_API_URL,
    CONF_CHAT_MODEL,
)


@pytest.mark.asyncio
async def test_config_flow_show_form(hass):
    """Test initial user step shows form."""
    flow = HermesAgentConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user(user_input=None)
    assert result["type"] == "form"
    assert result["step_id"] == "user"


@pytest.mark.asyncio
async def test_config_flow_success(hass):
    """Test successful config flow."""
    flow = HermesAgentConfigFlow()
    flow.hass = hass

    user_input = {
        CONF_API_URL: "http://100.64.0.1:8642",
        CONF_API_KEY: "valid_key",
    }

    with patch(
        "custom_components.hermes_agent.client.HermesAgentClient.async_check_health",
        new_callable=AsyncMock,
        return_value={"status": "ok"},
    ):
        result = await flow.async_step_user(user_input=user_input)
        assert result["type"] == "create_entry"
        assert result["title"] == "Hermes Agent (Gateway)"
        assert result["data"][CONF_API_URL] == "http://100.64.0.1:8642"


@pytest.mark.asyncio
async def test_config_flow_cannot_connect(hass):
    """Test connection error in config flow."""
    flow = HermesAgentConfigFlow()
    flow.hass = hass

    user_input = {
        CONF_API_URL: "http://invalid-host:8642",
    }

    with patch(
        "custom_components.hermes_agent.client.HermesAgentClient.async_check_health",
        new_callable=AsyncMock,
        side_effect=CannotConnect("Timeout"),
    ):
        result = await flow.async_step_user(user_input=user_input)
        assert result["type"] == "form"
        assert result["errors"]["base"] == "cannot_connect"


@pytest.mark.asyncio
async def test_config_flow_invalid_auth(hass):
    """Test auth error in config flow."""
    flow = HermesAgentConfigFlow()
    flow.hass = hass

    user_input = {
        CONF_API_URL: "http://100.64.0.1:8642",
        CONF_API_KEY: "wrong_key",
    }

    with patch(
        "custom_components.hermes_agent.client.HermesAgentClient.async_check_health",
        new_callable=AsyncMock,
        side_effect=InvalidAuth("Forbidden"),
    ):
        result = await flow.async_step_user(user_input=user_input)
        assert result["type"] == "form"
        assert result["errors"]["base"] == "invalid_auth"


@pytest.mark.asyncio
async def test_options_flow(hass, mock_config_entry):
    """Test options flow initialization and saving."""
    flow = HermesAgentOptionsFlowHandler(mock_config_entry)
    flow.hass = hass

    result = await flow.async_step_init(user_input=None)
    assert result["type"] == "form"
    assert result["step_id"] == "init"

    new_options = {
        CONF_CHAT_MODEL: "hermes-agent-v2",
        "temperature": 0.5,
    }
    save_result = await flow.async_step_init(user_input=new_options)
    assert save_result["type"] == "create_entry"
    assert save_result["data"][CONF_CHAT_MODEL] == "hermes-agent-v2"
