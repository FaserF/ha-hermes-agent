"""Notify platform for Hermes Agent integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.notify import (
    NotifyEntity,
    NotifyEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .client import HermesAgentClient
from .const import DATA_CLIENT, DATA_COORDINATOR, DOMAIN
from .coordinator import HermesAgentDataUpdateCoordinator
from .helpers import get_device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Hermes Agent notify entity from a config entry."""
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator: HermesAgentDataUpdateCoordinator = entry_data[DATA_COORDINATOR]
    client: HermesAgentClient = entry_data[DATA_CLIENT]

    async_add_entities([HermesAgentNotifyEntity(coordinator, client, entry)])


class HermesAgentNotifyEntity(
    CoordinatorEntity[HermesAgentDataUpdateCoordinator], NotifyEntity
):
    """Hermes Agent Notify Entity."""

    _attr_has_entity_name = True
    _attr_translation_key = "hermes_agent"
    _attr_name = "Hermes Agent"
    _attr_supported_features = NotifyEntityFeature.TITLE

    def __init__(
        self,
        coordinator: HermesAgentDataUpdateCoordinator,
        client: HermesAgentClient,
        entry: ConfigEntry,
    ) -> None:
        """Initialize notify entity."""
        super().__init__(coordinator)
        self._client = client
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_notify"
        self._attr_device_info = get_device_info(entry)

    async def async_send_message(
        self,
        message: str,
        title: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Send message via Hermes Agent to Telegram."""
        data = kwargs.get("data") or {}
        thread_id = data.get("thread_id") or kwargs.get("target") or "305748"
        chat_id = data.get("chat_id") or "649657901"
        enrich = data.get("enrich", True)
        inline_keyboard = data.get("inline_keyboard")
        disable_notification = data.get("disable_notification", False)

        try:
            await self._client.async_send_notification(
                message=message,
                title=title,
                thread_id=str(thread_id),
                chat_id=str(chat_id),
                enrich=bool(enrich),
                inline_keyboard=inline_keyboard,
                disable_notification=bool(disable_notification),
                data=data,
            )
        except Exception as err:
            _LOGGER.error("Failed to send notification via Hermes Agent: %s", err)
            raise
