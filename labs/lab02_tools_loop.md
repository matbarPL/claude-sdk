# Lab 02: Custom Tools, `tool_choice`, Parallel Tool Calls & `is_error` Recovery

**Target Script:** `lab2_tools.py`  
**Exam Domains:** Domain 8 (Tools & MCPs) & Domain 2 (Applications & Integration)  
**Model & Cost Guardrail:** `claude-haiku-4-5-20251001` (`max_tokens <= 256`, max 4 loop iterations)

## 1. Learning Objectives
1. Define clear, unambiguous JSON input schemas and descriptions for user-defined client tools.
2. Control tool invocation behavior using `tool_choice` (`{"type": "auto"}`, `{"type": "any"}`, and forced `{"type": "tool", "name": "..."}`).
3. Implement a `stop_reason == "tool_use"` client execution loop that handles multiple parallel `tool_use` blocks in a single assistant turn.
4. Signal recoverable tool execution failures to Claude using `is_error=True` inside a `tool_result` block so the model can self-correct.

## 2. Implementation Requirements
Create `lab2_tools.py` implementing a mock cloud-cost & service-lookup assistant:
1. **Define Two Client Tools (`TOOLS` list)**:
   - `get_service_status(service_name: str, region: str)`: returns status (`healthy`, `degraded`) and latency for a valid region (`us-east-1`, `eu-west-1`). If given an unknown region (e.g., `mars-1`), raise a `ValueError` listing valid regions.
   - `estimate_monthly_cost(input_tokens: int, output_tokens: int, tier: str)`: calculates cost for `haiku` (`$1/$5` per MTok) or `sonnet` (`$3/$15` per MTok).
2. **Build the `run_tool_loop(client, model, user_prompt, tool_choice=None)` Engine**:
   - Loop up to `MAX_TURNS = 4` (safety cap against runaway loops).
   - Call `client.messages.create(model=model, max_tokens=256, tools=TOOLS, tool_choice=tool_choice, messages=messages)`.
   - Always append `{"role": "assistant", "content": response.content}` unmodified (preserving any `thinking` or `text` blocks alongside `tool_use` blocks).
   - If `response.stop_reason != "tool_use"`, return the final text response.
   - When `response.stop_reason == "tool_use"`, iterate over **all** `block` items in `response.content` where `block.type == "tool_use"`:
     - Dispatch to the matching local Python function.
     - On success, build `{"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(result)}`.
     - On exception, catch the error and build `{"type": "tool_result", "tool_use_id": block.id, "is_error": True, "content": f"Tool execution error: {err}"}`.
   - Append a single `{"role": "user", "content": tool_results}` message containing all `tool_result` blocks for that turn.
3. **Run Three Test Scenarios**:
   - **Scenario A (Parallel Calls + `auto`):** Ask for status of `payments-api` in `us-east-1` AND monthly cost of `2_000_000` input / `500_000` output tokens on `haiku` in one prompt.
   - **Scenario B (`is_error=True` Self-Repair):** Ask for `auth-service` status in invalid region `eu-central-99`, instructing Claude to fall back to `eu-west-1` if a region error occurs.
   - **Scenario C (Forced `tool_choice`):** Pass `tool_choice={"type": "tool", "name": "estimate_monthly_cost"}` and verify Claude invokes that exact tool on turn 1.

## 3. Verification & Expected Output
Run:
```powershell
.\.venv\Scripts\python.exe lab2_tools.py
```
Confirm:
- Scenario A executes both `tool_use` blocks in one round-trip and returns both `tool_result` blocks in one `user` message.
- Scenario B sends `is_error=True` on turn 1, prompting Claude to retry with `eu-west-1` on turn 2.
- Scenario C immediately produces `stop_reason == "tool_use"` for `estimate_monthly_cost`.

## 4. CCDV-F Exam Checkpoints & Traps
- **Three Tool Categories:**
  1. *User-defined client tools:* You write the JSON schema; your code executes the tool.
  2. *Anthropic-schema client tools* (e.g., bash, text editor): Anthropic defines the schema; your environment still executes the action.
  3. *Server-executed tools* (e.g., web search): Anthropic hosts and executes the tool; you never construct a `tool_result` for server tools, and if a server loop pauses (`stop_reason == "pause_turn"`), re-send the paused response to let Claude continue.
- **Execution Error vs. Invalid Tool Call:** A missing/malformed `tool_use_id` or invalid API schema returns an HTTP `400` integration error. A runtime failure inside your tool (e.g., record not found, invalid region) is returned inside HTTP `200` as a `tool_result` with `is_error: true`.
- **Preserve Thinking Blocks Unmodified:** When extended thinking is active alongside tool calls, the entire `response.content` array (including `thinking` blocks and their cryptographic `signature`) must be passed back unmodified in the assistant turn; editing or dropping them triggers an HTTP `400` error.
