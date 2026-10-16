"""Service registration and handlers for Hermes Agent integration."""

from __future__ import annotations

import base64
import logging
import re
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components import camera
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError

from .client import HermesAgentClient
from .const import (
    CONF_AI_TASK_MAX_TOKENS,
    CONF_AI_TASK_MODEL,
    CONF_AI_TASK_PROMPT,
    CONF_AI_TASK_TEMPERATURE,
    CONF_CHAT_MODEL,
    DATA_CLIENT,
    DATA_COORDINATOR,
    DATA_SUGGESTIONS_SENSOR,
    DEFAULT_AI_TASK_MAX_TOKENS,
    DEFAULT_AI_TASK_MODEL,
    DEFAULT_AI_TASK_PROMPT,
    DEFAULT_AI_TASK_TEMPERATURE,
    DEFAULT_CHAT_MODEL,
    DOMAIN,
    SERVICE_ANALYZE_AUTOMATION,
    SERVICE_ANALYZE_CAMERA,
    SERVICE_APPROVE_RUN,
    SERVICE_CREATE_SESSION,
    SERVICE_DELETE_SESSION,
    SERVICE_DIAGNOSE_LOGS,
    SERVICE_EXECUTE_AI_TASK,
    SERVICE_FORK_SESSION,
    SERVICE_GET_RUN_STATUS,
    SERVICE_PAUSE_JOB,
    SERVICE_REFRESH_STATUS,
    SERVICE_RESUME_JOB,
    SERVICE_RUN_JOB,
    SERVICE_SEND_MESSAGE,
    SERVICE_START_RUN,
    SERVICE_STEER_RUN,
    SERVICE_STOP_RUN,
    SERVICE_SUGGEST_AUTOMATIONS,
)
from .coordinator import HermesAgentDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

EXECUTE_AI_TASK_SCHEMA = vol.Schema(
    {
        vol.Required("prompt"): cv.string,
        vol.Optional("model"): cv.string,
        vol.Optional("temperature"): vol.Coerce(float),
        vol.Optional("max_tokens"): vol.Coerce(int),
        vol.Optional("system_prompt"): cv.string,
    }
)

SEND_MESSAGE_SCHEMA = vol.Schema(
    {
        vol.Required("message"): cv.string,
        vol.Optional("session_id"): cv.string,
        vol.Optional("model"): cv.string,
    }
)

REFRESH_STATUS_SCHEMA = vol.Schema({})

PAUSE_JOB_SCHEMA = vol.Schema(
    {
        vol.Required("job_id"): cv.string,
    }
)

RESUME_JOB_SCHEMA = vol.Schema(
    {
        vol.Required("job_id"): cv.string,
    }
)

RUN_JOB_SCHEMA = vol.Schema(
    {
        vol.Required("job_id"): cv.string,
    }
)

START_RUN_SCHEMA = vol.Schema(
    {
        vol.Required("input"): cv.string,
        vol.Optional("model"): cv.string,
        vol.Optional("session_id"): cv.string,
    }
)

GET_RUN_STATUS_SCHEMA = vol.Schema(
    {
        vol.Required("run_id"): cv.string,
    }
)

STOP_RUN_SCHEMA = vol.Schema(
    {
        vol.Required("run_id"): cv.string,
    }
)

STEER_RUN_SCHEMA = vol.Schema(
    {
        vol.Required("run_id"): cv.string,
        vol.Required("message"): cv.string,
    }
)

APPROVE_RUN_SCHEMA = vol.Schema(
    {
        vol.Required("run_id"): cv.string,
        vol.Optional("action", default="approve"): vol.In(["approve", "reject"]),
        vol.Optional("response"): cv.string,
    }
)

FORK_SESSION_SCHEMA = vol.Schema(
    {
        vol.Required("session_id"): cv.string,
    }
)

DELETE_SESSION_SCHEMA = vol.Schema(
    {
        vol.Required("session_id"): cv.string,
    }
)

CREATE_SESSION_SCHEMA = vol.Schema(
    {
        vol.Optional("title"): cv.string,
        vol.Optional("prompt"): cv.string,
        vol.Optional("model"): cv.string,
    }
)

SUGGEST_AUTOMATIONS_SCHEMA = vol.Schema(
    {
        vol.Optional("domains"): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional("entity_limit", default=30): vol.Coerce(int),
        vol.Optional("custom_prompt"): cv.string,
        vol.Optional("model"): cv.string,
        vol.Optional("send_notification", default=True): cv.boolean,
    }
)

ANALYZE_AUTOMATION_SCHEMA = vol.Schema(
    {
        vol.Optional("automation_entity_id"): cv.entity_id,
        vol.Optional("yaml_content"): cv.string,
        vol.Optional("custom_prompt"): cv.string,
        vol.Optional("model"): cv.string,
    }
)

DIAGNOSE_LOGS_SCHEMA = vol.Schema(
    {
        vol.Optional("log_text"): cv.string,
        vol.Optional("hours_back", default=2): vol.Coerce(int),
        vol.Optional("custom_prompt"): cv.string,
        vol.Optional("model"): cv.string,
    }
)

ANALYZE_CAMERA_SCHEMA = vol.Schema(
    {
        vol.Required("camera_entity_id"): cv.entity_id,
        vol.Optional(
            "prompt",
            default="Describe what you see in this security camera snapshot in detail, highlighting any people, activity, or risks.",
        ): cv.string,
        vol.Optional("model"): cv.string,
    }
)


def _get_entry_context(
    hass: HomeAssistant,
) -> tuple[HermesAgentClient, HermesAgentDataUpdateCoordinator, Any, dict[str, Any]]:
    """Retrieve first configured client, coordinator, entry, and entry_data dict."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        raise HomeAssistantError("No Hermes Agent config entries configured")

    entry = entries[0]
    entry_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    client: HermesAgentClient | None = entry_data.get(DATA_CLIENT)
    coordinator: HermesAgentDataUpdateCoordinator | None = entry_data.get(
        DATA_COORDINATOR
    )

    if not client or not coordinator:
        raise HomeAssistantError("Hermes Agent client or coordinator not initialized")

    return client, coordinator, entry, entry_data


def async_setup_services(hass: HomeAssistant) -> None:
    """Register all Hermes Agent services."""

    async def _handle_execute_ai_task(call: ServiceCall) -> ServiceResponse:
        """Execute autonomous AI reasoning or task via Hermes Agent."""
        client, coordinator, entry, _ = _get_entry_context(hass)

        prompt = call.data["prompt"]
        model = call.data.get(
            "model",
            entry.options.get(CONF_AI_TASK_MODEL, DEFAULT_AI_TASK_MODEL),
        )
        temperature = call.data.get(
            "temperature",
            entry.options.get(CONF_AI_TASK_TEMPERATURE, DEFAULT_AI_TASK_TEMPERATURE),
        )
        max_tokens = call.data.get(
            "max_tokens",
            entry.options.get(CONF_AI_TASK_MAX_TOKENS, DEFAULT_AI_TASK_MAX_TOKENS),
        )
        system_prompt = call.data.get(
            "system_prompt",
            entry.options.get(CONF_AI_TASK_PROMPT, DEFAULT_AI_TASK_PROMPT),
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        try:
            result = await client.async_chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            choices = result.get("choices", [])
            response_text = ""
            if choices and "message" in choices[0]:
                response_text = choices[0]["message"].get("content", "")

            return {
                "response": response_text,
                "model": result.get("model", model),
                "usage": result.get("usage", {}),
            }
        except Exception as err:
            _LOGGER.error("Failed to execute AI task with Hermes Agent: %s", err)
            raise HomeAssistantError(f"Hermes Agent error: {err}") from err

    async def _handle_send_message(call: ServiceCall) -> ServiceResponse:
        """Send message into an active Hermes Agent session or chat."""
        client, coordinator, entry, _ = _get_entry_context(hass)

        message = call.data["message"]
        session_id = call.data.get("session_id")
        model = call.data.get(
            "model",
            entry.options.get(CONF_CHAT_MODEL, DEFAULT_CHAT_MODEL),
        )

        try:
            if session_id:
                res = await client.async_send_session_chat(session_id, message)
                return {"response": res, "session_id": session_id}

            messages = [{"role": "user", "content": message}]
            result = await client.async_chat_completion(
                messages=messages,
                model=model,
            )
            choices = result.get("choices", [])
            reply = ""
            if choices and "message" in choices[0]:
                reply = choices[0]["message"].get("content", "")
            return {"response": reply, "model": model}
        except Exception as err:
            _LOGGER.error("Failed to send message to Hermes Agent: %s", err)
            raise HomeAssistantError(f"Hermes Agent send_message error: {err}") from err

    async def _handle_create_session(call: ServiceCall) -> ServiceResponse:
        """Create a new autonomous conversation session."""
        client, coordinator, entry, _ = _get_entry_context(hass)
        title = call.data.get("title")
        prompt = call.data.get("prompt")
        model = call.data.get(
            "model", entry.options.get(CONF_CHAT_MODEL, DEFAULT_CHAT_MODEL)
        )

        try:
            session_data = await client.async_create_session(title=title)
            session_id = session_data.get("id") or session_data.get("session_id")
            first_reply = None
            if prompt and session_id:
                first_reply = await client.async_send_session_chat(session_id, prompt)
            return {
                "session": session_data,
                "session_id": session_id,
                "model": model,
                "initial_reply": first_reply,
            }
        except Exception as err:
            _LOGGER.error("Failed to create session with Hermes Agent: %s", err)
            raise HomeAssistantError(
                f"Hermes Agent create_session error: {err}"
            ) from err

    async def _handle_refresh_status(call: ServiceCall) -> ServiceResponse:
        """Force refresh of Hermes Agent status and telemetry."""
        client, coordinator, entry, _ = _get_entry_context(hass)
        await coordinator.async_refresh()
        return {"success": True, "status": coordinator.data}

    async def _handle_pause_job(call: ServiceCall) -> ServiceResponse:
        """Pause or unpause a background scheduled job."""
        client, coordinator, entry, _ = _get_entry_context(hass)
        job_id = call.data["job_id"]
        try:
            result = await client.async_pause_job(job_id)
            await coordinator.async_request_refresh()
            return {"success": True, "result": result, "job_id": job_id}
        except Exception as err:
            _LOGGER.error("Failed to pause job %s: %s", job_id, err)
            raise HomeAssistantError(f"Error pausing job {job_id}: {err}") from err

    async def _handle_resume_job(call: ServiceCall) -> ServiceResponse:
        """Resume a paused scheduled job."""
        client, coordinator, _, _ = _get_entry_context(hass)
        job_id = call.data["job_id"]
        try:
            result = await client.async_resume_job(job_id)
            await coordinator.async_request_refresh()
            return {"success": True, "result": result, "job_id": job_id}
        except Exception as err:
            _LOGGER.error("Failed to resume job %s: %s", job_id, err)
            raise HomeAssistantError(f"Error resuming job {job_id}: {err}") from err

    async def _handle_run_job(call: ServiceCall) -> ServiceResponse:
        """Trigger an immediate run of a scheduled job."""
        client, coordinator, _, _ = _get_entry_context(hass)
        job_id = call.data["job_id"]
        try:
            result = await client.async_run_job(job_id)
            await coordinator.async_request_refresh()
            return {"success": True, "result": result, "job_id": job_id}
        except Exception as err:
            _LOGGER.error("Failed to run job %s: %s", job_id, err)
            raise HomeAssistantError(f"Error running job {job_id}: {err}") from err

    async def _handle_start_run(call: ServiceCall) -> ServiceResponse:
        """Start a durable background agent run."""
        client, _, entry, _ = _get_entry_context(hass)
        input_text = call.data["input"]
        model = call.data.get(
            "model", entry.options.get(CONF_AI_TASK_MODEL, DEFAULT_AI_TASK_MODEL)
        )
        session_id = call.data.get("session_id")
        try:
            result = await client.async_start_run(
                input_text=input_text, model=model, session_id=session_id
            )
            return {
                "run": result,
                "run_id": result.get("id"),
                "status": result.get("status"),
            }
        except Exception as err:
            _LOGGER.error("Failed to start run: %s", err)
            raise HomeAssistantError(f"Error starting run: {err}") from err

    async def _handle_get_run_status(call: ServiceCall) -> ServiceResponse:
        """Get status of an asynchronous agent run."""
        client, _, _, _ = _get_entry_context(hass)
        run_id = call.data["run_id"]
        try:
            result = await client.async_get_run(run_id)
            return {
                "run": result,
                "run_id": run_id,
                "status": result.get("status"),
            }
        except Exception as err:
            _LOGGER.error("Failed to get status for run %s: %s", run_id, err)
            raise HomeAssistantError(f"Error fetching run {run_id}: {err}") from err

    async def _handle_stop_run(call: ServiceCall) -> ServiceResponse:
        """Stop/interrupt an ongoing agent run."""
        client, _, _, _ = _get_entry_context(hass)
        run_id = call.data["run_id"]
        try:
            result = await client.async_stop_run(run_id)
            return {"success": True, "result": result, "run_id": run_id}
        except Exception as err:
            _LOGGER.error("Failed to stop run %s: %s", run_id, err)
            raise HomeAssistantError(f"Error stopping run {run_id}: {err}") from err

    async def _handle_steer_run(call: ServiceCall) -> ServiceResponse:
        """Steer or inject instructions into an active run."""
        client, _, _, _ = _get_entry_context(hass)
        run_id = call.data["run_id"]
        message = call.data["message"]
        try:
            result = await client.async_steer_run(run_id, message)
            return {"success": True, "result": result, "run_id": run_id}
        except Exception as err:
            _LOGGER.error("Failed to steer run %s: %s", run_id, err)
            raise HomeAssistantError(f"Error steering run {run_id}: {err}") from err

    async def _handle_approve_run(call: ServiceCall) -> ServiceResponse:
        """Approve or reject tool execution for a run requiring action."""
        client, _, _, _ = _get_entry_context(hass)
        run_id = call.data["run_id"]
        action = call.data.get("action", "approve")
        response = call.data.get("response")
        try:
            result = await client.async_approve_run(run_id, action, response)
            return {"success": True, "result": result, "run_id": run_id}
        except Exception as err:
            _LOGGER.error("Failed to resolve approval for run %s: %s", run_id, err)
            raise HomeAssistantError(f"Error approving run {run_id}: {err}") from err

    async def _handle_fork_session(call: ServiceCall) -> ServiceResponse:
        """Fork an existing conversation session into a branch."""
        client, coordinator, _, _ = _get_entry_context(hass)
        session_id = call.data["session_id"]
        try:
            result = await client.async_fork_session(session_id)
            await coordinator.async_request_refresh()
            return {"success": True, "session": result}
        except Exception as err:
            _LOGGER.error("Failed to fork session %s: %s", session_id, err)
            raise HomeAssistantError(f"Error forking session {session_id}: {err}") from err

    async def _handle_delete_session(call: ServiceCall) -> ServiceResponse:
        """Delete a conversation session."""
        client, coordinator, _, _ = _get_entry_context(hass)
        session_id = call.data["session_id"]
        try:
            await client.async_delete_session(session_id)
            await coordinator.async_request_refresh()
            return {"success": True, "session_id": session_id}
        except Exception as err:
            _LOGGER.error("Failed to delete session %s: %s", session_id, err)
            raise HomeAssistantError(f"Error deleting session {session_id}: {err}") from err

    async def _handle_suggest_automations(call: ServiceCall) -> ServiceResponse:
        """Analyze actual Home Assistant entities and generate smart automation suggestions."""
        client, coordinator, entry, entry_data = _get_entry_context(hass)

        domains_filter = call.data.get("domains")
        entity_limit = call.data.get("entity_limit", 30)
        custom_prompt = call.data.get("custom_prompt")
        model = call.data.get(
            "model", entry.options.get(CONF_AI_TASK_MODEL, DEFAULT_AI_TASK_MODEL)
        )
        send_notification = call.data.get("send_notification", True)

        all_states = hass.states.async_all()
        selected: list[dict[str, Any]] = []

        for st in all_states:
            domain = st.domain
            if domains_filter and domain not in domains_filter:
                continue
            if domain in ["persistent_notification", "zone"]:
                continue
            selected.append(
                {
                    "entity_id": st.entity_id,
                    "state": st.state,
                    "name": st.attributes.get("friendly_name", st.entity_id),
                }
            )
            if len(selected) >= entity_limit:
                break

        entities_summary = "\n".join(
            f"- {e['entity_id']} ({e['name']}): {e['state']}" for e in selected
        )

        system_instruction = (
            "You are Hermes, an autonomous AI specialist for Home Assistant automation engineering. "
            "You analyze real smart home entities, detect automation opportunities, and provide ready-to-use YAML automations. "
            "Return a concise explanation followed by a markdown code block containing valid Home Assistant automation YAML."
        )

        user_msg = (
            f"Here is a sample of {len(selected)} active entities in my Home Assistant environment:\n\n"
            f"{entities_summary}\n\n"
            "Suggest 1-2 practical, high-value, creative automations using these entities. "
            "Ensure the YAML has valid triggers, conditions, and actions."
        )
        if custom_prompt:
            user_msg += f"\nCustom Request / Focus: {custom_prompt}\n"

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_msg},
        ]

        try:
            resp = await client.async_chat_completion(
                messages=messages,
                model=model,
                temperature=0.7,
                max_tokens=2048,
            )
            choices = resp.get("choices", [])
            content = ""
            if choices and "message" in choices[0]:
                content = str(choices[0]["message"].get("content", ""))

            yaml_match = re.search(r"```(?:yaml)?\s*([\s\S]*?)```", content)
            yaml_block = yaml_match.group(1).strip() if yaml_match else ""
            description = re.sub(r"```(?:yaml)?[\s\S]*?```", "", content).strip()

            sugg_sensor = entry_data.get(DATA_SUGGESTIONS_SENSOR)
            if sugg_sensor:
                sugg_sensor.set_suggestion(
                    description=description,
                    yaml_block=yaml_block,
                    model=model,
                    entities_processed_count=len(selected),
                )

            if send_notification:
                await hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "Hermes Agent Automation Suggestion",
                        "message": f"{description}\n\n```yaml\n{yaml_block}\n```",
                        "notification_id": "hermes_agent_automation_suggestion",
                    },
                )

            return {
                "description": description,
                "yaml_block": yaml_block,
                "model": model,
                "entities_analyzed": len(selected),
                "raw_response": content,
            }
        except Exception as err:
            _LOGGER.error("Failed to suggest automations: %s", err)
            raise HomeAssistantError(
                f"Hermes Agent suggest_automations error: {err}"
            ) from err

    async def _handle_analyze_automation(call: ServiceCall) -> ServiceResponse:
        """Analyze an automation for potential bugs, improvements, or syntax issues."""
        client, coordinator, entry, _ = _get_entry_context(hass)

        automation_id = call.data.get("automation_entity_id")
        yaml_content = call.data.get("yaml_content")
        custom_prompt = call.data.get("custom_prompt")
        model = call.data.get(
            "model", entry.options.get(CONF_AI_TASK_MODEL, DEFAULT_AI_TASK_MODEL)
        )

        code_to_analyze = ""
        if automation_id:
            state = hass.states.get(automation_id)
            if state:
                code_to_analyze = f"Entity: {automation_id}\nState: {state.state}\nAttributes: {state.attributes}"
            else:
                code_to_analyze = f"Entity {automation_id} (not currently loaded)"
        elif yaml_content:
            code_to_analyze = yaml_content
        else:
            raise HomeAssistantError(
                "Must specify either automation_entity_id or yaml_content"
            )

        user_prompt = (
            f"Analyze this Home Assistant automation for bugs, edge cases, performance improvements, or modern syntax:\n\n"
            f"```yaml\n{code_to_analyze}\n```\n"
        )
        if custom_prompt:
            user_prompt += f"\nSpecific question: {custom_prompt}\n"

        messages = [
            {
                "role": "system",
                "content": (
                    "You are Hermes, a Home Assistant core automation expert. "
                    "Analyze automations rigorously, identify potential race conditions or invalid syntax, "
                    "and provide clean, optimized replacement YAML."
                ),
            },
            {"role": "user", "content": user_prompt},
        ]

        try:
            resp = await client.async_chat_completion(
                messages=messages,
                model=model,
                temperature=0.2,
                max_tokens=3000,
            )
            choices = resp.get("choices", [])
            analysis = (
                choices[0].get("message", {}).get("content", "") if choices else ""
            )
            return {"analysis": analysis, "model": model}
        except Exception as err:
            _LOGGER.error("Failed to analyze automation: %s", err)
            raise HomeAssistantError(
                f"Hermes Agent analyze_automation error: {err}"
            ) from err

    async def _handle_diagnose_logs(call: ServiceCall) -> ServiceResponse:
        """Diagnose system error logs or provided error text."""
        client, coordinator, entry, _ = _get_entry_context(hass)

        log_text = call.data.get("log_text")
        custom_prompt = call.data.get("custom_prompt")
        model = call.data.get(
            "model", entry.options.get(CONF_AI_TASK_MODEL, DEFAULT_AI_TASK_MODEL)
        )

        logs_content = log_text or ""
        if not logs_content:
            system_log = hass.data.get("system_log")
            if system_log and hasattr(system_log, "records"):
                records = [
                    f"[{r.level}] {r.name}: {r.message}"
                    for r in list(system_log.records)[-20:]
                ]
                logs_content = "\n".join(records)

        if not logs_content:
            logs_content = (
                "No direct error log text provided or found in recent system log cache."
            )

        user_prompt = (
            f"Analyze the following Home Assistant error log excerpt:\n\n```text\n{logs_content}\n```\n\n"
            f"Please identify:\n"
            f"1. Root cause of each error\n"
            f"2. Severity (Benign vs Critical)\n"
            f"3. Concrete step-by-step instructions to fix each issue\n"
        )
        if custom_prompt:
            user_prompt += f"\nAdditional Context: {custom_prompt}\n"

        messages = [
            {
                "role": "system",
                "content": (
                    "You are Hermes, senior Python and Home Assistant core debugging expert. "
                    "Diagnose log traces clearly and provide actionable solutions."
                ),
            },
            {"role": "user", "content": user_prompt},
        ]

        try:
            resp = await client.async_chat_completion(
                messages=messages,
                model=model,
                temperature=0.2,
                max_tokens=3000,
            )
            choices = resp.get("choices", [])
            diagnosis = (
                choices[0].get("message", {}).get("content", "") if choices else ""
            )
            return {"diagnosis": diagnosis, "model": model}
        except Exception as err:
            _LOGGER.error("Failed to diagnose logs: %s", err)
            raise HomeAssistantError(
                f"Hermes Agent diagnose_logs error: {err}"
            ) from err

    async def _handle_analyze_camera(call: ServiceCall) -> ServiceResponse:
        """Capture camera frame and analyze image with multimodal Hermes vision."""
        client, coordinator, entry, _ = _get_entry_context(hass)

        camera_entity_id = call.data["camera_entity_id"]
        prompt = call.data.get(
            "prompt",
            "Describe what you see in this security camera snapshot in detail, highlighting any people, activity, or risks.",
        )
        model = call.data.get(
            "model", entry.options.get(CONF_AI_TASK_MODEL, DEFAULT_AI_TASK_MODEL)
        )

        try:
            image_frame = await camera.async_get_image(hass, camera_entity_id)
        except Exception as exc:
            raise HomeAssistantError(
                f"Failed to capture snapshot from {camera_entity_id}: {exc}"
            ) from exc

        b64_image = base64.b64encode(image_frame.content).decode("utf-8")
        data_url = f"data:{image_frame.content_type};base64,{b64_image}"

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ]

        try:
            resp = await client.async_chat_completion(
                messages=messages,
                model=model,
                temperature=0.3,
                max_tokens=2048,
            )
            choices = resp.get("choices", [])
            analysis = (
                choices[0].get("message", {}).get("content", "") if choices else ""
            )
            return {
                "camera_entity_id": camera_entity_id,
                "analysis": analysis,
                "model": model,
            }
        except Exception as err:
            _LOGGER.error("Failed to analyze camera snapshot: %s", err)
            raise HomeAssistantError(
                f"Hermes Agent analyze_camera error: {err}"
            ) from err

    # Register all services
    service_defs = [
        (SERVICE_EXECUTE_AI_TASK, _handle_execute_ai_task, EXECUTE_AI_TASK_SCHEMA),
        (SERVICE_SEND_MESSAGE, _handle_send_message, SEND_MESSAGE_SCHEMA),
        (SERVICE_REFRESH_STATUS, _handle_refresh_status, REFRESH_STATUS_SCHEMA),
        (SERVICE_PAUSE_JOB, _handle_pause_job, PAUSE_JOB_SCHEMA),
        (SERVICE_RESUME_JOB, _handle_resume_job, RESUME_JOB_SCHEMA),
        (SERVICE_RUN_JOB, _handle_run_job, RUN_JOB_SCHEMA),
        (SERVICE_START_RUN, _handle_start_run, START_RUN_SCHEMA),
        (SERVICE_GET_RUN_STATUS, _handle_get_run_status, GET_RUN_STATUS_SCHEMA),
        (SERVICE_STOP_RUN, _handle_stop_run, STOP_RUN_SCHEMA),
        (SERVICE_STEER_RUN, _handle_steer_run, STEER_RUN_SCHEMA),
        (SERVICE_APPROVE_RUN, _handle_approve_run, APPROVE_RUN_SCHEMA),
        (SERVICE_FORK_SESSION, _handle_fork_session, FORK_SESSION_SCHEMA),
        (SERVICE_DELETE_SESSION, _handle_delete_session, DELETE_SESSION_SCHEMA),
        (SERVICE_CREATE_SESSION, _handle_create_session, CREATE_SESSION_SCHEMA),
        (
            SERVICE_SUGGEST_AUTOMATIONS,
            _handle_suggest_automations,
            SUGGEST_AUTOMATIONS_SCHEMA,
        ),
        (
            SERVICE_ANALYZE_AUTOMATION,
            _handle_analyze_automation,
            ANALYZE_AUTOMATION_SCHEMA,
        ),
        (SERVICE_DIAGNOSE_LOGS, _handle_diagnose_logs, DIAGNOSE_LOGS_SCHEMA),
        (SERVICE_ANALYZE_CAMERA, _handle_analyze_camera, ANALYZE_CAMERA_SCHEMA),
    ]

    for name, handler, schema in service_defs:
        if not hass.services.has_service(DOMAIN, name):
            hass.services.async_register(
                DOMAIN,
                name,
                handler,
                schema=schema,
                supports_response=SupportsResponse.OPTIONAL,
            )


def async_unload_services(hass: HomeAssistant) -> None:
    """Unload all Hermes Agent services."""
    for service in [
        SERVICE_EXECUTE_AI_TASK,
        SERVICE_SEND_MESSAGE,
        SERVICE_REFRESH_STATUS,
        SERVICE_PAUSE_JOB,
        SERVICE_RESUME_JOB,
        SERVICE_RUN_JOB,
        SERVICE_START_RUN,
        SERVICE_GET_RUN_STATUS,
        SERVICE_STOP_RUN,
        SERVICE_STEER_RUN,
        SERVICE_APPROVE_RUN,
        SERVICE_FORK_SESSION,
        SERVICE_DELETE_SESSION,
        SERVICE_CREATE_SESSION,
        SERVICE_SUGGEST_AUTOMATIONS,
        SERVICE_ANALYZE_AUTOMATION,
        SERVICE_DIAGNOSE_LOGS,
        SERVICE_ANALYZE_CAMERA,
    ]:
        if hass.services.has_service(DOMAIN, service):
            hass.services.async_remove(DOMAIN, service)

