"""Async client for the Hermes Agent API."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import aiohttp
from homeassistant.exceptions import HomeAssistantError

from .const import DEFAULT_CHAT_MODEL, LOGGER


class HermesAgentError(HomeAssistantError):
    """Base exception for Hermes Agent."""


class CannotConnect(HermesAgentError):
    """Error to indicate we cannot connect to Hermes Agent."""


class InvalidAuth(HermesAgentError):
    """Error to indicate invalid authentication token."""


class ModelNotFoundError(HermesAgentError):
    """Error to indicate requested model is not found."""


class HermesAgentClient:
    """Client for interacting with Hermes Agent Gateway and API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_url: str,
        api_key: str | None = None,
        timeout: float = 300.0,
    ) -> None:
        """Initialize the Hermes Agent client."""
        self._session = session
        self._api_key = api_key
        self._timeout = timeout

        clean_url = api_url.rstrip("/")
        if clean_url.endswith("/v1"):
            self._v1_url = clean_url
            self._root_url = clean_url[:-3]
        else:
            self._v1_url = f"{clean_url}/v1"
            self._root_url = clean_url

    @property
    def v1_url(self) -> str:
        """Return the v1 API URL."""
        return self._v1_url

    @property
    def root_url(self) -> str:
        """Return the root gateway URL."""
        return self._root_url

    def _get_headers(self) -> dict[str, str]:
        """Build request headers."""
        headers = {
            "User-Agent": "HomeAssistant-HermesAgent",
            "Accept": "application/json",
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def async_check_health(self) -> dict[str, Any]:
        """Check Hermes Agent health and connectivity."""
        url = f"{self._root_url}/health"
        headers = self._get_headers()
        start_time = time.monotonic()

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.get(url, headers=headers) as resp:
                    latency = round((time.monotonic() - start_time) * 1000, 2)
                    if resp.status == 401:
                        raise InvalidAuth("Invalid gateway API key (API_SERVER_KEY)")
                    if resp.status != 200:
                        text = await resp.text()
                        raise CannotConnect(
                            f"HTTP {resp.status} checking health: {text}"
                        )

                    data = await resp.json()
                    return {
                        "reachable": True,
                        "status": data.get("status", "ok"),
                        "platform": data.get("platform", "hermes-agent"),
                        "version": data.get("version", "unknown"),
                        "latency_ms": latency,
                    }
        except TimeoutError as err:
            raise CannotConnect(f"Timeout connecting to Hermes Agent at {url}") from err
        except aiohttp.ClientError as err:
            raise CannotConnect(
                f"ClientError connecting to Hermes Agent at {url}: {err}"
            ) from err

    async def async_get_health_detailed(self) -> dict[str, Any]:
        """Fetch detailed health status including readiness and platforms."""
        url = f"{self._root_url}/health/detailed"
        headers = self._get_headers()

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.get(url, headers=headers) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid gateway API key (API_SERVER_KEY)")
                    if resp.status != 200:
                        text = await resp.text()
                        raise CannotConnect(
                            f"HTTP {resp.status} fetching detailed health: {text}"
                        )
                    return await resp.json()
        except TimeoutError as err:
            raise CannotConnect(f"Timeout fetching detailed health from {url}") from err
        except aiohttp.ClientError as err:
            raise CannotConnect(
                f"ClientError fetching detailed health from {url}: {err}"
            ) from err

    async def async_get_models(self) -> list[str]:
        """Fetch available models from Hermes Agent."""
        url = f"{self._v1_url}/models"
        headers = self._get_headers()

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.get(url, headers=headers) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status != 200:
                        text = await resp.text()
                        raise CannotConnect(
                            f"HTTP {resp.status} while fetching models: {text}"
                        )

                    data = await resp.json()
                    models = [
                        m["id"]
                        for m in data.get("data", [])
                        if isinstance(m, dict) and "id" in m
                    ]
                    if not models:
                        models = [DEFAULT_CHAT_MODEL]
                    return models
        except TimeoutError as err:
            raise CannotConnect(f"Timeout connecting to Hermes Agent at {url}") from err
        except aiohttp.ClientError as err:
            raise CannotConnect(
                f"ClientError fetching models from {url}: {err}"
            ) from err

    async def async_chat_completion(
        self,
        messages: list[dict[str, Any]],
        model: str = DEFAULT_CHAT_MODEL,
        temperature: float = 0.7,
        top_p: float = 1.0,
        max_tokens: int = 2048,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute chat completion through Hermes Agent."""
        url = f"{self._v1_url}/chat/completions"
        headers = self._get_headers()

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.post(
                    url, headers=headers, json=payload
                ) as resp:
                    if resp.status == 401:
                        raise InvalidAuth(
                            "Invalid authentication token for chat completion"
                        )
                    if resp.status == 404:
                        raise ModelNotFoundError(
                            f"Model '{model}' not found in Hermes Agent"
                        )
                    if resp.status != 200:
                        err_text = await resp.text()
                        raise HermesAgentError(
                            f"HTTP {resp.status} in chat completion: {err_text}"
                        )
                    return await resp.json()
        except TimeoutError as err:
            raise CannotConnect(
                f"Timeout waiting for Hermes Agent completion at {url}"
            ) from err
        except aiohttp.ClientError as err:
            raise CannotConnect(
                f"ClientError during chat completion at {url}: {err}"
            ) from err

    async def async_get_sessions(self) -> list[dict[str, Any]]:
        """Fetch list of conversation sessions from Hermes Agent."""
        url = f"{self._root_url}/api/sessions"
        headers = self._get_headers()

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.get(url, headers=headers) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    if isinstance(data, list):
                        return data
                    if isinstance(data, dict):
                        return (
                            data.get("data")
                            if "data" in data
                            else data.get("sessions", [])
                        )
                    return []
        except Exception as err:
            LOGGER.debug("Could not fetch sessions: %s", err)
            return []

    async def async_create_session(self, title: str | None = None) -> dict[str, Any]:
        """Create a new conversation session in Hermes Agent."""
        url = f"{self._root_url}/api/sessions"
        headers = self._get_headers()
        payload = {"title": title} if title else {}

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.post(
                    url, headers=headers, json=payload
                ) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status not in (200, 201):
                        text = await resp.text()
                        raise HermesAgentError(
                            f"HTTP {resp.status} creating session: {text}"
                        )
                    return await resp.json()
        except TimeoutError as err:
            raise CannotConnect(f"Timeout creating session at {url}") from err
        except aiohttp.ClientError as err:
            raise CannotConnect(
                f"ClientError creating session at {url}: {err}"
            ) from err

    async def async_send_session_chat(
        self, session_id: str, message: str
    ) -> dict[str, Any]:
        """Send message into a specific session."""
        url = f"{self._root_url}/api/sessions/{session_id}/chat"
        headers = self._get_headers()
        payload = {"message": message}

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.post(
                    url, headers=headers, json=payload
                ) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status != 200:
                        text = await resp.text()
                        raise HermesAgentError(
                            f"HTTP {resp.status} sending session chat: {text}"
                        )
                    return await resp.json()
        except TimeoutError as err:
            raise CannotConnect(f"Timeout chatting with session {session_id}") from err
        except aiohttp.ClientError as err:
            raise CannotConnect(
                f"ClientError chatting with session {session_id}: {err}"
            ) from err

    async def async_get_jobs(self) -> list[dict[str, Any]]:
        """Fetch list of scheduled background jobs."""
        url = f"{self._root_url}/api/jobs"
        headers = self._get_headers()

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.get(url, headers=headers) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    if isinstance(data, list):
                        return data
                    if isinstance(data, dict):
                        return (
                            data.get("data") if "data" in data else data.get("jobs", [])
                        )
                    return []
        except Exception as err:
            LOGGER.debug("Could not fetch jobs: %s", err)
            return []

    async def async_pause_job(self, job_id: str) -> dict[str, Any]:
        """Pause or unpause a scheduled job."""
        url = f"{self._root_url}/api/jobs/{job_id}/pause"
        headers = self._get_headers()

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.post(url, headers=headers) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status != 200:
                        text = await resp.text()
                        raise HermesAgentError(
                            f"HTTP {resp.status} pausing job {job_id}: {text}"
                        )
                    return await resp.json()
        except TimeoutError as err:
            raise CannotConnect(f"Timeout pausing job {job_id}") from err
        except aiohttp.ClientError as err:
            raise CannotConnect(f"ClientError pausing job {job_id}: {err}") from err

    async def async_get_skills(self) -> list[dict[str, Any]]:
        """Fetch active agent skills."""
        url = f"{self._v1_url}/skills"
        headers = self._get_headers()

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.get(url, headers=headers) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    return data.get("data", []) if isinstance(data, dict) else []
        except Exception as err:
            LOGGER.debug("Could not fetch skills: %s", err)
            return []

    async def async_get_toolsets(self) -> list[dict[str, Any]]:
        """Fetch active agent toolsets."""
        url = f"{self._v1_url}/toolsets"
        headers = self._get_headers()

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.get(url, headers=headers) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    return data.get("data", []) if isinstance(data, dict) else []
        except Exception as err:
            LOGGER.debug("Could not fetch toolsets: %s", err)
            return []

    async def async_resume_job(self, job_id: str) -> dict[str, Any]:
        """Resume a paused scheduled job."""
        url = f"{self._root_url}/api/jobs/{job_id}/resume"
        headers = self._get_headers()

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.post(url, headers=headers) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status != 200:
                        text = await resp.text()
                        raise HermesAgentError(
                            f"HTTP {resp.status} resuming job {job_id}: {text}"
                        )
                    return await resp.json()
        except TimeoutError as err:
            raise CannotConnect(f"Timeout resuming job {job_id}") from err
        except aiohttp.ClientError as err:
            raise CannotConnect(f"ClientError resuming job {job_id}: {err}") from err

    async def async_run_job(self, job_id: str) -> dict[str, Any]:
        """Trigger an immediate run of a scheduled job."""
        url = f"{self._root_url}/api/jobs/{job_id}/run"
        headers = self._get_headers()

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.post(url, headers=headers) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status != 200:
                        text = await resp.text()
                        raise HermesAgentError(
                            f"HTTP {resp.status} triggering job {job_id}: {text}"
                        )
                    return await resp.json()
        except TimeoutError as err:
            raise CannotConnect(f"Timeout triggering job {job_id}") from err
        except aiohttp.ClientError as err:
            raise CannotConnect(f"ClientError triggering job {job_id}: {err}") from err

    async def async_start_run(
        self,
        input_text: str,
        model: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Start a durable background agent run."""
        url = f"{self._v1_url}/runs"
        headers = self._get_headers()
        payload: dict[str, Any] = {"input": input_text}
        if model:
            payload["model"] = model
        if session_id:
            payload["session_id"] = session_id

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.post(
                    url, headers=headers, json=payload
                ) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status not in (200, 201, 202):
                        text = await resp.text()
                        raise HermesAgentError(
                            f"HTTP {resp.status} starting run: {text}"
                        )
                    return await resp.json()
        except TimeoutError as err:
            raise CannotConnect(f"Timeout starting run at {url}") from err
        except aiohttp.ClientError as err:
            raise CannotConnect(f"ClientError starting run at {url}: {err}") from err

    async def async_get_run(self, run_id: str) -> dict[str, Any]:
        """Get status and output of a durable agent run."""
        url = f"{self._v1_url}/runs/{run_id}"
        headers = self._get_headers()

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.get(url, headers=headers) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status != 200:
                        text = await resp.text()
                        raise HermesAgentError(
                            f"HTTP {resp.status} fetching run {run_id}: {text}"
                        )
                    return await resp.json()
        except TimeoutError as err:
            raise CannotConnect(f"Timeout getting run {run_id}") from err
        except aiohttp.ClientError as err:
            raise CannotConnect(f"ClientError getting run {run_id}: {err}") from err

    async def async_stop_run(self, run_id: str) -> dict[str, Any]:
        """Stop/cancel an in-progress agent run."""
        url = f"{self._v1_url}/runs/{run_id}/stop"
        headers = self._get_headers()

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.post(url, headers=headers) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status != 200:
                        text = await resp.text()
                        raise HermesAgentError(
                            f"HTTP {resp.status} stopping run {run_id}: {text}"
                        )
                    return await resp.json()
        except TimeoutError as err:
            raise CannotConnect(f"Timeout stopping run {run_id}") from err
        except aiohttp.ClientError as err:
            raise CannotConnect(f"ClientError stopping run {run_id}: {err}") from err

    async def async_steer_run(self, run_id: str, message: str) -> dict[str, Any]:
        """Inject guidance or instruction into an active run."""
        url = f"{self._v1_url}/runs/{run_id}/steer"
        headers = self._get_headers()
        payload = {"message": message}

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.post(
                    url, headers=headers, json=payload
                ) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status != 200:
                        text = await resp.text()
                        raise HermesAgentError(
                            f"HTTP {resp.status} steering run {run_id}: {text}"
                        )
                    return await resp.json()
        except TimeoutError as err:
            raise CannotConnect(f"Timeout steering run {run_id}") from err
        except aiohttp.ClientError as err:
            raise CannotConnect(f"ClientError steering run {run_id}: {err}") from err

    async def async_approve_run(
        self, run_id: str, action: str = "approve", response: str | None = None
    ) -> dict[str, Any]:
        """Approve or reject a pending run tool execution."""
        url = f"{self._v1_url}/runs/{run_id}/approval"
        headers = self._get_headers()
        payload: dict[str, Any] = {"action": action}
        if response:
            payload["response"] = response

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.post(
                    url, headers=headers, json=payload
                ) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status != 200:
                        text = await resp.text()
                        raise HermesAgentError(
                            f"HTTP {resp.status} approving run {run_id}: {text}"
                        )
                    return await resp.json()
        except TimeoutError as err:
            raise CannotConnect(f"Timeout resolving approval for {run_id}") from err
        except aiohttp.ClientError as err:
            raise CannotConnect(f"ClientError resolving approval: {err}") from err

    async def async_fork_session(self, session_id: str) -> dict[str, Any]:
        """Fork an existing conversation session into a branch."""
        url = f"{self._root_url}/api/sessions/{session_id}/fork"
        headers = self._get_headers()

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.post(url, headers=headers) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status not in (200, 201):
                        text = await resp.text()
                        raise HermesAgentError(
                            f"HTTP {resp.status} forking session {session_id}: {text}"
                        )
                    return await resp.json()
        except TimeoutError as err:
            raise CannotConnect(f"Timeout forking session {session_id}") from err
        except aiohttp.ClientError as err:
            raise CannotConnect(
                f"ClientError forking session {session_id}: {err}"
            ) from err

    async def async_delete_session(self, session_id: str) -> dict[str, Any]:
        """Delete an old session from Hermes Agent."""
        url = f"{self._root_url}/api/sessions/{session_id}"
        headers = self._get_headers()

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.delete(url, headers=headers) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status not in (200, 204):
                        text = await resp.text()
                        raise HermesAgentError(
                            f"HTTP {resp.status} deleting session {session_id}: {text}"
                        )
                    return {"deleted": True, "session_id": session_id}
        except TimeoutError as err:
            raise CannotConnect(f"Timeout deleting session {session_id}") from err
        except aiohttp.ClientError as err:
            raise CannotConnect(
                f"ClientError deleting session {session_id}: {err}"
            ) from err

    async def async_get_session_messages(self, session_id: str) -> list[dict[str, Any]]:
        """Fetch transcript messages for a session."""
        url = f"{self._root_url}/api/sessions/{session_id}/messages"
        headers = self._get_headers()

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.get(url, headers=headers) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    return data.get("messages", []) if isinstance(data, dict) else []
        except Exception as err:
            LOGGER.debug("Could not fetch messages for session %s: %s", session_id, err)
            return []

    async def async_get_capabilities(self) -> dict[str, Any]:
        """Fetch Hermes Agent capabilities manifest."""
        url = f"{self._v1_url}/capabilities"
        headers = self._get_headers()

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.get(url, headers=headers) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status != 200:
                        return {}
                    return await resp.json()
        except Exception as err:
            LOGGER.debug("Could not fetch capabilities: %s", err)
            return {}

    async def async_get_model_options(self) -> dict[str, Any]:
        """Fetch Hermes Agent model providers and options."""
        url = f"{self._root_url}/api/model/options"
        headers = self._get_headers()

        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.get(url, headers=headers) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid authentication token")
                    if resp.status != 200:
                        return {}
                    return await resp.json()
        except Exception as err:
            LOGGER.debug("Could not fetch model options: %s", err)
            return {}

    async def async_send_notification(
        self,
        message: str,
        title: str | None = None,
        thread_id: str | None = None,
        chat_id: str | None = None,
        enrich: bool = True,
        inline_keyboard: list[Any] | str | None = None,
        disable_notification: bool = False,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send notification through Hermes Agent to Telegram."""
        url = f"{self._root_url}/api/ha/notify"
        headers = self._get_headers()
        payload: dict[str, Any] = {
            "message": message,
            "title": title or "",
            "thread_id": str(thread_id) if thread_id else "305748",
            "chat_id": str(chat_id) if chat_id else "649657901",
            "enrich": bool(enrich),
            "disable_notification": bool(disable_notification),
        }
        if inline_keyboard is not None:
            payload["inline_keyboard"] = inline_keyboard
        if data:
            payload["data"] = data

        try:
            async with asyncio.timeout(30.0):
                async with self._session.post(url, headers=headers, json=payload) as resp:
                    if resp.status == 401:
                        raise InvalidAuth("Invalid gateway API key (API_SERVER_KEY)")
                    if resp.status not in (200, 201):
                        text = await resp.text()
                        raise HermesAgentError(
                            f"HTTP {resp.status} sending notification: {text}"
                        )
                    return await resp.json()
        except TimeoutError as err:
            raise CannotConnect("Timeout sending notification to Hermes Agent") from err
        except aiohttp.ClientError as err:
            raise CannotConnect(
                f"ClientError sending notification to Hermes Agent: {err}"
            ) from err

