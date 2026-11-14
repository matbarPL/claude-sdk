# CCDV-F Exam Practice Workspace (`claude-sdk`)

## Environment & Runtime Rules
- **OS / Shell:** Windows 11 with PowerShell (`.\.venv\Scripts\python.exe`).
- **Auth:** Direct Anthropic API (`Anthropic()`), loaded via `load_dotenv(".env", override=True)`.
- **Security:** NEVER read, print, or commit `.env`. `.claude/settings.json` blocks `Read(./.env)` and scrubs subprocess env vars (`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1`).
- **Cost Guardrail:** Keep all practice scripts on `claude-haiku-4-5-20251001` ($1/$5 per MTok) with small `max_tokens` caps unless a lab specifically tests model-tier differences.

## Detailed Lab Guides (`labs/`)
Each lab has a dedicated specification file in `labs/` with objectives, implementation steps, verification commands, and CCDV-F exam traps:
1. `labs/lab01_messages_streaming.md` -> `lab1_messages.py` (Messages API, token counting, `stop_reason`, SSE streaming)
2. `labs/lab02_tools_loop.md` -> `lab2_tools.py` (Custom tools, `tool_choice`, parallel `tool_use`, `is_error=True` recovery)
3. `labs/lab03_structured_context.md` -> `lab3_structured_context.py` (Structured outputs, `strict: true`, XML boundaries, context pruning)
4. `labs/lab04_caching_batches.md` -> `lab4_caching_batches.py` (Prompt caching breakpoints/TTLs, Message Batches API)
5. `labs/lab05_workflows_agents.md` -> `lab5_workflows_agents.py` (Workflows vs. agents, subagent isolation, Agent SDK `query()`)
6. `labs/lab06_mcp_server.md` -> `lab6_mcp_server.py` & `lab6_mcp_client.py` (MCP Tools, Resources, Prompts, `stdio` vs. Streamable HTTP)
7. `labs/lab07_security_hooks.md` -> `.claude/hooks/pre_tool_guard.py` & `lab7_security_test.py` (`PreToolUse` exit `2` vs. JSON decisions, prompt injection defense)
8. `labs/lab08_claude_code_errors.md` -> `.claude/rules/python-labs.md` & `lab8_error_triage.py` (Claude Code scopes, headless `-p`, API error classification)
