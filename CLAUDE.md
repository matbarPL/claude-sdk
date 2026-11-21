# StrideCoach (`claude-sdk`)

A Python portfolio project for runners. It also serves as CCDV-F exam practice: each stage exercises a set of exam skills.

## Environment & Runtime Rules
- **OS / Shell:** Windows 11 with PowerShell. Run Python as `.\.venv\Scripts\python.exe`.
- **Auth:** Direct Anthropic API via `load_dotenv(".env", override=True)` before creating `Anthropic()`.
- **Security:** NEVER read, print, or commit `.env`. `.claude/settings.json` blocks `Read(./.env)` and scrubs subprocess env vars (`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1`).
- **SDK caveat:** The installed `anthropic` Python SDK (2.8.0) does NOT accept `temperature` as a keyword argument in `client.messages.create()` or `client.messages.stream()`. Do not pass it; use the default sampling settings. Any sampling experiment needs a different approach, verified against the installed SDK first.

## Cost & Model Pinning Rule
- Always pin `model="claude-haiku-4-5-20251001"`. Never use floating `-latest` aliases.
- Keep `max_tokens <= 300` on every call, including batch request params.
- Use small `max_tokens` values in verification scripts to keep cost below the lab budget.
- Use another model only when a stage explicitly tests model-tier differences, and note the reason in the code.

## Architecture Overview
All application code lives in the `stridecoach/` package. It is built in four stages:

1. **Stage 1 — Core Messages API & Streaming:** Client setup, `messages.create()`, `messages.stream()` with `get_final_message()`, `count_tokens()`, and defensive `stop_reason` handling.
2. **Stage 2 — Messy Run Note Structured Parser & Prompt Caching:** Parse free-text run notes into structured data with strict schemas and XML boundaries. Add prompt caching breakpoints and measure their effect.
3. **Stage 3 — VDOT/ACWR Tools, Agent Loop & MCP Training Log Server:** Custom tools for VDOT and acute:chronic workload ratio calculations, a tool-use loop with `is_error=True` recovery, and an MCP server that exposes the training log.
4. **Stage 4 — Guardrails, Hooks, Evals & Streamlit UI:** Input and output guardrails, `PreToolUse` hooks, an eval harness, and a Streamlit front end.

## Response Handling Rules
Path-scoped rules for `stridecoach/**/*.py` are in `.claude/rules/stridecoach-python.md`. In short: check `stop_reason` and empty `content` before reading text, scan blocks by `type == "text"`, and log `_request_id`.
