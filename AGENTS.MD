# AI Agent Reference for ha-hermes-agent

---

## Token Efficiency Rules (CRITICAL — Read First)

These rules apply to **every response** without exception:

1. **Output minimal prose.** Bullet points only. No introductory sentences, no filler, no "Great question!", no "As requested".
2. **No walkthrough unless explicitly asked.** Never create or update `walkthrough.md` unless the user writes "walkthrough" or "summary" in their request.
3. **No implementation plan unless complex.** Skip planning artifacts for simple tweaks, single-file edits, bug fixes, or minor features. Plan only for major architectural changes.
4. **Short change summaries only.** After making changes, output ≤5 bullet points describing *what* changed and *why* — never a line-by-line description.
5. **No repeating file content.** Never echo back code you just wrote or edited. Reference filenames with links instead.
6. **No tool-call narration.** Do not describe what tool you are about to call. Just call it.
7. **Targeted file reads only.** Use `grep_search` or `view_file` with `StartLine`/`EndLine` to read only the relevant section.
8. **Skip trivial confirmations.** Do not ask "Would you like me to proceed?" for obvious next steps. Just do them.
9. **No closing pleasantries.** End your response after the change summary.
10. **Suppress test output noise.** When running pytest, only report failures. Do not paste successful test output unless the user asks.

---

## Codebase Architecture

| Area | Path |
|---|---|
| Integration Entry | `custom_components/hermes_agent/__init__.py` |
| Coordinator | `custom_components/hermes_agent/coordinator.py` |
| Client | `custom_components/hermes_agent/client.py` |
| Config & Options Flow | `custom_components/hermes_agent/config_flow.py` |
| Conversation Agent | `custom_components/hermes_agent/conversation.py` |
| AI Task Entity | `custom_components/hermes_agent/ai_task.py` |
| Diagnostics & Sensors | `custom_components/hermes_agent/sensor.py` |
| Binary Sensors | `custom_components/hermes_agent/binary_sensor.py` |
| Buttons | `custom_components/hermes_agent/button.py` |
| Selects & Switches | `custom_components/hermes_agent/select.py`, `switch.py` |
| Services & Actions | `custom_components/hermes_agent/services.py`, `services.yaml` |
| Tests | `tests/` |
| Workflows | `.github/workflows/` |
| Scripts | `.github/scripts/` |

---

## CLI Commands

| Task | Command | Dir |
|---|---|---|
| Run tests | `pytest` | Root |
| Ruff linter | `ruff check . --fix` | Root |
| mypy linter | `mypy .` | Root |

---

## Coding Rules

- **Traceback Preservation**: NEVER use `raise e`. ALWAYS use `raise ... from e` or a naked `raise` to prevent stack trace destruction.
- **Silent Failure Prohibition**: `except: pass` is FORBIDDEN. All exceptions must be wrapped and propagated, or logged with context.
- **Async HA Patterns**: Ensure all Home Assistant async updates are correctly handled (e.g. using `async_write_ha_state`).
