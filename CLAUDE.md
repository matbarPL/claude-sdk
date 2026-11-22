# StrideCoach (`claude-sdk`)

A Python portfolio project for runners. It also serves as CCDV-F exam practice: each stage exercises a set of exam skills.

## Environment & Runtime Rules
- **OS / Shell:** Windows 11 with PowerShell. Run Python as `.\.venv\Scripts\python.exe`.
- **Auth:** Direct Anthropic API via `load_dotenv(".env", override=True)` before creating `Anthropic()`.
- **Security:** NEVER read, print, or commit `.env`. `.claude/settings.json` blocks `Read(./.env)` and scrubs subprocess env vars (`CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1`).
- **SDK caveat:** The installed `anthropic` Python SDK (2.8.0) does NOT accept `temperature` as a keyword argument in `client.messages.create()` or `client.messages.stream()`. Do not pass it; use the default sampling settings. Any sampling experiment needs a different approach, verified against the installed SDK first.

## Commands
- Run the dashboard: `.\.venv\Scripts\streamlit.exe run app.py`
- Demos (live API calls, small caps): `.\.venv\Scripts\python.exe demo_stage1.py`, `demo_stage2.py`, `demo_research_agent.py`
- Tests (offline, no API calls, ~40 s): `.\.venv\Scripts\python.exe -m pytest`. Single file: `-m pytest tests/test_parser.py`. Single test: `-m pytest tests/test_parser.py::test_note_cannot_close_its_own_wrapper`.
- Live smoke test (costs a few cents): `$env:RUN_LIVE_TESTS=1; .\.venv\Scripts\python.exe -m pytest -m live`. Live tests are skipped by default. Do not enable them in routine runs.
- Lint: `.\.venv\Scripts\python.exe -m ruff check .` (add `--fix` for import ordering). Config is in `pyproject.toml`.
- Test config lives in `pyproject.toml`. Tests are in `tests/`. `tests/conftest.py` sets a placeholder API key so imports succeed without `.env`.
- Dependencies are not declared in the repo. Imported packages: `anthropic`, `pydantic`, `python-dotenv`, `streamlit`, `claude-agent-sdk`. `pytest` and `ruff` were installed into `.venv` by hand.

## Cost & Model Pinning Rule
- Always pin `model="claude-haiku-4-5-20251001"`. Never use floating `-latest` aliases.
- Keep `max_tokens <= 300` on every call, including batch request params.
- Use small `max_tokens` values in verification scripts to keep cost below the lab budget.
- Use another model only when a stage explicitly tests model-tier differences, and note the reason in the code.

## Architecture
The `stridecoach/` package holds the API logic. `app.py` and the `demo_*.py` scripts sit at the repo root and import from it.

1. **Stage 1 — Core Messages API & Streaming:** Client setup, `messages.create()`, `messages.stream()` with `get_final_message()`, `count_tokens()`, and defensive `stop_reason` handling.
2. **Stage 2 — Messy Run Note Structured Parser & Prompt Caching:** Parse free-text run notes into structured data with strict schemas and XML boundaries. Add prompt caching breakpoints and measure their effect.
3. **Stage 3 — VDOT/ACWR Tools, Agent Loop & MCP Training Log Server:** Custom tools for VDOT and acute:chronic workload ratio calculations, a tool-use loop with `is_error=True` recovery, and an MCP server that exposes the training log. *Not started.*
4. **Stage 4 — Guardrails, Hooks, Evals & Streamlit UI:** Input and output guardrails, `PreToolUse` hooks, an eval harness, and a Streamlit front end. *Partly done:* the Streamlit UI exists in `app.py`; guardrails, hooks, and evals do not.

How the pieces connect:
- `app.py` is a Streamlit dashboard with three tabs. Its streaming tab calls `api.client.messages.stream()` directly through `stream_coach_to_ui`, not through `StrideCoachAPI.stream_coach_feedback`.
- `stridecoach/coach_api.py` holds the pinned model, the `max_tokens` cap, and `validate_response`. Responses are validated there before text is read.
- `stridecoach/parser.py` defines `StructuredWorkout` and parses notes with `messages.parse()`. The cached variant puts the handbook first as the only `cache_control` block. The handbook is built from `athlete_profile.md` and `research_papers/*.md`.
- `stridecoach/cost.py` computes per-call cost from usage and prunes conversation history.
- `stridecoach/research_agent.py` runs the Claude Agent SDK `query()` with `Glob`, `Grep`, `Read`, and `Write` tools, under turn and USD limits. It writes `athlete_profile.md`, which feeds the parser's cached handbook.
- Project skills in `.claude/skills/`: `create-training-plan` and `give-feedback`.

## Gotchas
- `research_agent.py` overwrites `athlete_profile.md` in the repo root. `demo_research_agent.py` and the dashboard's regenerate button replace it without asking.
- Importing `stridecoach.coach_api` loads `.env` as a side effect. `parser.py` relies on this.
- Every demo calls `sys.stdout.reconfigure(encoding="utf-8")`, because the Windows console defaults to cp1250 and crashes on model output.
- `messages.parse()` raises a pydantic `ValidationError` on truncated JSON, before any `stop_reason` check. `parser.py` converts it to a `ValueError`.
- Prompt caching needs the handbook above Haiku 4.5's 4,096-token minimum. It is currently about 8,075 tokens. Check with `count_tokens` after editing the handbook files.
- The "Prompt Injection Defense Test" preset in `app.py` relies only on the system prompt for defense.
- The cache TTL is 5 minutes. A second parse outside that window is a cache write again, not a read.

## Response Handling Rules
Path-scoped rules for `stridecoach/**/*.py` are in `.claude/rules/stridecoach-python.md`. In short: check `stop_reason` and empty `content` before reading text, scan blocks by `type == "text"`, and log `_request_id`.
