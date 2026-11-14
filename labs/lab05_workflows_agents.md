# Lab 05: Workflow Patterns, Subagent Context Isolation & Agent SDK `query()`

**Target Script:** `lab5_workflows_agents.py`  
**Exam Domains:** Domain 1 (Agents & Workflows — 14.7%)  
**Model & Cost Guardrail:** `claude-haiku-4-5-20251001` (`max_tokens <= 150`, strict turn/budget caps)

## 1. Learning Objectives
1. Distinguish a deterministic workflow (application code controls the sequence) from an autonomous agent (the model decides the next tool/step in a feedback loop).
2. Implement two core workflow patterns—**Prompt Chaining** (with a programmatic gate) and **Routing**—and contrast them with an **Orchestrator–Subagent** architecture.
3. Demonstrate subagent context isolation so verbose intermediate tool traces stay inside a subagent's window and only its final summary message returns to the orchestrator.
4. Configure Agent SDK `query()` loop guardrails (`maxTurns`, `maxBudgetUsd`, `allowedTools`, and `agents` subagent definitions) and inspect the `ResultMessage` subtype.

## 2. Implementation Requirements
Create `lab5_workflows_agents.py`:
1. **Deterministic Workflow: Router + Prompt Chain with Gate**:
   - **Step 1 (Classifier Router):** Classify an incoming developer request as `"billing"` or `"technical"` using a low-token Haiku call.
   - **Step 2 (Programmatic Gate + Specialist Prompt):** Route in Python `if/else` to a specialized prompt, then validate the output format in Python before passing it to Step 3 (final formatting).
2. **Orchestrator–Subagent Context Isolation Pattern**:
   - Simulate a `log_analyzer_subagent(raw_logs: str)` function that runs its own isolated `messages` list over a noisy 1,000-line log dump and returns only a 3-bullet root-cause summary to the parent `orchestrator_agent()`.
   - Verify the parent orchestrator's `messages` history never ingests the raw 1,000-line log payload.
3. **Agent SDK `query()` Guardrail Configuration (Reference / Dry-Run)**:
   - Write a helper showing how `claude-agent-sdk` (`query(prompt=..., options=ClaudeAgentOptions(...))`) configures `max_turns=3`, `max_budget_usd=0.05`, `allowed_tools=["Read", "Grep"]`, `system_prompt={"type": "preset", "preset": "claude_code"}`, and `agents={"auditor": AgentDefinition(...)}`, and inspects `message.subtype` (`success`, `error_max_turns`, `error_max_budget_usd`, `error_max_structured_output_retries`) on the final `ResultMessage`.

## 3. Verification & Expected Output
Run:
```powershell
.\.venv\Scripts\python.exe lab5_workflows_agents.py
```
Confirm:
- Deterministic router cleanly separates `"billing"` vs. `"technical"` inputs and enforces the programmatic gate.
- Parent orchestrator context remains small while receiving the subagent's synthesized findings.

## 4. CCDV-F Exam Checkpoints & Traps
- **Workflow vs. Agent Decision Rule:** Ask *"Who decides the next step?"* If your code/DAG controls the path, it is a **workflow**; if the model dynamically chooses tools and termination in a `Gather Context -> Take Action -> Verify Results` loop, it is an **agent**. Always choose the lowest rung of autonomy that solves the task.
- **Subagent Context Isolation:** A subagent runs in its own fresh conversation and does NOT automatically inherit the parent's conversation history—any file paths, decisions, or error messages it needs must be passed in its prompt, and only its final message returns to the parent as a tool result.
- **Agent SDK Default System Prompt Trap:** By default, the Agent SDK runs a minimal system prompt covering tool calling only; to match interactive Claude Code CLI behavior, explicitly pass `systemPrompt: { type: "preset", preset: "claude_code" }`.
