# Lab 08: Claude Code Scopes, Session Hygiene, Headless CI & API Error Triage

**Target Scripts:** `.claude/rules/python-labs.md` and `lab8_error_triage.py`  
**Exam Domains:** Domain 3 (Claude Code — 3.1%) & Domain 4 (Eval, Testing & Debugging — 2.6%)  
**Model & Cost Guardrail:** `claude-haiku-4-5-20251001` (simulated SDK error handling + optional 1-turn `claude -p`)

## 1. Learning Objectives
1. Organize project instructions across `CLAUDE.md` scopes (managed, user `~/.claude/CLAUDE.md`, project `./CLAUDE.md`, local `./CLAUDE.local.md`), path-scoped `.claude/rules/*.md`, Skills (`.claude/skills/<name>/SKILL.md`), and `settings.json` precedence.
2. Manage session context hygiene using `/compact` (with focus instructions), `/clear`, subagent delegation, and `PreCompact` hooks, and run non-interactive automation via `claude -p --output-format stream-json` or `--bare`.
3. Classify Claude API exceptions into **retryable** (`429`, `500`, `529`) vs. **non-retryable integration bugs** (`400`, `401`, `403`, `404`, `413`) and configure SDK `max_retries` + exponential backoff.

## 2. Implementation Requirements
1. **Create a Path-Scoped Rule File `.claude/rules/python-labs.md`**:
   - Add YAML frontmatter `paths: ["**/*.py"]` specifying Python lab conventions (`load_dotenv(".env", override=True)`, `claude-haiku-4-5-20251001`, typed `anthropic` exception handling).
2. **Create `lab8_error_triage.py` for SDK Exception Classification & Retry Policy**:
   - Instantiate `Anthropic(max_retries=2)` (explaining the SDK's default of 2 automatic retries with exponential backoff on transient errors).
   - Implement `classify_api_error(exc: Exception) -> dict` returning `{"action": "retry" | "fix_request" | "escalate", "layer": "integration" | "infrastructure"}` for:
     - `anthropic.RateLimitError` (`429`): distinguish standard RPM/TPM rate-limit vs. acceleration limit vs. spend-cap `429` (carries no `retry-after` header; requires billing cap increase, not blind retry).
     - `anthropic.BadRequestError` (`400`) & `anthropic.APIStatusError` (`413` `request_too_large` > 32 MB): classify as `"fix_request"` / `"integration"`.
     - `anthropic.AuthenticationError` (`401`) & `anthropic.PermissionDeniedError` (`403`): classify as `"escalate"` / `"integration"`.
     - `anthropic.InternalServerError` (`500` / `529` `overloaded_error`): classify as `"retry"` / `"infrastructure"`.
   - Trigger one controlled `BadRequestError` (e.g., `max_tokens=0`) against the live API to inspect `exc.status_code`, `exc.request_id`, and `exc.body`, and verify `classify_api_error()` routes it to `"fix_request"`.
3. **Headless CLI Verification Command (PowerShell)**:
   - Run a single bounded headless query with budget and turn caps:
     ```powershell
     claude -p "List the files in labs/ in one sentence." --max-turns 2 --max-budget-usd 0.05 --output-format json
     ```

## 3. Verification & Expected Output
Run:
```powershell
.\.venv\Scripts\python.exe lab8_error_triage.py
```
Confirm:
- Controlled `400` error prints `status_code: 400`, a `req_...` `request_id`, and classifies as `action: fix_request, layer: integration`.
- Headless `claude -p --output-format json` returns a structured JSON result object without hanging for interactive approval.

## 4. CCDV-F Exam Checkpoints & Traps
- **`settings.json` Precedence Order (Highest to Lowest):**
  1. Managed settings (`managed-settings.json` / MDM / server-managed — cannot be overridden)
  2. Command-line flags (`--model`, `--allowedTools`, `--permission-mode`, etc.)
  3. Local project settings (`.claude/settings.local.json`, gitignored)
  4. Shared project settings (`.claude/settings.json`, committed)
  5. User settings (`~/.claude/settings.json`)
- **What Survives `/compact`:** Project-root `CLAUDE.md`, unscoped rules, and auto memory (`MEMORY.md` first 200 lines) are re-injected from disk, and up to 5 most recently modified files are re-read. However, path-scoped rules (`paths:` frontmatter), nested `CLAUDE.md` files, and one-off chat instructions are summarized away unless re-triggered or placed in root `CLAUDE.md`. Use a `PreCompact` hook to archive the full unsummarized transcript before compaction runs.
- **`@path` Imports vs. Path-Scoped Rules:** Splitting `CLAUDE.md` with `@path` imports helps organization but does NOT save startup context because imported files still load at launch (unless wrapped in backticks as a code span, which skips the import). To load rules only on demand, use `.claude/rules/*.md` with a `paths:` glob or a Skill (`.claude/skills/<name>/SKILL.md`).
