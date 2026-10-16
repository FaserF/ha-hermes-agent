"""Config flow for Hermes Agent integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import aiohttp_client, llm
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TemplateSelector,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .client import CannotConnect, HermesAgentClient, InvalidAuth
from .const import (
    CONF_AI_TASK_MAX_TOKENS,
    CONF_AI_TASK_MODEL,
    CONF_AI_TASK_PROMPT,
    CONF_AI_TASK_TEMPERATURE,
    CONF_API_KEY,
    CONF_API_URL,
    CONF_CHAT_MODEL,
    CONF_LLM_HASS_API,
    CONF_MAX_TOKENS,
    CONF_PROMPT,
    CONF_TEMPERATURE,
    CONF_TOP_P,
    DEFAULT_AI_TASK_MAX_TOKENS,
    DEFAULT_AI_TASK_MODEL,
    DEFAULT_AI_TASK_PROMPT,
    DEFAULT_AI_TASK_TEMPERATURE,
    DEFAULT_API_URL,
    DEFAULT_CHAT_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_NAME,
    DEFAULT_PROMPT,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DOMAIN,
    LOGGER,
)


class HermesAgentConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hermes Agent."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_url = user_input[CONF_API_URL].rstrip("/")
            api_key = user_input.get(CONF_API_KEY)

            # Prevent duplicate instances with identical normalized API URL
            await self.async_set_unique_id(api_url.lower())
            self._abort_if_unique_id_configured()

            session = aiohttp_client.async_get_clientsession(self.hass)
            client = HermesAgentClient(session=session, api_url=api_url, api_key=api_key)

            try:
                health = await client.async_check_health()
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception as err:
                LOGGER.exception("Unexpected exception connecting to Hermes Agent: %s", err)
                errors["base"] = "unknown"
            else:
                title = f"{DEFAULT_NAME} ({health.get('version', 'Gateway')})"
                return self.async_create_entry(title=title, data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_API_URL, default=DEFAULT_API_URL): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.URL)
                ),
                vol.Optional(CONF_API_KEY): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return HermesAgentOptionsFlowHandler(config_entry)


class HermesAgentOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Hermes Agent options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        entry_data = self.config_entry.data
        entry_options = self.config_entry.options

        # Fetch models from coordinator or direct client
        models = [DEFAULT_CHAT_MODEL]
        try:
            entry_store = self.hass.data.get(DOMAIN, {}).get(self.config_entry.entry_id, {})
            coordinator = entry_store.get("coordinator")
            if coordinator and coordinator.models:
                models = coordinator.models
            else:
                session = aiohttp_client.async_get_clientsession(self.hass)
                client = HermesAgentClient(
                    session=session,
                    api_url=entry_data[CONF_API_URL],
                    api_key=entry_data.get(CONF_API_KEY),
                )
                fetched = await client.async_get_models()
                if fetched:
                    models = fetched
        except Exception as err:
            LOGGER.debug("Could not fetch models for options flow: %s", err)

        model_options = [SelectOptionDict(value=m, label=m) for m in models]

        # Home Assistant LLM APIs
        hass_apis: list[SelectOptionDict] = [
            SelectOptionDict(
                value="none",
                label="No Control (Conversation Only)",
            )
        ]
        try:
            available_apis = llm.async_get_apis(self.hass)
            for api in available_apis:
                hass_apis.append(SelectOptionDict(value=api.id, label=api.name))
        except Exception:
            pass

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_CHAT_MODEL,
                    default=entry_options.get(CONF_CHAT_MODEL, DEFAULT_CHAT_MODEL),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=model_options,
                        mode=SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                    )
                ),
                vol.Optional(
                    CONF_LLM_HASS_API,
                    default=entry_options.get(CONF_LLM_HASS_API, "none"),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=hass_apis,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_PROMPT,
                    default=entry_options.get(CONF_PROMPT, DEFAULT_PROMPT),
                ): TemplateSelector(),
                vol.Optional(
                    CONF_TEMPERATURE,
                    default=entry_options.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0,
                        max=2.0,
                        step=0.05,
                        mode=NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Optional(
                    CONF_TOP_P,
                    default=entry_options.get(CONF_TOP_P, DEFAULT_TOP_P),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0,
                        max=1.0,
                        step=0.05,
                        mode=NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Optional(
                    CONF_MAX_TOKENS,
                    default=entry_options.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=64,
                        max=32768,
                        step=64,
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_AI_TASK_MODEL,
                    default=entry_options.get(CONF_AI_TASK_MODEL, DEFAULT_AI_TASK_MODEL),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=model_options,
                        mode=SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                    )
                ),
                vol.Optional(
                    CONF_AI_TASK_PROMPT,
                    default=entry_options.get(CONF_AI_TASK_PROMPT, DEFAULT_AI_TASK_PROMPT),
                ): TemplateSelector(),
                vol.Optional(
                    CONF_AI_TASK_TEMPERATURE,
                    default=entry_options.get(
                        CONF_AI_TASK_TEMPERATURE, DEFAULT_AI_TASK_TEMPERATURE
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0.0,
                        max=2.0,
                        step=0.05,
                        mode=NumberSelectorMode.SLIDER,
                    )
                ),
                vol.Optional(
                    CONF_AI_TASK_MAX_TOKENS,
                    default=entry_options.get(
                        CONF_AI_TASK_MAX_TOKENS, DEFAULT_AI_TASK_MAX_TOKENS
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=64,
                        max=32768,
                        step=64,
                        mode=NumberSelectorMode.BOX,
                    )
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
