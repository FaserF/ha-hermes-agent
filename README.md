<p align="center">
  <img src="https://raw.githubusercontent.com/FaserF/ha-hermes-agent/main/custom_components/hermes_agent/brand/logo.png" alt="Hermes Agent Logo" width="360">
</p>

# Hermes Agent for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/default)
[![CI](https://github.com/FaserF/ha-hermes-agent/actions/workflows/ci-orchestrator.yml/badge.svg)](https://github.com/FaserF/ha-hermes-agent/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Semantic Versioning: SemVer](https://img.shields.io/badge/versioning-SemVer-informational.svg)](https://semver.org)

Home Assistant custom integration for **Hermes Agent** (Nous Research). Seamlessly connects Home Assistant to your local or remote Hermes Agent instance, providing autonomous tool calling, multi-agent reasoning, voice conversation pipelines, scheduled jobs monitoring, multi-channel platform adapters (Telegram, Teams), and comprehensive system telemetry.

---

## 🧭 Quick Links

| | | | |
| :--- | :--- | :--- | :--- |
| [✨ Features](#-key-features--platforms) | [📦 Installation](#-installation) | [⚙️ Configuration](#️-configuration) | [🛡️ Security](SECURITY.md) |
| [🧱 Services](#-custom-services) | [📊 Diagnostics](#-diagnostics--troubleshooting) | [🧑‍💻 Development](AGENTS.MD) | [💖 Sponsors](.github/FUNDING.yml) |

---

## 🌟 Key Features & Platforms

### 1. 🗣️ Assist Voice & Conversation Agent (`conversation.hermes_agent_*`)
- **Native LLM Tool / Intent Calling**: Control smart home devices, query states, trigger automations, and run scripts through Home Assistant's built-in LLM Assist API.
- **Multi-Step Autonomous Reasoning**: Handles up to 10 sequential tool iterations to solve complex multi-device instructions.
- **Configurable LLM Parameters**: Customize system prompts with Jinja2 template support, temperature, top_p, and token limits.

### 2. 🧠 Autonomous AI Task Engine (`ai_task.hermes_agent_*`)
- **Native Home Assistant AI Tasks**: Complies with Home Assistant's AI Task specifications (`GENERATE_DATA`, `GENERATE_IMAGE`, `SUPPORT_ATTACHMENTS`).
- Power automation suggestions, blueprints, and analytical smart home summaries through autonomous reasoning.

### 3. 📊 Gateway & Agent Telemetry Sensors (`sensor.hermes_agent_*`)
- **Real-Time Performance**:
  - `sensor.hermes_agent_gateway_status`: Operational status of the agent gateway.
  - `sensor.hermes_agent_system_state`: Current agent state (idle, busy, running).
  - `sensor.hermes_agent_gateway_latency`: Roundtrip ping response latency in milliseconds.
- **Agent Capacity & Workload**:
  - `sensor.hermes_agent_available_models`: Count of registered models.
  - `sensor.hermes_agent_active_agents`: Number of autonomous subagents currently running.
  - `sensor.hermes_agent_active_sessions`: Active conversation sessions.
  - `sensor.hermes_agent_scheduled_jobs`: Registered background jobs.
  - `sensor.hermes_agent_installed_skills`: Skills and toolsets active on the gateway.
- **Usage & Resource Analytics**:
  - `sensor.hermes_agent_requests_today`: Total API requests handled today.
  - `sensor.hermes_agent_messages_today`: Total chat messages processed today.
  - `sensor.hermes_agent_tokens_today`: Total prompt and completion tokens consumed today.
  - `sensor.hermes_agent_host_disk_usage`: Storage capacity utilized on the host.
  - `sensor.hermes_agent_connected_platforms`: List of active platform connectors.
  - `sensor.hermes_agent_version`: Hermes Agent software version.

### 4. 🛡️ System & Adapter Binary Sensors (`binary_sensor.hermes_agent_*`)
- **Connectivity & Health**:
  - `binary_sensor.hermes_agent_connected`: Gateway reachable and answering requests.
  - `binary_sensor.hermes_agent_problem`: Flags backend health warnings or failures.
  - `binary_sensor.hermes_agent_busy`: Indicates ongoing autonomous processing.
- **Platform Integrations**:
  - `binary_sensor.hermes_agent_telegram_adapter`: Status of connected Telegram bot adapter.
  - `binary_sensor.hermes_agent_teams_adapter`: Status of connected Microsoft Teams bot adapter.

### 5. 🎛️ Dynamic Model Selectors (`select.hermes_agent_*`)
- **`select.hermes_agent_conversation_model`**: Dynamically switch the conversation model on the fly without reloading or modifying configuration.
- **`select.hermes_agent_ai_task_model`**: Dynamically switch the AI task reasoning model.

### 6. ⚡ Autonomous Switches & Action Buttons (`switch` & `button`)
- **`switch.hermes_agent_autonomous_execution`**: Toggle autonomous tool execution without user confirmation.
- **`switch.hermes_agent_telemetry_reporting`**: Enable or disable continuous telemetry polling.
- **`button.hermes_agent_refresh_gateway`**: Force an instant data refresh from the gateway.
- **`button.hermes_agent_check_health`**: Execute an explicit health ping and update diagnostic attributes.

### 7. 🤖 AI Automation Suggester & Diagnostics (`sensor` & services)
- **`sensor.hermes_agent_automation_suggestions`**: Real-time sensor exposing the suggested description, ready-to-use YAML block, and processed entity count for dashboard Markdown cards.
- **`hermes_agent.suggest_automations`**: Scans live entities across areas and domains, generates bespoke YAML automations, and posts persistent notifications in Home Assistant UI.
- **`hermes_agent.analyze_automation`**: Deeply analyzes existing automations or YAML snippets for syntax errors, race conditions, edge cases, and performance gains.
- **`hermes_agent.diagnose_logs`**: Analyzes system error logs or provided error traces to diagnose root causes and deliver step-by-step resolution plans.
- **`hermes_agent.analyze_camera`**: Captures security camera frames and uses multimodal Hermes vision to inspect activities, risks, package deliveries, or persons.

### 8. 🛠️ Session & Job Management Services
- **`hermes_agent.create_session`**: Create autonomous conversation sessions with optional starting instructions.
- **`hermes_agent.send_message`**: Send direct messages to specific sessions or chat directly.
- **`hermes_agent.execute_ai_task`**: Run arbitrary reasoning or autonomous tasks with custom system prompt overrides.
- **`hermes_agent.pause_job`**: Pause or resume scheduled background jobs.
- **`hermes_agent.refresh_status`**: Programmatically trigger a coordinator status refresh.

---

## 🚀 Installation

### Option 1: HACS (Recommended)

1. Open **HACS** in Home Assistant.
2. Navigate to **Integrations**, click the three dots in the upper right corner, and select **Custom repositories**.
3. Add `https://github.com/FaserF/ha-hermes-agent` with category **Integration**.
4. Search for **Hermes Agent**, click **Download**, and restart Home Assistant.

### Option 2: Manual Installation

1. Download the latest release zip from the [Releases page](https://github.com/FaserF/ha-hermes-agent/releases).
2. Unpack and copy the `custom_components/hermes_agent/` directory into your Home Assistant `<config_dir>/custom_components/hermes_agent/`.
3. Restart Home Assistant.

---

## ⚙️ Configuration

1. In Home Assistant, navigate to **Settings > Devices & Services > Add Integration**.
2. Search for **Hermes Agent**.
3. Fill in the connection settings:
   - **API URL**: e.g., `http://100.64.0.1:8642` or `http://localhost:8642`
   - **API Key**: Hermes Agent API key (optional if no authorization is configured).

### Options Flow Settings

Click **Configure** on the Hermes Agent integration card to fine-tune:
- **Conversation Model**: Select default model for voice assist.
- **Assist System Prompt**: Custom system prompt with Jinja2 templating support.
- **Temperature & Top P**: Generation randomness controls.
- **Max Tokens**: Token output ceiling.
- **LLM Assist API**: Tool calling provider selection (`Assist`).
- **AI Task Model & Prompt**: Model and prompt specifically for autonomous tasks.

---

## 🧪 Testing & Quality Assurance

This integration adheres to strict semantic versioning (`major.minor.patch`), robust linting with `ruff`, strict type checking with `mypy`, and 100% automated test coverage with `pytest` and `pytest-homeassistant-custom-component`.

Run the test suite locally:
```bash
pytest tests/ -v
```

---


## 🔌 Recommended Hardware & Ecosystem Links

| Device / Service | Integration Use Case | Link |
| :--- | :--- | :--- |
| **Home Assistant Green & Offizielle Smart-Home-Hardware** | Empfohlene Hardware-Basis für lokale Home Assistant Integrationen | [Offizielle Geräte-Seite →](https://fabiseitz.de/go/ha-hardware) |
| **Home Assistant Connect ZBT-1 (Zigbee / Thread)** | Lokales Zigbee2MQTT, ZHA & Matter-over-Thread Funknetz | [Offizielle Geräte-Seite →](https://fabiseitz.de/go/ha-zigbee) |

---

## 📄 License & Credits

Distributed under the **MIT License**. Created by [FaserF](https://github.com/FaserF).
Logo and branding assets property of [Nous Research](https://github.com/NousResearch/hermes-agent).
