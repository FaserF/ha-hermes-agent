"""Constants for the Hermes Agent integration."""

from __future__ import annotations

import logging
from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "hermes_agent"
LOGGER: Final = logging.getLogger(__package__)

DEFAULT_NAME: Final = "Hermes Agent"
DEFAULT_API_URL: Final = "http://127.0.0.1:8642"
DEFAULT_MANUFACTURER: Final = "Nous Research"
DEFAULT_MODEL: Final = "Hermes Agent"

DATA_COORDINATOR: Final = "coordinator"
DATA_CLIENT: Final = "client"

# Configuration keys
CONF_API_URL: Final = "api_url"
CONF_API_KEY: Final = "api_key"

# Conversation options
CONF_CHAT_MODEL: Final = "chat_model"
CONF_PROMPT: Final = "prompt"
CONF_TEMPERATURE: Final = "temperature"
CONF_TOP_P: Final = "top_p"
CONF_MAX_TOKENS: Final = "max_tokens"
CONF_LLM_HASS_API: Final = "llm_hass_api"

# AI Task options
CONF_AI_TASK_MODEL: Final = "ai_task_model"
CONF_AI_TASK_PROMPT: Final = "ai_task_prompt"
CONF_AI_TASK_TEMPERATURE: Final = "ai_task_temperature"
CONF_AI_TASK_MAX_TOKENS: Final = "ai_task_max_tokens"

# Switch options
CONF_AUTONOMOUS_EXECUTION: Final = "autonomous_execution"
CONF_TELEMETRY: Final = "telemetry"

# Default values
DEFAULT_CHAT_MODEL: Final = "hermes-agent"
DEFAULT_AI_TASK_MODEL: Final = "hermes-agent"
DEFAULT_TEMPERATURE: Final = 0.7
DEFAULT_TOP_P: Final = 1.0
DEFAULT_MAX_TOKENS: Final = 2048
DEFAULT_AI_TASK_TEMPERATURE: Final = 0.2
DEFAULT_AI_TASK_MAX_TOKENS: Final = 4096
DEFAULT_AUTONOMOUS_EXECUTION: Final = True
DEFAULT_TELEMETRY: Final = True

DEFAULT_PROMPT: Final = (
    "You are Hermes, an intelligent autonomous AI assistant for Home Assistant. "
    "Answer concisely and use the provided tools to interact with devices."
)
DEFAULT_AI_TASK_PROMPT: Final = (
    "You are Hermes, an autonomous AI specialist for complex reasoning, analysis, "
    "and task execution in Home Assistant."
)

# Supported platforms
PLATFORM_AI_TASK: Final = "ai_task"
PLATFORMS: Final[list[Platform | str]] = [
    Platform.CONVERSATION,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SELECT,
    Platform.SWITCH,
    PLATFORM_AI_TASK,
]

# Services
SERVICE_EXECUTE_AI_TASK: Final = "execute_ai_task"
SERVICE_SEND_MESSAGE: Final = "send_message"
SERVICE_REFRESH_STATUS: Final = "refresh_status"
SERVICE_PAUSE_JOB: Final = "pause_job"
SERVICE_RESUME_JOB: Final = "resume_job"
SERVICE_RUN_JOB: Final = "run_job"
SERVICE_START_RUN: Final = "start_run"
SERVICE_GET_RUN_STATUS: Final = "get_run_status"
SERVICE_STOP_RUN: Final = "stop_run"
SERVICE_STEER_RUN: Final = "steer_run"
SERVICE_APPROVE_RUN: Final = "approve_run"
SERVICE_FORK_SESSION: Final = "fork_session"
SERVICE_DELETE_SESSION: Final = "delete_session"
SERVICE_SUGGEST_AUTOMATIONS: Final = "suggest_automations"
SERVICE_ANALYZE_AUTOMATION: Final = "analyze_automation"
SERVICE_DIAGNOSE_LOGS: Final = "diagnose_logs"
SERVICE_ANALYZE_CAMERA: Final = "analyze_camera"
SERVICE_CREATE_SESSION: Final = "create_session"

DATA_SUGGESTIONS_SENSOR: Final = "suggestions_sensor"

# Max tool calling iterations in conversation agent
MAX_TOOL_ITERATIONS: Final = 10

# Attributes
ATTR_LATENCY_MS: Final = "latency_ms"
ATTR_ACTIVE_MODELS: Final = "active_models"
ATTR_TOTAL_MODELS: Final = "total_models"
ATTR_PROMPT_TOKENS: Final = "prompt_tokens"
ATTR_COMPLETION_TOKENS: Final = "completion_tokens"
ATTR_TOTAL_TOKENS: Final = "total_tokens"
ATTR_SESSION_ID: Final = "session_id"
ATTR_GATEWAY_STATE: Final = "gateway_state"
